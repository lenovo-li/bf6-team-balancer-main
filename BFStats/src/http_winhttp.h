#pragma once

#include <string>

namespace bfstats {

// HTTP GET 的结果。
struct HttpResponse {
    bool        transport_ok = false;  // 网络层是否成功 (连接/收发完成)
    int         status_code = 0;       // HTTP 状态码 (transport_ok 为 true 时有效)
    std::string body;                  // 响应体 (UTF-8)
};

// 对 https URL 发起 GET 请求。
//   url     : 完整 URL, 必须是 https://host/path?query 形式
//   timeout_ms : 总体超时 (连接 + 接收), 0 用默认
// 失败时 transport_ok=false。
HttpResponse HttpGet(const std::wstring& url, int timeout_ms = 15000);

// 将 UTF-8 字符串做 percent-encode (用于拼接 query 参数值)。
// 保留 unreserved 字符 (A-Z a-z 0-9 - _ . ~), 其余转 %XX。
std::string UrlEncode(const std::string& utf8);

// UTF-8 <-> UTF-16 转换辅助。
std::wstring Utf8ToWide(const std::string& utf8);
std::string  WideToUtf8(const std::wstring& wide);

}  // namespace bfstats
