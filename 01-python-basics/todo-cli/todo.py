# add：加一条，python todo.py add "买菜"
# list：列出所有，带上 id 和是否完成
# done：按 id 标记完成，python todo.py done 1
# delete：按 id 删除，python todo.py delete 1
import argparse
import json
from pathlib import Path

DATA_FILE = Path(__file__).with_name("todos.json")
    
def load_todos(path=DATA_FILE):
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else [data]

def save_todos(todos, path=DATA_FILE):
    with path.open("w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)

def add_task(title, path=DATA_FILE):
    todos = load_todos(path)
    new_id = max((t["id"] for t in todos), default=0) + 1
    new_todo = {"id": new_id, "title": title, "done": False}
    todos.append(new_todo)
    save_todos(todos, path)
    return new_todo

def cmd_add(args):
    task = add_task(args.title)
    print(f"已添加 #{task['id']}: {task['title']}")

def list_task(path=DATA_FILE):
    todos = load_todos(path)
    if not todos:
        return []
    for t in todos:
        mark = "✅" if t["done"] else " "
    return todos

def cmd_list(_args):
    todos = list_task()
    if not todos:
        print("暂无代办")
    for t in todos:
        mark = "✅" if t["done"] else " "
        print(f"[{mark}] #{t['id']} {t['title']}") 
    

def done_task(id, path=DATA_FILE):
    todos = load_todos(path)
    for t in todos:
        if t["id"] == id:
            t["done"] = True
            save_todos(todos, path)
            return t
    return None

def cmd_done(args):
    task = done_task(args.id)
    if not task:
        print(f"找不到 id={args.id}")
    else:
        print(f"已完成 #{args.id}")
    

def delete_task(id, path=DATA_FILE):
    todos = load_todos(path)
    new_todos = [t for t in todos if t["id"] != id]
    if len(new_todos) == len(todos):
        return None
    save_todos(new_todos, path)
    return new_todos
            
def cmd_delete(args):
    todos = delete_task(args.id)
    if not todos:
        print(f"找不到 id={args.id}")
    else:
        print(f"已删除 #{args.id}")

def main():
    parser = argparse.ArgumentParser(description="Todo CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="添加代办")
    p_add.add_argument("title", help="待办标题")
    p_add.set_defaults(func=cmd_add)

    p_list = sub.add_parser("list", help="列出待办")
    p_list.set_defaults(func=cmd_list)

    p_done = sub.add_parser("done", help="标记完成")
    p_done.add_argument("id", type=int, help="待办 id")
    p_done.set_defaults(func=cmd_done)

    p_delete = sub.add_parser("delete", help="删除待办")
    p_delete.add_argument("id", type=int, help="待办 id")
    p_delete.set_defaults(func=cmd_delete)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()