import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Modal, TextInput
from dotenv import load_dotenv
import aiohttp
import os
import re
import io
import logging
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
# from pymongo import MongoClient
import asyncio

#------------------------environment variable ---------------------------
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
SERVER_ID = int(os.getenv("SERVER_ID"))
SAVE_PATH = os.getenv("SAVE_PATH")
MONGO_URI = os.getenv("MONGODB_URI")

#---------------路径设置-----------------------
LOG_PATH = os.path.join(SAVE_PATH, "log")
os.makedirs(LOG_PATH, exist_ok=True)

#---------------MongoDB-----------------------
mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client["chillmartTemp"]
collection = db["qa_bot"]

#-------------log-----------------------------
log_file = os.path.join(LOG_PATH, "qa_bot.log")
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    encoding='utf-8'
)

#--------------discord bot ------------------------
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.reactions = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree



# 异步下载函数
download_lock = asyncio.Lock()
async def download_image(session, attachment, folder, index):
    if attachment.content_type and "image" in attachment.content_type:
        async with session.get(attachment.url) as resp:
            if resp.status == 200:
                image_bytes = await resp.read()
                filename = f"{folder}-{index + 10}.jpg"
                filepath = os.path.join(SAVE_PATH, folder, filename)
                async with download_lock:
                    with open(filepath, 'wb') as f:
                        f.write(image_bytes)
                return discord.File(io.BytesIO(image_bytes), filename=filename)
    return None



# === Modal 表单定义 ===
class QAForm(Modal, title="🧾 质检表单填写"):
    bach_code = TextInput(label="label (E / F/ B)", placeholder="请输入 E/ F/ B", required=True)
    number = TextInput(label="产品编号（如 286）", placeholder="输入产品编号", required=True)
    optional = TextInput(label="产品链接（可选）", placeholder="https://example.com", required=False)
    description = TextInput(label="产品描述（格式：SKU123/描述）", style=discord.TextStyle.paragraph, required=True)
    location = TextInput(label="存放位置", placeholder="例如：？？？", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        logging.info(f"📝 用户 {interaction.user.display_name} 提交了质检表单")


        # 检查图片
        found_image_msg = None
        async for msg in interaction.channel.history(limit=5):
            if msg.author.id == interaction.user.id and any(
                a.content_type and "image" in a.content_type for a in msg.attachments):
                found_image_msg = msg
                break

        if not found_image_msg:
            await interaction.followup.send("⚠️ 未检测到你最近上传的图片，请先发送图片再使用指令。", ephemeral=True)
            return

        # 检查重复编号
        number_upper = self.number.value.upper()
        if await collection.find_one({"number": number_upper}):
            await interaction.followup.send(
                f"⚠️ 编号 `{number_upper}` 已存在，请检查是否重复提交。或者呼叫 admin 处理。",
                ephemeral=False
            )
            logging.warning(f"❌ 拒绝重复提交：{number_upper} by {interaction.user.display_name}")
            return

        # 校验 Bach Code
        bach_code_clean = self.bach_code.value.strip().upper()
        if bach_code_clean not in ["E", "F", "B"]:
            await interaction.followup.send("❌ Label 只能是 E 或 F 或 B，请重新填写。", ephemeral=True)
            return
        # 映射 Bach ID
        if bach_code_clean == "E":
            bach_id = "1950-BUNJ-2507002"
        elif bach_code_clean == "F":
            bach_id = "1120-BRNJ-2507001"
        else:  # bach_code_clean == "B"
            bach_id = "2505-1STIN50"

        # 获取链接与描述
        url_val = self.optional.value.strip() if self.optional.value.strip() else "（未填写）"
        product_desc = self.description.value.strip()
        
        # 保存图片
        save_dir = os.path.join(SAVE_PATH, number_upper)
        async with download_lock:
            os.makedirs(save_dir, exist_ok=True)

        async with aiohttp.ClientSession() as session:
            tasks = [
                download_image(session, att, number_upper, idx)
                for idx, att in enumerate(found_image_msg.attachments)
            ]
            files = await asyncio.gather(*tasks)
            files = [f for f in files if f is not None]

        # 时间戳
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')

        # Embed 卡片
        embed_description = (
            f"🏷️ **label**：{bach_code_clean}\n"
            f"📦 **编号**：{number_upper}\n"
            f"🔗 **链接**：{url_val}\n"
            f"📝 **描述**：{product_desc}\n"
            f"📷 **图片数量**：{len(files)} 张\n"
            f"🪜 **位置**：{self.location.value or '（未填写）'}\n"
            f"👤 **上传人**：{interaction.user.mention}\n"
            f"📅 **时间**：{timestamp}"
        )
        embed = discord.Embed(
            title=number_upper,
            description=embed_description,
            color=discord.Color.blue()
        )

        reply = await interaction.followup.send(embed=embed, files=files)
        jump_url = f"https://discord.com/channels/{SERVER_ID}/{reply.channel.id}/{reply.id}"

        # 写入 MongoDB
        doc = {
            "label": bach_code_clean,
            "number": number_upper,
            "url": url_val,
            "description": product_desc,
            "location": self.location.value,
            "image_count": len(files),
            "user": interaction.user.display_name,
            "timestamp": timestamp,
            "jump_url": jump_url,
            "Bach Code": bach_id,
            "record_status": False
        }
        await collection.insert_one(doc)
        logging.info(f"✅ 上传记录已保存到数据库：{doc}")

        try:
            await found_image_msg.delete()
        except Exception as e:
            logging.warning(f"❌ 删除图片消息失败：{e}")

# === Slash 指令绑定 ===
@tree.command(name="qa", description="打开质检上传表单")
async def open_form(interaction: discord.Interaction):
    await interaction.response.send_modal(QAForm())

@bot.event
async def on_ready():
    try:
        await tree.sync()
        print(f"✅ Bot 已上线：{bot.user}")
    except discord.errors.Forbidden:
        print("❌ 缺少权限，无法同步 Slash 指令。请检查 OAuth 权限设置。")

bot.run(TOKEN)
