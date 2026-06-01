#pragma once

#include <string>

namespace bfstats {

// 将 gametools /bf6/stats/ 的原始 JSON 文本规整为干净结构。
//   raw_json : gametools 返回的原始 JSON 文本 (format_values=false)
//   out      : 规整后的 JSON 文本 (UTF-8)
// 返回 true 表示解析并规整成功; false 表示 JSON 无效或不是预期结构。
//
// 规整内容:
//  - 修正 gametools 的拼写问题 key (humanPrecentage/loses 等) 为规范名
//  - 顶层只保留查询关心的标量字段
//  - weapons/vehicles/classes/maps/gameModes 数组只保留关键列
bool ShapeStatsJson(const std::string& raw_json, std::string& out);

// 判断规整后的数据是否表示"玩家无结果/不存在"。
// gametools 对不存在的玩家通常返回 hasResults=false 或空主体。
// 传入原始 JSON。
bool LooksLikeNotFound(const std::string& raw_json);

}  // namespace bfstats
