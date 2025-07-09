# === Discord QA Bot（读取 current_session.txt，记录日志）===
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Modal, TextInput
from dotenv import load_dotenv
from pathlib import Path
import os
import logging
import hashlib
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient

# === 环境变量 ===
load_dotenv()
TOKEN = os.getenv("TOKEN")
SERVER_ID = int(os.getenv("SERVER_ID"))
UPLOAD_URL = os.getenv("UPLOAD_URL")
MONGO_URI = os.getenv("MONGODB_URI")

# === 路径设置 ===
BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = Path(os.getenv("SESSION_CONFIG_PATH"))
LOG_DIR = BASE_DIR / "uploader" / "logs"  # ✅ 指向 uploader/logs 目录
DISCORD_LOG_FILE = LOG_DIR / "discord.log"
LOG_DIR.mkdir(parents=True, exist_ok=True)  # ✅ 确保路径存在

# === 设置独立 Discord 日志器 ===
discord_logger = logging.getLogger("discord_log")
discord_logger.setLevel(logging.INFO)

if not discord_logger.hasHandlers():
    file_handler = logging.FileHandler(DISCORD_LOG_FILE, encoding="utf-8")
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
    file_handler.setFormatter(formatter)
    discord_logger.addHandler(file_handler)

# === MongoDB 初始化 ===
mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client["QCsys"]
collection = db["qa_bot_test"]
label_map = db["label_map"]

# === Bot 设置 ===
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# === 工具函数：读取 current_session.txt ===
def get_current_session_name():
    if CONFIG_FILE.exists():
        session = CONFIG_FILE.read_text(encoding="utf-8").strip()
        print("读取到当前场次为：", session)
        return session
    else:
        print("⚠️ 找不到 current_session.txt，路径是：", CONFIG_FILE)
    return "未设置"



# === 工具函数：生成上传链接 token ===
def generate_token(number: str, user: str, secret="chillmart_secret"):
    raw = f"{number}-{user}-{secret}"
    return hashlib.sha256(raw.encode()).hexdigest()


# === 表单定义 ===
class QAForm(Modal, title="🧾 Inspector Submission Form"):
    bach_code = TextInput(label="Label (e.g. E / F / B / AB)", required=True)
    number = TextInput(label="Item Number (e.g. 286)", required=True)
    optional = TextInput(label="Product Link (optional)", required=False)
    note = TextInput(
        label="QC Note, Scroll down for more(下滑显示更多)", 
        style=discord.TextStyle.paragraph, 
        required=True,
        default=(
            "SKU:\n"
            "Parts Complete? Y / N\n"
            "Condition:\n"
            "No testing required or Tested:\n"
            "QC Note:"
            )
        )
    location = TextInput(label="Storage Location", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        number = self.number.value.strip().upper()
        label = self.bach_code.value.strip().upper()
        url_val = self.optional.value.strip() or "(NA)"
        note_raw = self.note.value.strip()
        location_val = self.location.value.strip() or "(NA)"
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')

        # 检查编号是否已存在
        exists = await collection.find_one({"number": number})
        if exists:
            await interaction.followup.send(f"⚠️ number `{number}` exists.", ephemeral=True)
            return

        # 查询 label → bach_code 映射
        label_doc = await label_map.find_one({"label": label})
        if not label_doc:
            await interaction.followup.send(f"❌ Label `{label}` not found. Please contact the admin", ephemeral=True)
            return

        bach_code = label_doc["bach_code"]
        current_session = get_current_session_name()


        # Parse SKU from note (first line like "SKU: 123")
        lines = note_raw.splitlines()
        sku_val = ""
        if lines and lines[0].strip().lower().startswith("sku"):
            sku_val = lines[0].split(":", 1)[-1].strip()
            lines = lines[1:]  # Remove SKU line
        
        product_note = "\n".join(lines).strip()
        # 插入记录到 MongoDB
        doc = {
            "session": current_session,
            "label": label,
            "number": number,
            "url": url_val,
            "sku": sku_val,
            "note": product_note,
            "location": location_val,
            "user": interaction.user.display_name,
            "timestamp": timestamp,
            "Bach Code": bach_code,
        }
        await collection.insert_one(doc)

        # ✅ 使用独立日志器记录
        discord_logger.info(
            f"[SUBMIT] {interaction.user.display_name} 提交表单 | 场次：{current_session} | 编号：{number} | label：{label} | Note：{product_note[:30]}..."
        )

        # 生成上传链接
        token = generate_token(number, interaction.user.display_name)
        upload_link = f"{UPLOAD_URL}?number={number}&user={interaction.user.display_name}&token={token}"

        await interaction.followup.send(content="✅ Form submitted successfully. Information has been sent to the channel.", ephemeral=True)

        msg_text = (
            f"🏷️ **label**: {label}\n"
            f"📦 **Item number**: {number}\n"
            f"🔗 **Link**: {url_val}\n"
            f"🆔 **SKU**: {sku_val or '(NA)'}\n"
            f"📝 **Note**: {product_note}\n"
            f"🪜 **location**: {location_val}\n"
            f"👤 **Inspector**: {interaction.user.mention}\n"
            f"📅 **Time**: {timestamp}\n"
            # f"📸 上传链接：{upload_link}"
        )
        await interaction.channel.send(content=msg_text)
        await interaction.followup.send(
            content=f"📸 Upload link: {upload_link}",
            ephemeral=True
        )

# === 注册命令 ===
@tree.command(name="f", description="Open QA form (Please upload images via webpage)")
async def qa(interaction: discord.Interaction):
    await interaction.response.send_modal(QAForm())

# === 启动事件 ===
@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Bot 已上线：{bot.user}")
    print(f"current session: {get_current_session_name()}")
bot.run(TOKEN)
