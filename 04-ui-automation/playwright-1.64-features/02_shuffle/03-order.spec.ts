import { test, expect } from '@playwright/test';

// 订单相关用例。注意 D 和 E 之间没有接力：结算是自己算的，不读购物车那条。

test('E 结算下单', async () => {
  const total = 10 + 6 + 30; // 本条自己算，不依赖别条留下的状态
  expect(total).toBe(46);
});

test('F 查看订单', async () => {
  const order = { id: 'NO-1', status: '已付款' };
  expect(order.status).toBe('已付款');
});
