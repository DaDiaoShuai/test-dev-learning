import { defineConfig } from '@playwright/test';

// 练习用的最小配置。
// fullyParallel: true 是关键：--shuffle 只会打乱「文件之间」的顺序，
// 文件内部的用例要在并行模式下才会被打乱（串行组 serial 除外）。
// workers: 1 是为了练习时看得清楚：一台工人按打乱后的顺序逐个执行，
// 输出的先后就是被打乱的顺序；平时项目里不用这样限。
export default defineConfig({
  testDir: '.',
  fullyParallel: true,
  workers: 1,
  reporter: 'list',
});
