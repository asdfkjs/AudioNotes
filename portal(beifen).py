import os
from flask import Flask, render_template_string, request, redirect
from dotenv import set_key, load_dotenv

app = Flask(__name__)
env_file_path = ".env"

# 简单的内嵌 HTML 模板，包含登录、改密和跳转功能
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>AudioNotes 智能笔记系统门户</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f0f2f5; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .card { background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); width: 350px; text-align: center; }
        h2 { color: #333; margin-bottom: 1.5rem; }
        input { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box; }
        button { width: 100%; padding: 10px; background: #007bff; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; margin-top: 10px; }
        button:hover { background: #0056b3; }
        .btn-green { background: #28a745; margin-top: 20px; }
        .btn-green:hover { background: #218838; }
        .msg { color: green; font-size: 14px; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="card">
        <h2>AudioNotes 管理门户</h2>
        <form method="POST" action="/update_password">
            <p style="text-align:left; color:#666; font-size:14px;">修改登录密码：</p>
            <input type="text" name="new_username" placeholder="设置新用户名 (默认 admin)" required>
            <input type="password" name="new_password" placeholder="设置新密码" required>
            <button type="submit">更新配置</button>
        </form>
        {% if message %}
        <p class="msg">{{ message }}</p>
        <p style="font-size:12px; color:red;">注意：更新后请重启 Main 程序生效</p>
        {% endif %}
        
        <hr style="margin: 20px 0; border: 0; border-top: 1px solid #eee;">
        <button class="btn-green" onclick="window.location.href='http://localhost:8000'">进入笔记系统 (Chainlit)</button>
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET'])
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/update_password', methods=['POST'])
def update_password():
    new_user = request.form.get('new_username')
    new_pass = request.form.get('new_password')
    
    # 修改 .env 文件中的配置
    try:
        # 如果 .env 不存在则创建
        if not os.path.exists(env_file_path):
            with open(env_file_path, 'w') as f:
                f.write(f"USERNAME={new_user}\nPASSWORD={new_pass}\n")
        else:
            set_key(env_file_path, "USERNAME", new_user)
            set_key(env_file_path, "PASSWORD", new_pass)
        
        msg = f"成功！用户名已设为 {new_user}"
    except Exception as e:
        msg = f"设置失败: {str(e)}"

    return render_template_string(HTML_TEMPLATE, message=msg)

if __name__ == '__main__':
    print("启动门户系统: http://localhost:5000")
    app.run(port=5000, debug=True)