"""练习 1：locator.within() —— 「在某个范围里面找元素」（Playwright 1.64 新特性）。

解决的痛点：页面上有很多一模一样的元素（每张商品卡都有一个「加入购物车」、
表格里每一行都有同名单元格），只按文本找会匹配出一堆，没法下手。
老办法是先定位父级再一层层往里链式查找；within() 把它写成一句话的顺序：
    按钮.within(卡片)  —— 读作「卡片里面的那个按钮」，和跟同事说话的顺序一样。

另一个关键点：nth() 这类相对定位在 within() 里是「在每个父级里分别数」的，
所以能一把抓出「每一行的第 3 个单元格」——也就是整列。

运行：python 01_within.py（需要先装好 playwright 和 chromium，见本目录 README）
本页是脚本内置的本地页面，不访问任何网站。
"""

from playwright.sync_api import sync_playwright

# 练习用页面：3 张商品卡（按钮同名）+ 一张 3 行订单表（第 3 列是状态）
PAGE_HTML = """
<h1>水果店</h1>
<div class="card" data-testid="card-apple">
  <h2>苹果</h2><button onclick="add(this)">加入购物车</button>
  <span class="count">已加购：0</span>
</div>
<div class="card" data-testid="card-banana">
  <h2>香蕉</h2><button onclick="add(this)">加入购物车</button>
  <span class="count">已加购：0</span>
</div>
<div class="card" data-testid="card-cherry">
  <h2>樱桃</h2><button onclick="add(this)">加入购物车</button>
  <span class="count">已加购：0</span>
</div>
<table>
  <tr><th>商品</th><th>金额</th><th>状态</th></tr>
  <tr><td>苹果</td><td>10</td><td>已付款</td></tr>
  <tr><td>香蕉</td><td>6</td><td>待付款</td></tr>
  <tr><td>樱桃</td><td>30</td><td>已付款</td></tr>
</table>
<script>
function add(btn) {
  const span = btn.parentElement.querySelector('.count');
  const n = parseInt(span.textContent.split('：')[1]) + 1;
  span.textContent = '已加购：' + n;
}
</script>
"""


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()  # 默认无头模式，跑完自动关
        page = browser.new_page()
        page.set_content(PAGE_HTML)

        # ---- 场景 A：点「香蕉卡片里面的」加入购物车 ----
        # 不用 within 的话，光按按钮名字找会同时匹配到 3 个按钮（严格模式直接报错）：
        same_name_buttons = page.get_by_role("button", name="加入购物车")
        assert same_name_buttons.count() == 3
        print("PASS A0：只按名字找「加入购物车」会匹配到 3 个按钮，点不了")

        banana_card = page.get_by_test_id("card-banana")
        # within()：把按钮的作用域收进香蕉卡片里，全页同名也不怕
        page.get_by_role("button", name="加入购物车").within(banana_card).click()

        assert page.get_by_test_id("card-banana").locator(".count").inner_text() == "已加购：1"
        assert page.get_by_test_id("card-apple").locator(".count").inner_text() == "已加购：0"
        assert page.get_by_test_id("card-cherry").locator(".count").inner_text() == "已加购：0"
        print("PASS A：within() 只点中了香蕉卡片的按钮，另外两张卡没被误伤")

        # ---- 场景 B：一把抓出表格的整列（每一行的第 3 个单元格） ----
        # 先看不用 within 的 nth(2)：它数的是全表的单元格，只会拿到第一行的状态
        plain_third = page.get_by_role("cell").nth(2)
        assert plain_third.count() == 1
        assert plain_third.inner_text() == "已付款"
        print("PASS B0：不用 within，nth(2) 只拿到全表第 3 个单元格（第一行的状态）")

        # 用 within(行)：nth(2) 在每一行里分别数，拿到的就是整列
        status_column = page.get_by_role("cell").nth(2).within(page.get_by_role("row"))
        assert status_column.all_inner_texts() == ["已付款", "待付款", "已付款"]
        print("PASS B：within(行) 让 nth(2) 在每行分别数，整列状态一次断言完")

        browser.close()
    print("\n练习 1 全部通过：locator.within() 已跑通")


if __name__ == "__main__":
    main()
