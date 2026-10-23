import { test, expect } from '@playwright/test';

// 商品相关用例。同样是每条自己准备数据，不读其他文件、其他用例的结果。

test('C 搜索商品', async () => {
  const results = ['苹果', '香蕉', '樱桃'].filter((x) => x.includes('苹'));
  expect(results).toEqual(['苹果']);
});

test('D 加入购物车', async () => {
  const cart: string[] = []; // 每条用例一份全新的购物车
  cart.push('樱桃');
  expect(cart).toHaveLength(1);
});
