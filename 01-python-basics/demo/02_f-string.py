# P2 f-string：拼出 用例总数 12，通过 10，失败 2，通过率 83.3%，通过率保留 1 位小数，要用数字算出来，不要手写死 83.3

total = 12
passed = 10
failed = 2
rate = passed / total * 100
# rate = round(rate, 1)

# print(f"用例总数 {total}, 通过 {passed}, 失败{failed}, 通过率{rate} %")
# 用 round() 算没错，但测试报告里更推荐直接在 f-string 里控格式
print(f"用例总数 {total}, 通过 {passed}, 失败{failed}, 通过率{rate:.1f}%")