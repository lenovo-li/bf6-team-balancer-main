#include "json_shape.h"
#include "debug_log.h"

#include <nlohmann/json.hpp>

using nlohmann::json;

namespace bfstats {

namespace {

// 安全取值: key 不存在或类型不符时返回默认值。
template <typename T>
T GetOr(const json& j, const char* key, T def) {
    auto it = j.find(key);
    if (it == j.end() || it->is_null()) return def;
    try {
        return it->get<T>();
    } catch (...) {
        return def;
    }
}

std::string GetStr(const json& j, const char* key) {
    auto it = j.find(key);
    if (it == j.end() || it->is_null()) return std::string();
    if (it->is_string()) return it->get<std::string>();
    return it->dump();  // 数字等转字符串
}

// 拷贝一个数组对象的指定数值/字符串 key 到目标对象 (按需取, 缺失给 0/"")。
void CopyNum(json& dst, const json& src, const char* key) {
    auto it = src.find(key);
    if (it != src.end() && it->is_number()) dst[key] = *it;
    else dst[key] = 0;
}
void CopyStr(json& dst, const json& src, const char* key) {
    dst[key] = GetStr(src, key);
}

json ShapeWeapon(const json& w) {
    json o = json::object();
    CopyStr(o, w, "name");
    CopyStr(o, w, "type");
    CopyStr(o, w, "image");
    CopyNum(o, w, "kills");
    CopyNum(o, w, "headshotKills");
    CopyNum(o, w, "accuracy");
    CopyNum(o, w, "headshots");
    CopyNum(o, w, "killsPerMinute");
    CopyNum(o, w, "damagePerMinute");
    CopyNum(o, w, "shotsFired");
    CopyNum(o, w, "shotsHit");
    CopyNum(o, w, "timeEquipped");
    return o;
}

json ShapeVehicle(const json& v) {
    json o = json::object();
    CopyStr(o, v, "name");
    CopyStr(o, v, "type");
    CopyStr(o, v, "image");
    CopyNum(o, v, "kills");
    CopyNum(o, v, "killsPerMinute");
    CopyNum(o, v, "damage");
    CopyNum(o, v, "destroyed");
    CopyNum(o, v, "roadKills");
    CopyNum(o, v, "distanceTraveled");
    CopyNum(o, v, "timeIn");
    return o;
}

json ShapeClass(const json& c) {
    json o = json::object();
    CopyStr(o, c, "className");
    CopyNum(o, c, "kills");
    CopyNum(o, c, "deaths");
    CopyNum(o, c, "killDeath");
    CopyNum(o, c, "kpm");
    CopyNum(o, c, "score");
    CopyNum(o, c, "assists");
    CopyNum(o, c, "revives");
    CopyNum(o, c, "secondsPlayed");
    return o;
}

json ShapeMap(const json& m) {
    json o = json::object();
    CopyStr(o, m, "mapName");
    CopyNum(o, m, "wins");
    CopyNum(o, m, "losses");
    CopyNum(o, m, "matches");
    CopyNum(o, m, "winPercent");
    CopyNum(o, m, "secondsPlayed");
    return o;
}

json ShapeGameMode(const json& g) {
    json o = json::object();
    CopyStr(o, g, "gamemodeName");
    CopyNum(o, g, "kills");
    CopyNum(o, g, "deaths");
    CopyNum(o, g, "wins");
    CopyNum(o, g, "losses");
    CopyNum(o, g, "killDeath");
    CopyNum(o, g, "winPercent");
    CopyNum(o, g, "matches");
    CopyNum(o, g, "kpm");
    CopyNum(o, g, "secondsPlayed");
    return o;
}

void ShapeArray(json& dst, const json& root, const char* key,
                json (*fn)(const json&)) {
    json arr = json::array();
    auto it = root.find(key);
    if (it != root.end() && it->is_array()) {
        for (const auto& e : *it) {
            if (e.is_object()) arr.push_back(fn(e));
        }
    }
    dst[key] = std::move(arr);
}

}  // namespace

bool LooksLikeNotFound(const std::string& raw_json) {
    json j = json::parse(raw_json, nullptr, false);
    if (j.is_discarded() || !j.is_object()) return true;
    // gametools: 无数据时通常 hasResults=false, 或缺少 userName。
    auto hr = j.find("hasResults");
    if (hr != j.end() && hr->is_boolean() && hr->get<bool>() == false) return true;
    if (!j.contains("userName") && !j.contains("kills")) return true;
    // 也可能返回 {"errors":[...]}
    if (j.contains("errors")) return true;
    return false;
}

bool ShapeStatsJson(const std::string& raw_json, std::string& out) {
    json j = json::parse(raw_json, nullptr, false);
    if (j.is_discarded() || !j.is_object()) {
        BF_LOG("Parse", "ShapeStatsJson: invalid JSON");
        return false;
    }

    json o = json::object();

    // 身份
    o["userName"]   = GetStr(j, "userName");
    o["userId"]     = GetStr(j, "userId");
    o["id"]         = GetStr(j, "id");
    o["avatar"]     = GetStr(j, "avatar");
    o["platform"]   = GetStr(j, "platform");

    // 核心战绩 (注意修正拼写: humanPrecentage -> humanPercentage, loses -> losses)
    o["score"]            = GetOr<long long>(j, "score", 0);
    o["kills"]            = GetOr<long long>(j, "kills", 0);
    o["deaths"]           = GetOr<long long>(j, "deaths", 0);
    o["assists"]          = GetOr<long long>(j, "assists", 0);
    o["killDeath"]        = GetOr<double>(j, "killDeath", 0.0);
    o["infantryKillDeath"]= GetOr<double>(j, "infantryKillDeath", 0.0);
    o["winPercent"]       = GetOr<double>(j, "winPercent", 0.0);
    o["accuracy"]         = GetOr<double>(j, "accuracy", 0.0);
    o["headshotPercent"]  = GetOr<double>(j, "headshots", 0.0);   // gametools: headshots(float)=爆头率
    o["headshotKills"]    = GetOr<long long>(j, "headShots", 0);  // gametools: headShots(int)=爆头数
    o["killsPerMinute"]   = GetOr<double>(j, "killsPerMinute", 0.0);
    o["killsPerMatch"]    = GetOr<double>(j, "killsPerMatch", 0.0);
    o["damagePerMinute"]  = GetOr<double>(j, "damagePerMinute", 0.0);
    o["timePlayed"]       = GetStr(j, "timePlayed");
    o["secondsPlayed"]    = GetOr<long long>(j, "secondsPlayed", 0);
    o["matchesPlayed"]    = GetOr<long long>(j, "matchesPlayed", 0);
    o["wins"]             = GetOr<long long>(j, "wins", 0);
    o["losses"]           = GetOr<long long>(j, "loses", 0);  // 修正拼写
    o["revives"]          = GetOr<long long>(j, "revives", 0);
    o["heals"]            = GetOr<long long>(j, "heals", 0);
    o["resupplies"]       = GetOr<long long>(j, "resupplies", 0);
    o["repairs"]          = GetOr<long long>(j, "repairs", 0);
    o["humanPercentage"]  = GetOr<double>(j, "humanPrecentage", 0.0);  // 修正拼写
    o["shotsFired"]       = GetOr<long long>(j, "shotsFired", 0);
    o["shotsHit"]         = GetOr<long long>(j, "shotsHit", 0);

    // 明细数组
    ShapeArray(o, j, "weapons",   &ShapeWeapon);
    ShapeArray(o, j, "vehicles",  &ShapeVehicle);
    ShapeArray(o, j, "classes",   &ShapeClass);
    ShapeArray(o, j, "maps",      &ShapeMap);
    ShapeArray(o, j, "gameModes", &ShapeGameMode);

    out = o.dump();
    return true;
}

}  // namespace bfstats
