# P1 列表推导：把 1-20 里 3 的倍数挑出来。对照 JS 想一下，JS 要 filter，Python 一行推导式就完了

# arr = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]

# for i in arr:
#     if i % 3 == 0:
#         print(i)


result = [i for i in range(1, 21) if i % 3 == 0]

# print(list(range(1, 21))) # 1-20 的列表
print(result)