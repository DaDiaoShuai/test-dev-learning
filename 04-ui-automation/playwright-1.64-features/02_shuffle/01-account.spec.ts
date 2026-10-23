import { test, expect } from '@playwright/test';

// 账号相关用例。每条只用自己内部造的数据，互相独立（见上层 README 的讲解）。

test('A 注册账号', async () => {
  const user = { name: '练习用户A', id: 1 };
  expect(user.id).toBeGreaterThan(0);
});

test('B 退出登录', async () => {
  let loggedIn = true;
  loggedIn = false;
  expect(loggedIn).toBe(false);
});
