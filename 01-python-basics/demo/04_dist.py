# P4 字典计数：给 ["pass","fail","pass","pass","fail"]，统计出 {"pass": 3, "fail": 2}

items = ["pass","fail","pass","pass","fail"]

dist = {}

# for item in items:
#     if item in dist:
#         dist[item] += 1
#     else:
#         dist[item] = 1

# dist.get(item, 0) 就是 JS 里 dist[item] ?? 0 的意思，不用再写 if/else 判断在不在。
for item in items:
    dist[item] = dist.get(item, 0) + 1

print(dist)