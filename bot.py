import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
import aiohttp
import os
import re
import csv
import io
import asyncio
from datetime import datetime

# load_dotenv()
# TOKEN = os.getenv("TOKEN")
# GUILD_ID = int(os.getenv("GUILD_ID")) # 替换为你的服务器 ID
# SAVE_PATH = os.getenv("SAVE_PATH")

# LOG_PATH = os.path.join(SAVE_PATH, "log")
# CSV_PATH = os.path.join(SAVE_PATH, "csv")
# os.makedirs(LOG_PATH, exist_ok=True)
# os.makedirs(CSV_PATH, exist_ok=True)

# intents = discord.Intents.default()
# intents.message_content = True
# intents.guilds = True
# intents.reactions = True
# bot = commands.Bot(command_prefix="!", intents=intents)
# tree = bot.tree

# recorded_data = []

# @bot.event
# async def on_ready():
#     try:
#         await tree.sync()
#         print(f"✅ Bot 已上线：{bot.user}")
#     except discord.errors.Forbidden:
#         print("❌ 缺少权限，无法同步 Slash 指令。请检查 OAuth 权限设置。")

# @tree.command(name="test", description="发送图片后立即执行本指令以上传产品信息")
# @app_commands.describe(
#     y_number="请输入产品编号(如 Y286)",
#     description="请输入产品描述信息",
#     sku="请输入产品 SKU"
# )
# async def upload(interaction: discord.Interaction, y_number: str, description: str, sku: str):
#     await interaction.response.defer(thinking=True)

#     if not interaction.channel:
#         await interaction.followup.send("❌ 无效的频道。", ephemeral=True)
#         return

#     found_image_msg = None
#     async for msg in interaction.channel.history(limit=5):
#         if msg.author.id == interaction.user.id and any(
#             a.content_type and "image" in a.content_type for a in msg.attachments):
#             found_image_msg = msg
#             break

#     if not found_image_msg:
#         await interaction.followup.send("⚠️ 未检测到你最近上传的图片，请先发送图片再使用指令。", ephemeral=True)
#         return

#     folder = re.sub(r'\D', '', y_number.upper())
#     save_dir = os.path.join(SAVE_PATH, folder)
#     os.makedirs(save_dir, exist_ok=True)

#     count = 1
#     for attachment in found_image_msg.attachments:
#         if attachment.content_type and "image" in attachment.content_type:
#             filename = os.path.join(save_dir, f"{folder}-{count+10}.jpg")
#             async with aiohttp.ClientSession() as session:
#                 async with session.get(attachment.url) as resp:
#                     if resp.status == 200:
#                         with open(filename, 'wb') as f:
#                             f.write(await resp.read())
#             count += 1

#     now = datetime.now()
#     timestamp = now.strftime('%Y-%m-%d %H:%M')

#     output = (
#         f"📦 **y_number**：{y_number.upper()}\n"
#         f"🔖 **SKU**：{sku}\n"
#         f"📝 **说明**：{description}\n"
#         f"📷 **图片数量**：{count - 1} 张\n"
#         f"👤 **上传人**：{interaction.user.mention}\n"
#         f"📅 **时间**：{timestamp}"
#     )
#     reply = await found_image_msg.reply(output)

#     recorded_data.append({
#         "y_number": y_number.upper(),
#         "description": description,
#         "图片数量": count - 1,
#         "上传人": interaction.user.display_name,
#         "时间": timestamp,
#         "消息ID": reply.id
#     })

# @tree.command(name="csv", description="手动导出当天上传记录为 CSV")
# async def export_csv(interaction: discord.Interaction):
#     if not recorded_data:
#         await interaction.response.send_message("⚠️ 当前没有记录可导出。", ephemeral=True)
#         return

#     date_str = datetime.now().strftime("%Y-%m-%d")
#     csv_filename = os.path.join(CSV_PATH, f"upload_log_{date_str}.csv")

#     final_data = []
#     for record in recorded_data:
#         msg_id = record.get("消息ID")
#         status = "未标记"

#         # 尝试从当前频道获取消息并读取 reactions
#         try:
#             channel = interaction.channel
#             msg = await channel.fetch_message(msg_id)
#             for reaction in msg.reactions:
#                 if str(reaction.emoji) == "✅":
#                     users = [user async for user in reaction.users() if not user.bot]
#                     if users:
#                         status = f"录货完成（{users[0].display_name}）"
#                 elif str(reaction.emoji) == "🚫":
#                     users = [user async for user in reaction.users() if not user.bot]
#                     if users:
#                         status = f"有问题（{users[0].display_name}）"
#         except Exception:
#             pass

#         final_data.append({
#             "y_number": record["y_number"],
#             "description": record["description"],
#             "图片数量": record["图片数量"],
#             "上传人": record["上传人"],
#             "时间": record["时间"],
#             "状态": status
#         })

#     with open(csv_filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
#         fieldnames = ["y_number", "description", "图片数量", "上传人", "时间", "状态"]
#         writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
#         writer.writeheader()
#         writer.writerows(final_data)

#     recorded_data.clear()
#     await interaction.response.send_message(f"✅ 上传记录已导出：`{csv_filename}`")

# bot.run(TOKEN)
load_dotenv()
TOKEN = os.getenv("TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))  # 替换为你的服务器 ID
SAVE_PATH = os.getenv("SAVE_PATH")

LOG_PATH = os.path.join(SAVE_PATH, "log")
CSV_PATH = os.path.join(SAVE_PATH, "csv")
os.makedirs(LOG_PATH, exist_ok=True)
os.makedirs(CSV_PATH, exist_ok=True)

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.reactions = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

recorded_data = []

@bot.event
async def on_ready():
    try:
        await tree.sync()
        print(f"✅ Bot 已上线：{bot.user}")
    except discord.errors.Forbidden:
        print("❌ 缺少权限，无法同步 Slash 指令。请检查 OAuth 权限设置。")

@tree.command(name="qa", description="发送图片后立即执行本指令以上传产品信息")
@app_commands.describe(
    y_number="请输入产品编号(如 Y286)",
    description="请输入产品描述信息",
    sku="请输入产品 SKU"
)
async def upload(interaction: discord.Interaction, y_number: str, description: str, sku: str):
    await interaction.response.defer(thinking=True)

    if not interaction.channel:
        await interaction.followup.send("❌ 无效的频道。", ephemeral=True)
        return

    found_image_msg = None
    async for msg in interaction.channel.history(limit=5):
        if msg.author.id == interaction.user.id and any(
            a.content_type and "image" in a.content_type for a in msg.attachments):
            found_image_msg = msg
            break

    if not found_image_msg:
        await interaction.followup.send("⚠️ 未检测到你最近上传的图片，请先发送图片再使用指令。", ephemeral=True)
        return

    folder = re.sub(r'\D', '', y_number.upper())
    save_dir = os.path.join(SAVE_PATH, folder)
    os.makedirs(save_dir, exist_ok=True)

    count = 1
    files = []
    for attachment in found_image_msg.attachments:
        if attachment.content_type and "image" in attachment.content_type:
            async with aiohttp.ClientSession() as session:
                async with session.get(attachment.url) as resp:
                    if resp.status == 200:
                        image_bytes = await resp.read()
                        filename_local = os.path.join(save_dir, f"{folder}-{count+10}.jpg")
                        with open(filename_local, 'wb') as f:
                            f.write(image_bytes)
                        file = discord.File(io.BytesIO(image_bytes), filename=f"{folder}-{count+10}.jpg")
                        files.append(file)
                        count += 1

    now = datetime.now()
    timestamp = now.strftime('%Y-%m-%d %H:%M')

    embed = discord.Embed(
        title=y_number.upper(),
        description=(
        f"📦 **y_number**：{y_number.upper()}\n"
        f"🔖 **SKU**：{sku}\n"
        f"📝 **说明**：{description}\n"
        f"📷 **图片数量**：{count - 1} 张\n"
        f"👤 **上传人**：{interaction.user.mention}\n"
        f"📅 **时间**：{timestamp}\n\n"
        ),
        color=discord.Color.blue()
    )

    reply = await interaction.followup.send(embed=embed, files=files)
    
    # 尝试删除用户原始上传的图片消息
    try:
        await found_image_msg.delete()
    # except discord.Forbidden:
    #     print("❌ Bot 无法删除图片消息（权限不足）")
    except Exception as e:
        print(f"❌ 删除失败：{e}")
    recorded_data.append({
        "y_number": y_number.upper(),
        "description": description,
        "图片数量": count - 1,
        "上传人": interaction.user.display_name,
        "时间": timestamp,
        "消息ID": reply.id
    })

@tree.command(name="csv", description="手动导出当天上传记录为 CSV")
async def export_csv(interaction: discord.Interaction):
    if not recorded_data:
        await interaction.response.send_message("⚠️ 当前没有记录可导出。", ephemeral=True)
        return

    date_str = datetime.now().strftime("%Y-%m-%d")
    csv_filename = os.path.join(CSV_PATH, f"upload_log_{date_str}.csv")

    final_data = []
    for record in recorded_data:
        msg_id = record.get("消息ID")
        status = "未标记"

        try:
            channel = interaction.channel
            msg = await channel.fetch_message(msg_id)
            for reaction in msg.reactions:
                if str(reaction.emoji) == "✅":
                    users = [user async for user in reaction.users() if not user.bot]
                    if users:
                        status = f"录货完成（{users[0].display_name}）"
                elif str(reaction.emoji) == "🚫":
                    users = [user async for user in reaction.users() if not user.bot]
                    if users:
                        status = f"有问题（{users[0].display_name}）"
        except Exception:
            pass

        final_data.append({
            "y_number": record["y_number"],
            "description": record["description"],
            "图片数量": record["图片数量"],
            "上传人": record["上传人"],
            "时间": record["时间"],
            "状态": status
        })

    with open(csv_filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
        fieldnames = ["y_number", "description", "图片数量", "上传人", "时间", "状态"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(final_data)

    recorded_data.clear()
    await interaction.response.send_message(f"✅ 上传记录已导出：`{csv_filename}`")

bot.run(TOKEN)
