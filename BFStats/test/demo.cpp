// 临时验证程序: 调用 BFStats 导出的 C API 实跑一次真实查询。
// 仅用于开发期验证, 不属于交付产物。
#include "bfstats.h"
#include <cstdio>

int main(int argc, char** argv) {
    const char* name = (argc > 1) ? argv[1] : "AshTwoPoint0";

    printf("BFStats version: %s\n", bf6_version());
    printf("Querying single: %s\n", name);

    char* out = nullptr;
    BF6Result rc = bf6_query_stats(name, BF6_PLATFORM_PC, &out);
    printf("bf6_query_stats rc=%d\n", (int)rc);
    if (rc == BF6_OK && out) {
        printf("JSON (first 800 chars):\n%.800s\n", out);
        bf6_free(out);
    }

    printf("\n--- multiple ---\n");
    const char* names[] = { name, "definitely_not_a_real_player_xyz" };
    char* out2 = nullptr;
    BF6Result rc2 = bf6_query_multiple(names, 2, BF6_PLATFORM_PC, &out2);
    printf("bf6_query_multiple rc=%d\n", (int)rc2);
    if (out2) {
        printf("JSON (first 500 chars):\n%.500s\n", out2);
        bf6_free(out2);
    }
    return 0;
}
