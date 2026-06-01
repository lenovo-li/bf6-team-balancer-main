#pragma once

#include <windows.h>
#include <string>
#include <cstdio>

// 统一 trace 前缀, 便于在 VS 输出窗口过滤。
namespace bfstats {

inline void DebugLog(const char* tag, const char* fmt, ...) {
    char msg[1024];
    va_list args;
    va_start(args, fmt);
    _vsnprintf_s(msg, sizeof(msg), _TRUNCATE, fmt, args);
    va_end(args);

    char line[1152];
    _snprintf_s(line, sizeof(line), _TRUNCATE, "[BFStats.%s] %s\n", tag, msg);
    OutputDebugStringA(line);
}

}  // namespace bfstats

#define BF_LOG(tag, ...) ::bfstats::DebugLog(tag, __VA_ARGS__)
