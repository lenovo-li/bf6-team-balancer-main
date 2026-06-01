#pragma once

// ============================================================================
// BFStats - Battlefield 6 player stats query C API
//
// 数据源: gametools.network (https://api.gametools.network/bf6/stats/)
// 内部实现使用 C++ / WinHTTP / nlohmann-json, 对外导出纯 C ABI 接口。
//
// 所有返回的字符串均为 UTF-8 编码的 JSON, 由本库分配, 调用方必须用
// bf6_free() 释放, 不能用调用方自己的 free/delete (跨 DLL 堆不同)。
// ============================================================================

#ifdef BFSTATS_EXPORTS
#define BFSTATS_API __declspec(dllexport)
#else
#define BFSTATS_API __declspec(dllimport)
#endif

#define BFSTATS_VERSION_MAJOR 0
#define BFSTATS_VERSION_MINOR 1
#define BFSTATS_VERSION_PATCH 0

#ifdef __cplusplus
extern "C" {
#endif

// 玩家所在平台。对应 gametools 的 platform 参数。
typedef enum {
    BF6_PLATFORM_PC = 0,   // pc
    BF6_PLATFORM_EA,       // ea  (EA App / Origin, 默认)
    BF6_PLATFORM_PSN,      // psn (PlayStation)
    BF6_PLATFORM_XBOX      // xbox
} BF6Platform;

// 返回码。0 表示成功, 负值表示各类错误。
typedef enum {
    BF6_OK = 0,
    BF6_ERR_BADARG = -1,    // 参数非法 (空指针 / 空名字 / count<=0)
    BF6_ERR_NETWORK = -2,   // 网络层失败 (连接/超时/TLS)
    BF6_ERR_HTTP = -3,      // HTTP 非 2xx
    BF6_ERR_NOTFOUND = -4,  // 玩家不存在 / 无数据
    BF6_ERR_PARSE = -5,     // 响应 JSON 解析失败
    BF6_ERR_INTERNAL = -6   // 其它内部错误 (如内存分配)
} BF6Result;

// ----------------------------------------------------------------------------
// 查询单个玩家战绩。
//   player_name : 游戏 ID (EA ID), UTF-8, 不可为空
//   platform    : 平台
//   out_json    : 成功时写入新分配的 UTF-8 JSON 字符串指针 (规整后的字段)。
//                 失败时写入 NULL。需用 bf6_free() 释放。
// 返回 BF6_OK 表示成功。
//
// 输出 JSON 结构 (规整后, key 已修正 gametools 的拼写问题):
// {
//   "userName": "...", "userId": "...", "avatar": "...", "platform": "pc",
//   "score": 0, "kills": 0, "deaths": 0, "assists": 0,
//   "killDeath": 0.0, "winPercent": 0.0, "accuracy": 0.0, "headshots": 0.0,
//   "killsPerMinute": 0.0, "killsPerMatch": 0.0, "timePlayed": "HH:MM:SS",
//   "matchesPlayed": 0, "wins": 0, "losses": 0, "revives": 0,
//   "weapons": [...], "vehicles": [...], "classes": [...], "maps": [...],
//   "gameModes": [...]
// }
// ----------------------------------------------------------------------------
BFSTATS_API BF6Result bf6_query_stats(const char* player_name,
                                      BF6Platform platform,
                                      char** out_json);

// ----------------------------------------------------------------------------
// 批量查询多个玩家 (内部并发对每个名字调用单查接口)。
//   names    : 玩家 ID 数组 (UTF-8), 长度为 count
//   count    : 数组长度, 必须 > 0
//   platform : 平台 (所有玩家用同一平台)
//   out_json : 成功时写入新分配的 UTF-8 JSON 数组字符串。需用 bf6_free() 释放。
//
// 输出为 JSON 数组, 每个元素:
//   { "name": "<输入名>", "ok": true, "data": { ...单查结构... } }
//   或失败: { "name": "<输入名>", "ok": false, "error": <BF6Result 数值> }
//
// 只要有任一玩家成功即返回 BF6_OK; 全部失败返回最后一个错误码。
// ----------------------------------------------------------------------------
BFSTATS_API BF6Result bf6_query_multiple(const char* const* names,
                                         int count,
                                         BF6Platform platform,
                                         char** out_json);

// 释放本库返回的任意字符串 (out_json)。传 NULL 安全。
BFSTATS_API void bf6_free(char* p);

// 返回库版本字符串, 形如 "0.1.0"。返回的是静态常量, 不需释放。
BFSTATS_API const char* bf6_version(void);

#ifdef __cplusplus
}
#endif
