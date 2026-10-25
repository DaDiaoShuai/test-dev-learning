# 新建 test_todo.py，至少 6 条用例，覆盖四个功能，必须用上两个东西：

# fixture：用 pytest 自带的 tmp_path，每个用例给一个干净的临时 JSON 文件，跑完自动清理，不污染你真实的 todos.json
# @pytest.mark.parametrize：比如一次测多个标题的添加，或者多个 id 的完成/删除，别把相似用例复制粘贴好几遍
# 给你一个用例清单参考，照着写就够 6 条：
# add 后能 list 到、add 多条 id 递增、done 后状态变 True、delete 后查不到、done 一个不存在的 id 要有合理处理、数据写进 JSON 后重新读出来还在。

from todo import add_task, done_task, delete_task, list_task
import pytest

@pytest.fixture
def todo_file(tmp_path):
    return tmp_path / "todos.json"

@pytest.mark.parametrize("title", ["soccer", "work", "sleep"])
def test_add_many(todo_file, title):
    task = add_task(title, path=todo_file)
    todos = list_task(path=todo_file)
    assert task["title"] == title, "添加待办错误"
    assert todos is not None, "数据写进 JSON 后重新读出来应该还在才对"
    assert len(todos) == 1
    assert todos[0]["title"] == title
    assert todos[0]["id"] == task["id"]

def test_item_id(todo_file):
    task_1 = add_task("task_1", path=todo_file)
    task_2 = add_task("task_2", path=todo_file)
    task_3 = add_task("task_3", path=todo_file)
    assert task_2["id"] == task_1["id"] + 1 and task_3["id"] == task_2["id"] + 1, "add多条ID应该是递增才对"

def test_done(todo_file):
    task = add_task("test_done", path=todo_file)
    done = done_task(task["id"], path=todo_file)
    err_done = done_task(999, path=todo_file)
    assert done["done"] is True, f"标记完成后的任务的done应该是True, 却是{done['done']}"
    assert err_done is None, f"done一个不存在的id返回值应该为None且提示找不到该任务"

def test_delete(todo_file):
    task = add_task("test_delete", path=todo_file)
    remaining = delete_task(task["id"], path=todo_file)
    # assert len([t for t in remaining if t["id"] == task["id"]]) == 0, "delete后应该查不到才对，现在能查到已删除的"
    assert all(t["id"] != task["id"] for t in remaining), "delete后应该查不到才对，现在能查到已删除的"
    