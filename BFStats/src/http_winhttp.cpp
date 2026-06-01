#include "http_winhttp.h"
#include "debug_log.h"

#include <windows.h>
#include <winhttp.h>
#include <vector>

namespace bfstats {

std::wstring Utf8ToWide(const std::string& utf8) {
    if (utf8.empty()) return std::wstring();
    int n = MultiByteToWideChar(CP_UTF8, 0, utf8.data(), (int)utf8.size(), nullptr, 0);
    if (n <= 0) return std::wstring();
    std::wstring w(n, L'\0');
    MultiByteToWideChar(CP_UTF8, 0, utf8.data(), (int)utf8.size(), w.data(), n);
    return w;
}

std::string WideToUtf8(const std::wstring& wide) {
    if (wide.empty()) return std::string();
    int n = WideCharToMultiByte(CP_UTF8, 0, wide.data(), (int)wide.size(), nullptr, 0, nullptr, nullptr);
    if (n <= 0) return std::string();
    std::string s(n, '\0');
    WideCharToMultiByte(CP_UTF8, 0, wide.data(), (int)wide.size(), s.data(), n, nullptr, nullptr);
    return s;
}

std::string UrlEncode(const std::string& utf8) {
    static const char hex[] = "0123456789ABCDEF";
    std::string out;
    out.reserve(utf8.size() * 3);
    for (unsigned char c : utf8) {
        if ((c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') ||
            (c >= '0' && c <= '9') ||
            c == '-' || c == '_' || c == '.' || c == '~') {
            out.push_back((char)c);
        } else {
            out.push_back('%');
            out.push_back(hex[(c >> 4) & 0xF]);
            out.push_back(hex[c & 0xF]);
        }
    }
    return out;
}

// RAII 包装 WinHTTP 句柄。
namespace {
struct WinHttpHandle {
    HINTERNET h = nullptr;
    WinHttpHandle() = default;
    explicit WinHttpHandle(HINTERNET handle) : h(handle) {}
    ~WinHttpHandle() { if (h) WinHttpCloseHandle(h); }
    WinHttpHandle(const WinHttpHandle&) = delete;
    WinHttpHandle& operator=(const WinHttpHandle&) = delete;
    explicit operator bool() const { return h != nullptr; }
};
}  // namespace

HttpResponse HttpGet(const std::wstring& url, int timeout_ms) {
    HttpResponse resp;

    // 拆解 URL。
    URL_COMPONENTS uc{};
    uc.dwStructSize = sizeof(uc);
    wchar_t host[256] = {0};
    wchar_t path[2048] = {0};
    uc.lpszHostName = host;     uc.dwHostNameLength = ARRAYSIZE(host);
    uc.lpszUrlPath = path;      uc.dwUrlPathLength = ARRAYSIZE(path);
    uc.dwSchemeLength = (DWORD)-1;
    uc.dwExtraInfoLength = (DWORD)-1;

    if (!WinHttpCrackUrl(url.c_str(), (DWORD)url.size(), 0, &uc)) {
        BF_LOG("Http", "WinHttpCrackUrl failed, err=%lu", GetLastError());
        return resp;
    }

    // path + extra(query) 拼接成完整对象路径。
    std::wstring object = path;
    if (uc.lpszExtraInfo && uc.dwExtraInfoLength > 0) {
        object.append(uc.lpszExtraInfo, uc.dwExtraInfoLength);
    }

    WinHttpHandle session(WinHttpOpen(L"BFStats/0.1 (WinHTTP)",
                                      WINHTTP_ACCESS_TYPE_AUTOMATIC_PROXY,
                                      WINHTTP_NO_PROXY_NAME,
                                      WINHTTP_NO_PROXY_BYPASS, 0));
    if (!session) {
        BF_LOG("Http", "WinHttpOpen failed, err=%lu", GetLastError());
        return resp;
    }

    if (timeout_ms > 0) {
        WinHttpSetTimeouts(session.h, timeout_ms, timeout_ms, timeout_ms, timeout_ms);
    }

    WinHttpHandle connect(WinHttpConnect(session.h, host, uc.nPort, 0));
    if (!connect) {
        BF_LOG("Http", "WinHttpConnect failed host=%ls port=%u err=%lu",
               host, uc.nPort, GetLastError());
        return resp;
    }

    DWORD flags = (uc.nScheme == INTERNET_SCHEME_HTTPS) ? WINHTTP_FLAG_SECURE : 0;
    WinHttpHandle request(WinHttpOpenRequest(connect.h, L"GET", object.c_str(),
                                             nullptr, WINHTTP_NO_REFERER,
                                             WINHTTP_DEFAULT_ACCEPT_TYPES, flags));
    if (!request) {
        BF_LOG("Http", "WinHttpOpenRequest failed, err=%lu", GetLastError());
        return resp;
    }

    const wchar_t* headers = L"Accept: application/json\r\n";
    if (!WinHttpSendRequest(request.h, headers, (DWORD)-1L,
                            WINHTTP_NO_REQUEST_DATA, 0, 0, 0)) {
        BF_LOG("Http", "WinHttpSendRequest failed, err=%lu", GetLastError());
        return resp;
    }

    if (!WinHttpReceiveResponse(request.h, nullptr)) {
        BF_LOG("Http", "WinHttpReceiveResponse failed, err=%lu", GetLastError());
        return resp;
    }

    // 取状态码。
    DWORD status = 0, sz = sizeof(status);
    WinHttpQueryHeaders(request.h,
                        WINHTTP_QUERY_STATUS_CODE | WINHTTP_QUERY_FLAG_NUMBER,
                        WINHTTP_HEADER_NAME_BY_INDEX, &status, &sz,
                        WINHTTP_NO_HEADER_INDEX);
    resp.status_code = (int)status;
    resp.transport_ok = true;

    // 读取响应体。
    std::string body;
    for (;;) {
        DWORD avail = 0;
        if (!WinHttpQueryDataAvailable(request.h, &avail)) {
            BF_LOG("Http", "WinHttpQueryDataAvailable failed, err=%lu", GetLastError());
            break;
        }
        if (avail == 0) break;
        std::vector<char> buf(avail);
        DWORD read = 0;
        if (!WinHttpReadData(request.h, buf.data(), avail, &read)) {
            BF_LOG("Http", "WinHttpReadData failed, err=%lu", GetLastError());
            break;
        }
        if (read == 0) break;
        body.append(buf.data(), read);
    }
    resp.body = std::move(body);

    BF_LOG("Http", "GET %ls -> status=%d, %zu bytes",
           host, resp.status_code, resp.body.size());
    return resp;
}

}  // namespace bfstats
