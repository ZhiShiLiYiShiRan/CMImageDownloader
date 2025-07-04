import os
import requests

BASE_PATH = r"C:\\Y-112\\manually"

def download_image(url, folder_path):
    try:
        filename = url.split("/")[-1].split("?")[0]
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            os.makedirs(folder_path, exist_ok=True)
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            print(f"✅ 下载成功: {file_path}")
        else:
            print(f"❌ 下载失败: {url}")
    except Exception as e:
        print(f"❌ 错误: {e}")

def main():
    folder_name = input("请输入保存文件夹名（如186）：").strip()
    folder_path = os.path.join(BASE_PATH, folder_name)

    print("请输入图片链接（每行一个，输入空行结束）：")
    urls = []
    while True:
        line = input().strip()
        if not line:
            break
        urls.append(line)

    for url in urls:
        download_image(url, folder_path)

if __name__ == "__main__":
    main()