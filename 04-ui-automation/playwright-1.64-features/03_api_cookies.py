"""练习 3：APIRequestContext 的 cookie 管理（Playwright 1.64 新特性）。

以前 cookie 的增删查只有浏览器上下文（BrowserContext）有；接口测试想预置
一个登录 cookie，只能绕道storageState 文件或手动拼请求头。1.64 给接口请求
上下文（APIRequestContext）补齐了同一套方法，两边用法一致：
    add_cookies()   预置 cookie（最常见的用法：跳过登录接口，直接带身份发请求）
    cookies(url)    查某个地址下当前存着哪些 cookie
    clear_cookies() 清除（可按 name / domain / path 只清一条，不传参清全部）

本练习用 httpbin.org/cookies 当靶子：它会把你发过去的 cookie 原样回显，
方便断言「到底带没带上」。全程不打开浏览器，纯接口。

运行：python 03_api_cookies.py
"""

import os
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

BASE = "https://httpbin.org"


def proxy_from_env():
    """有些网络（公司、沙箱）必须走代理才能出外网：环境变量里配了就带上。
    自己电脑上没配这个变量时返回 None，行为和不加代理完全一样。"""
    raw = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    if not raw:
        return None
    u = urlparse(raw)
    proxy = {"server": f"{u.scheme}://{u.hostname}:{u.port}"}
    if u.username:
        proxy["username"] = u.username
    if u.password:
        proxy["password"] = u.password
    return proxy


def main():
    with sync_playwright() as p:
        # 新建一个接口请求上下文：可以理解成「一个专门发 HTTP 请求的会话」
        ctx = p.request.new_context(base_url=BASE, proxy=proxy_from_env())

        # 1）预置两个 cookie（url 表示这些 cookie 是给哪个站点准备的）
        ctx.add_cookies([
            {"name": "session-id", "value": "42", "url": BASE},
            {"name": "visitor", "value": "new", "url": BASE},
        ])
        names = {c["name"]: c["value"] for c in ctx.cookies(BASE)}
        assert names == {"session-id": "42", "visitor": "new"}, names
        print("PASS 1：add_cookies 预置成功，cookies() 查到两个 cookie")

        # 2）发请求时 cookie 会被自动带上（httpbin 把收到的 cookie 回显回来）
        data = ctx.get("/cookies").json()
        assert data["cookies"] == {"session-id": "42", "visitor": "new"}, data
        print("PASS 2：请求自动带上了预置 cookie，服务端回显一致")

        # 3）只清掉其中一条（按名字清），另一条不受影响
        ctx.clear_cookies(name="session-id")
        names = {c["name"] for c in ctx.cookies(BASE)}
        assert names == {"visitor"}, names
        data = ctx.get("/cookies").json()
        assert data["cookies"] == {"visitor": "new"}, data
        print("PASS 3：clear_cookies(name=...) 只清了 session-id，请求里也只剩 visitor")

        # 4）不带参数清全部
        ctx.clear_cookies()
        assert ctx.cookies(BASE) == []
        data = ctx.get("/cookies").json()
        assert data["cookies"] == {}, data
        print("PASS 4：clear_cookies() 清空后，请求不再带任何 cookie")

        ctx.dispose()
    print("\n练习 3 全部通过：API cookie 的增、查、清已跑通")


if __name__ == "__main__":
    main()
