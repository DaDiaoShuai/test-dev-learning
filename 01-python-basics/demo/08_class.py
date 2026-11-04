# 写一个 CaseRunner 类：add(name, func) 注册用例，run() 依次跑并打印每条通过/失败和最后的通过率；把第 2 课 T2 的用户名 5/6/16/17 位写成 4 个假用例喂给它跑通。
# 再给它加上 logging：每条结果写进 run.log，要有时间、级别、消息。

import logging

logging.basicConfig(filename='run.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
class CaseRunner:
    def __init__(self):
        self.cases = []

    def add(self, name, func):
        self.cases.append((name, func))

    def run(self):
        results = []
        for name, func in self.cases:
            result = func()
            logging.info(f"{name}: {result}")
            results.append(result)
            print(f"{name}: {'PASS' if result else 'FAIL'}")
        logging.info(f"Total: {len(self.cases)}")
        logging.info(f"Pass: {len([result for result in results if result])}")
        logging.info(f"Fail: {len([result for result in results if not result])}")
        logging.info(f"Pass Rate: {len([result for result in results if result]) / len(self.cases) * 100}%")
        print(f"Pass Rate: {len([result for result in results if result]) / len(self.cases) * 100}%")
        return results

def is_valid_username(name):
    return 6 <= len(name) <= 16  # 简化版，先不管字母数字

def case_username_5():
    return not is_valid_username("a" * 5)   # 5 位应被拦，拦住了才算通过
def case_username_6():
    return is_valid_username("a" * 6)
def case_username_16():
    return is_valid_username("a" * 16)
def case_username_17():
    return not is_valid_username("a" * 17)  # 17 位应被拦


if __name__ == "__main__":
    runner = CaseRunner()
    runner.add("case_username_5", case_username_5)
    runner.add("case_username_6", case_username_6)
    runner.add("case_username_16", case_username_16)
    runner.add("case_username_17", case_username_17)
    runner.run()