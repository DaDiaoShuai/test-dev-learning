# P3 异常处理：写函数读一个 JSON 测试数据文件，文件不存在时捕获 FileNotFoundError，JSON 非法时捕获 JSONDecodeError，都打印人话提示。对照 JS 的 try/catch，Python 是 try/except
import json

def read_json_file(file_path):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        print(f"文件{file_path}不存在")
    except json.JSONDecodeError:
        print(f"文件{file_path} JSON 格式非法")
    except Exception as e:
        print(f"读取文件{file_path}时出错：{e}")

data = read_json_file("test.json")
print(data)