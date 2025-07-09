from flask import Flask, request, render_template, jsonify, send_from_directory, Response
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from record import record_bp
import logging
import os
import socket
import hashlib

SECRET_KEY = os.getenv("UPLOAD_SECRET", "chillmart_secret")  # 默认值可修改
app = Flask(__name__)
app.register_blueprint(record_bp)

load_dotenv()  # ← 读取 .env 文件
# === 路径设置 ===
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_BASE = r"C:\test\saveImageTest"
CONFIG_FILE = Path(os.getenv("SESSION_CONFIG_PATH"))
LOG_DIR = BASE_DIR / "logs"
FLASK_LOG_FILE = LOG_DIR / "flask.log"
UPLOAD_LOG_FILE = LOG_DIR / "upload_log.txt"

# === 创建目录 ===
LOG_DIR.mkdir(exist_ok=True)
os.makedirs(UPLOAD_BASE, exist_ok=True)

# === 设置 flask 专属日志器 ===
flask_logger = logging.getLogger("flask_app")
flask_logger.setLevel(logging.INFO)
if not flask_logger.hasHandlers():
    file_handler = logging.FileHandler(FLASK_LOG_FILE, encoding="utf-8")
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
    file_handler.setFormatter(formatter)
    flask_logger.addHandler(file_handler)

# ✅ 屏蔽 werkzeug 默认日志输出
werkzeug_logger = logging.getLogger("werkzeug")
werkzeug_logger.setLevel(logging.ERROR)
werkzeug_logger.propagate = False
werkzeug_logger.handlers.clear()

# === 获取当前场次编号 ===
def get_current_session_name():
    try:    
        if CONFIG_FILE.exists():
            return CONFIG_FILE.read_text(encoding="utf-8").strip()
        return ""
    except Exception as e:
        flask_logger.error(f"[ERROR] 读取 current_session.txt 失败：{e}")
        return ""
    
def is_valid_token(number: str, user: str, token: str):
    raw = f"{number}-{user}-{SECRET_KEY}"
    expected = hashlib.sha256(raw.encode()).hexdigest()
    return token == expected
# === 上传页面 ===
@app.route("/", methods=["GET", "POST"])
def upload_page():

    if request.method == "POST":
        number = request.form.get("number")
        user = request.form.get("user")
        files = request.files.getlist("images")
        token = request.form.get("token")

        if not number or not files:
            flask_logger.warning(f"❌ 提交失败：编号或图片未填写（用户：{user}）")
            return "Number or images not provided.", 400
        if not token or not is_valid_token(number, user, token):
            flask_logger.warning(f"❌ 拒绝上传：token 无效（用户：{user}, 编号：{number}）")
            return "❌ Unauthorized upload request. Token verification failed.", 403


        current_session = get_current_session_name()
        if not current_session:
            flask_logger.warning(f"❗上传失败：未设置 current_session.txt，上传人：{user}，编号：{number}")
            return "❗Current session not configured. Please contact administrator.", 400

        save_path = os.path.join(UPLOAD_BASE, current_session, number)
        os.makedirs(save_path, exist_ok=True)

        existing = os.listdir(save_path)
        used_numbers = []
        for name in existing:
            try:
                base = name.split('.')[0]
                suffix = int(base.split('-')[-1])
                used_numbers.append(suffix)
            except Exception as e:
                flask_logger.warning(f"⚠️ 无法解析文件名：{name}，跳过。错误：{e}")
                continue

        next_index = max(used_numbers + [9]) + 1
        success_count = 0
        for file in files:
            ext = os.path.splitext(file.filename)[1]
            filename = f"{number}-{next_index}{ext}"
            file_path = os.path.join(save_path, filename)

            try:
                file.save(file_path)
                next_index += 1
                success_count += 1

                with open(UPLOAD_LOG_FILE, "a", encoding="utf-8") as f:
                    f.write(f"[UPLOAD] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {user} 上传 {filename} 至 {current_session}/{number}\n")

                flask_logger.info(f"✅ {user} 上传图片 {filename} 至 {current_session}/{number}")
            except Exception as e:
                flask_logger.error(f"❌ {user} 上传图片失败：{filename}，错误：{e}")

        return f"✅ Successfully uploaded {success_count} image(s) to folder {current_session}/{number}"

    return render_template("upload.html")

# === 图片预览 ===
@app.route("/images")
def get_existing_images():
    number = request.args.get("number")
    current_session = get_current_session_name()
    folder = os.path.join(UPLOAD_BASE, current_session, number)
    if not os.path.exists(folder):
        return jsonify([])

    files = [
        f for f in os.listdir(folder)
        if os.path.isfile(os.path.join(folder, f)) and f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))
    ]
    return jsonify(files)

# === 删除图片 ===
@app.route("/delete-image", methods=["POST"])
def delete_image():
    number = request.args.get("number")
    filename = request.args.get("filename")
    user = request.args.get("user") or "unknown"
    token = request.args.get("token")
    current_session = get_current_session_name()

    if not number or not filename:
        flask_logger.warning(f"❌ 删除失败：参数缺失（用户：{user}）")
        return "Missing parameters.", 400
    
    if not is_valid_token(number, user, token):
        flask_logger.warning(f"❌ 删除失败：Token 校验失败（用户：{user}）")
        return "❌ Unauthorized delete request. Token verification failed.", 403
    
        # ✅ 验证 token 防止伪造
    if not token or not is_valid_token(number, user, token):
        flask_logger.warning(f"❌ 拒绝删除：token 无效（用户：{user}, 编号：{number}）")
        return "❌ Unauthorized delete request. Token verification failed.", 403
    file_path = os.path.join(UPLOAD_BASE, current_session, number, filename)
    try:    
        if os.path.exists(file_path):
            os.remove(file_path)
            with open(UPLOAD_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(f"[DELETE] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {user} 删除 {filename} 从 {current_session}/{number}\n")
            flask_logger.info(f"🗑️ {user} 删除了图片 {filename} 从 {current_session}/{number}")
            return "✅ deleted"
        else:
            flask_logger.warning(f"❌ {user} 删除失败：文件 {filename} 不存在")
            return "❌ file not exist", 404
    except Exception as e:
        flask_logger.error(f"[ERROR] 删除图片时出错：{filename}，用户：{user}，错误：{e}")
        return "❌ Failed to delete image. Server error.", 500
    
    
# === 图片静态预览 ===
@app.route("/<number>/<filename>")
def serve_image(number, filename):
    current_session = get_current_session_name()
    folder = os.path.join(UPLOAD_BASE, current_session, number)
    return send_from_directory(folder, filename)

# === 实时日志页面 + 拉取 API ===
@app.route("/logs")
def log_viewer():
    return render_template("log_viewer.html")

@app.route("/get-log")
def get_log():
    log_type = request.args.get("file", "flask")
    if log_type == "flask":
        log_path = FLASK_LOG_FILE
    elif log_type == "discord":
        log_path = BASE_DIR / "logs" / "discord.log"
    elif log_type == "upload":
        log_path = UPLOAD_LOG_FILE
    else:
        return Response("❌ Unknown log type", status=400)

    if log_path.exists():
        content = log_path.read_text(encoding="utf-8")[-8000:]
        return Response(content, mimetype="text/plain")
    return Response("❌ Log file not found.", status=404)

# === 启动服务 ===
if __name__ == "__main__":
    flask_logger.info("🚀 Flask 服务器启动")
    print(" * Running on all addresses (0.0.0.0)")
    print(" * Running on http://127.0.0.1:5000")
    print("* Running on http://127.0.0.1:5000/logs")
    print(f" * Running on http://{socket.gethostbyname(socket.gethostname())}:5000")
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
