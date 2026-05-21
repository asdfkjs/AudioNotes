import os
import json
from flask import Flask, render_template_string, request

app = Flask(__name__)
USERS_FILE = "users.json"

# HTML 模板：包含 注册、改密、跳转 三大板块
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>AudioNotes 用户中心</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f0f2f5; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
        .container { display: flex; gap: 20px; flex-wrap: wrap; justify-content: center; }
        .card { background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); width: 300px; text-align: center; }
        h2 { color: #333; margin-bottom: 1rem; font-size: 1.2rem; }
        input { width: 100%; padding: 10px; margin: 8px 0; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box; }
        button { width: 100%; padding: 10px; background: #007bff; color: white; border: none; border-radius: 6px; cursor: pointer; margin-top: 10px; }
        button:hover { background: #0056b3; }
        .btn-green { background: #28a745; margin-top: 20px; font-weight: bold;}
        .btn-green:hover { background: #218838; }
        .msg { font-size: 13px; margin-top: 10px; padding: 5px; border-radius: 4px; }
        .success { color: #155724; background-color: #d4edda; }
        .error { color: #721c24; background-color: #f8d7da; }
        .divider { border-top: 1px solid #eee; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h2>👤 注册新用户</h2>
            <form method="POST" action="/register">
                <input type="text" name="new_username" placeholder="输入新用户名" required>
                <input type="password" name="new_password" placeholder="设置密码" required>
                <button type="submit">立即注册</button>
            </form>
            {% if action == 'register' %}
                <div class="msg {{ status }}">{{ message }}</div>
            {% endif %}
        </div>

        <div class="card">
            <h2>🔒 修改密码</h2>
            <form method="POST" action="/change_password">
                <input type="text" name="username" placeholder="用户名" required>
                <input type="password" name="old_password" placeholder="旧密码 (用于验证)" required>
                <input type="password" name="new_password" placeholder="新密码" required>
                <button type="submit" style="background:#6c757d">确认修改</button>
            </form>
            {% if action == 'change' %}
                <div class="msg {{ status }}">{{ message }}</div>
            {% endif %}
        </div>
    </div>

    <div style="position: fixed; bottom: 30px; text-align: center; width: 100%;">
        <button class="btn-green" style="width: 200px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);" 
                onclick="window.location.href='http://localhost:8000'">
            🚀 进入笔记系统
        </button>
    </div>
</body>
</html>
"""

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

@app.route('/', methods=['GET'])
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('new_username').strip()
    password = request.form.get('new_password').strip()
    
    users = load_users()
    
    if username in users:
        return render_template_string(HTML_TEMPLATE, action='register', status='error', message=f"❌ 用户名 '{username}' 已存在！")
    
    if not username or not password:
         return render_template_string(HTML_TEMPLATE, action='register', status='error', message="❌ 用户名或密码不能为空")

    users[username] = password
    save_users(users)
    return render_template_string(HTML_TEMPLATE, action='register', status='success', message=f"✅ 用户 '{username}' 注册成功！")

@app.route('/change_password', methods=['POST'])
def change_password():
    username = request.form.get('username').strip()
    old_pass = request.form.get('old_password').strip()
    new_pass = request.form.get('new_password').strip()
    
    users = load_users()
    
    if username not in users:
        return render_template_string(HTML_TEMPLATE, action='change', status='error', message="❌ 用户不存在")
    
    if users[username] != old_pass:
        return render_template_string(HTML_TEMPLATE, action='change', status='error', message="❌ 旧密码错误，无法修改")
        
    users[username] = new_pass
    save_users(users)
    return render_template_string(HTML_TEMPLATE, action='change', status='success', message="✅ 密码修改成功！请重新登录")

if __name__ == '__main__':
    print(f"用户管理门户已启动: http://localhost:5000")
    print(f"用户数据文件: {os.path.abspath(USERS_FILE)}")
    app.run(port=5000, debug=True)