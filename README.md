#CMImageDownloader

一个用于配合 Discord 质检机器人工作的图片采集与管理系统，支持图像上传、质检记录、MongoDB 数据存储与前后端交互。

---

## 功能概览

- ✅ Discord Bot 自动收集质检表单信息
- ✅ 提交表单包含产品编号、SKU、存放位置、备注等
- ✅ 后端 Flask 服务支持网页上传图片
- ✅ 图片保存到本地指定路径，支持批量上传、预览
- ✅ MongoDB 存储并映射 `label → bach_code` 数据
- ✅ 支持导出 CSV、日志记录与操作追踪
- ✅ 项目结构清晰，便于后期扩展录货系统或移动端适配

---

## 项目结构

```text
CMImageDownloader/
├── uploader/           # Flask 后端服务
│   ├── templates/      # 网页上传 HTML 表单页面
│   ├── logs/           # 自动生成的操作日志
│   └── app.py          # Flask 主程序
├── bot.py              # Discord Bot 主逻辑
├── .env                # 环境变量配置（不上传）
├── requirements.txt    # 所需依赖包
└── README.md           # 项目说明文档（你现在看的这个）
```
---
## 📦 安装依赖
推荐使用虚拟环境：
python -m venv venv
venv\Scripts\activate  # Windows

pip install -r requirements.txt
