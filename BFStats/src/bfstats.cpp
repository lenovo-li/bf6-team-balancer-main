#include "bfstats.h"
#include "http_winhttp.h"
#include "json_shape.h"
#include "debug_log.h"

#include <nlohmann/json.hpp>

#include <string>
#include <vector>
#include <thread>
#include <future>
#include <cstring>

using nlohmann::json;

namespace {

const char* PlatformSlug(BF6Platform p) {
    switch (p) {
        case BF6_PLATFORM_PC:   return "pc";
        case BF6_PLATFORM_EA:   return "ea";
        case BF6_PLATFORM_PSN:  return "psn";
        case BF6_PLATFORM_XBOX: return "xbox";
        default:                return "pc";
    }
}

// 分配一个 C 字符串副本 (调用方用 bf6_free 释放)。
char* DupCStr(const std::string& s) {
    char* p = static_cast<char*>(std::malloc(s.size() + 1));
    if (!p) return nullptr;
    std::memcpy(p, s.data(), s.size());
    p[s.size()] = '\0';
    return p;
}

// 内部: 查询单个玩家, 返回规整后的 JSON 字符串到 shaped。
BF6Result QueryOne(const std::string& name, BF6Platform platform, std::string& shaped) {
    if (name.empty()) return BF6_ERR_BADARG;

    std::string url = "https://api.gametools.network/bf6/stats/?name=";
    url += bfstats::UrlEncode(name);
    url += "&platform=";
    url += PlatformSlug(platform);
    url += "&format_values=false&lang=en-us";

    BF_LOG("Query", "QueryOne name=%s platform=%s", name.c_str(), PlatformSlug(platform));

    bfstats::HttpResponse r = bfstats::HttpGet(bfstats::Utf8ToWide(url));
    if (!r.transport_ok) {
        BF_LOG("Query", "network failure for %s", name.c_str());
        return BF6_ERR_NETWORK;
    }
    if (r.status_code == 404) {
        return BF6_ERR_NOTFOUND;
    }
    if (r.status_code < 200 || r.status_code >= 300) {
        BF_LOG("Query", "HTTP %d for %s", r.status_code, name.c_str());
        return BF6_ERR_HTTP;
    }
    if (bfstats::LooksLikeNotFound(r.body)) {
        return BF6_ERR_NOTFOUND;
    }
    if (!bfstats::ShapeStatsJson(r.body, shaped)) {
        return BF6_ERR_PARSE;
    }
    return BF6_OK;
}

}  // namespace

extern "C" {

BFSTATS_API BF6Result bf6_query_stats(const char* player_name,
                                      BF6Platform platform,
                                      char** out_json) {
    if (out_json) *out_json = nullptr;
    if (!player_name || !out_json || player_name[0] == '\0') {
        return BF6_ERR_BADARG;
    }

    std::string shaped;
    BF6Result rc = QueryOne(player_name, platform, shaped);
    if (rc != BF6_OK) return rc;

    char* dup = DupCStr(shaped);
    if (!dup) return BF6_ERR_INTERNAL;
    *out_json = dup;
    return BF6_OK;
}

BFSTATS_API BF6Result bf6_query_multiple(const char* const* names,
                                         int count,
                                         BF6Platform platform,
                                         char** out_json) {
    if (out_json) *out_json = nullptr;
    if (!names || count <= 0 || !out_json) return BF6_ERR_BADARG;

    // 并发查询每个名字。限制并发量, 对第三方服务友好。
    struct Item {
        std::string name;
        BF6Result   rc = BF6_ERR_INTERNAL;
        std::string shaped;
    };
    std::vector<Item> items(count);
    for (int i = 0; i < count; ++i) {
        items[i].name = (names[i] ? names[i] : "");
    }

    const int kMaxConcurrency = 6;
    int next = 0;
    while (next < count) {
        int batch = (count - next < kMaxConcurrency) ? (count - next) : kMaxConcurrency;
        std::vector<std::future<void>> futs;
        futs.reserve(batch);
        for (int k = 0; k < batch; ++k) {
            Item* it = &items[next + k];
            futs.push_back(std::async(std::launch::async, [it, platform]() {
                if (it->name.empty()) { it->rc = BF6_ERR_BADARG; return; }
                it->rc = QueryOne(it->name, platform, it->shaped);
            }));
        }
        for (auto& f : futs) f.get();
        next += batch;
    }

    // 组装结果数组。
    json arr = json::array();
    int success = 0;
    BF6Result last_err = BF6_ERR_NOTFOUND;
    for (auto& it : items) {
        json e = json::object();
        e["name"] = it.name;
        if (it.rc == BF6_OK) {
            e["ok"] = true;
            e["data"] = json::parse(it.shaped, nullptr, false);
            ++success;
        } else {
            e["ok"] = false;
            e["error"] = static_cast<int>(it.rc);
            last_err = it.rc;
        }
        arr.push_back(std::move(e));
    }

    std::string result = arr.dump();
    char* dup = DupCStr(result);
    if (!dup) return BF6_ERR_INTERNAL;
    *out_json = dup;

    BF_LOG("Query", "multiple done: %d/%d ok", success, count);
    return (success > 0) ? BF6_OK : last_err;
}

BFSTATS_API void bf6_free(char* p) {
    if (p) std::free(p);
}

BFSTATS_API const char* bf6_version(void) {
    return "0.1.0";
}

}  // extern "C"
