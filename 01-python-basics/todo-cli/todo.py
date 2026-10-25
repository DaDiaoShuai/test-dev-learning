# add：加一条，python todo.py add "买菜"
# list：列出所有，带上 id 和是否完成
# done：按 id 标记完成，python todo.py done 1
# delete：按 id 删除，python todo.py delete 1
import argparse
import json
from pathlib import Path

DATA_FILE = Path(__file__).with_name("todos.json")
    
def load_todos():
    if not DATA_FILE.exists():
        return []
    with DATA_FILE.open(encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else [data]

def save_todos(todos):
    with DATA_FILE.open("w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)

def cmd_add(args):
    todos = load_todos()
    new_id = max((t["id"] for t in todos), default=0) + 1
    todos.append({"id": new_id, "title": args.title, "done": False})
    save_todos(todos)
    print(f"已添加 #{new_id}: {args.title}")

def cmd_list(_args):
    todos = load_todos()
    if not todos:
        print("暂无代办")
        return
    for t in todos:
        mark = "✅" if t["done"] else " "
        print(f"[{mark}] #{t['id']} {t['title']}")

def cmd_done(args):
    todos = load_todos()
    for t in todos:
        if t["id"] == args.id:
            t["done"] = True
            save_todos(todos)
            print(f"已完成 #{args.id}")
            return
    print(f"找不到 id={args.id}")

def cmd_delete(args):
    todos = load_todos()
    new_todos = [t for t in todos if t["id"] != args.id]
    if len(new_todos) == len(todos):
        print(f"找不到 id={args.id}")
        return
    save_todos(new_todos)
    print(f"已删除 #{args.id}")
            

def main():
    parser = argparse.ArgumentParser(prog=None, usage=None, description="Todo CLI", epilog=None, parents=[], formatter_class=argparse.HelpFormatter, prefix_chars='-', fromfile_prefix_chars=None, argument_default=None, conflict_handler='error', add_help=True, allow_abbrev=True)
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