import requests
from bs4 import BeautifulSoup
import time
import os
from urllib.parse import urljoin
from tqdm import tqdm

# --- 1. 配置区 ---

# 目标小说目录页的第一页 URL
TOC_URL = "https://www.ghjun.com/0/uzlik09/1/"

# ==================================================================
# 在这里设置你想要保存小说的文件夹路径
# 示例1: 保存在脚本目录下的一个叫 "爬取的小说" 的文件夹里
SAVE_PATH = r"D:\爬取小说" 

# 示例2: 保存在 D盘 的 "MyNovels" 文件夹 (Windows用户)
# 注意路径前面的 r 很重要，可以防止转义字符问题
# SAVE_PATH = r"D:\MyNovels"

# 示例3: 保存在桌面上 (Windows用户, 请替换 YourUsername)
# SAVE_PATH = r"C:\Users\YourUsername\Desktop"

# 示例4: 保存在 "文稿" 文件夹 (macOS用户, 请替换 YourName)
# SAVE_PATH = "/Users/YourName/Documents/Novels"
# ==================================================================


# 设置请求头，模拟浏览器访问
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# ... 其他代码保持不变 ...

# --- 2. 功能函数 ---

def get_html(url):
    """请求指定URL并返回HTML文本"""
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()  # 如果请求失败 (例如 404, 500), 会抛出异常
        response.encoding = response.apparent_encoding # 自动识别编码，防止乱码
        return response.text
    except requests.RequestException as e:
        print(f"请求失败: {url}, 错误: {e}")
        return None

def get_chapter_links(toc_html, base_url):
    """从目录页HTML中解析出所有章节的链接和标题"""
    soup = BeautifulSoup(toc_html, 'html.parser')
    chapters = []
    
    # 根据2025年9月截图的最新分析，章节列表在 class="panel-chapterlist" 的 dl 标签中
    chapter_list_dl = soup.find('dl', class_='panel-chapterlist')
    
    if not chapter_list_dl:
        # 如果找不到章节列表的容器，打印警告并返回空列表
        print("【警告】: 在当前目录页未找到章节列表容器 (dl with class='panel-chapterlist')！请检查网页结构。")
        return []

    # 寻找这个容器内的所有 a 标签 (链接)
    for a_tag in chapter_list_dl.find_all('a'):
        # 确保 a_tag 和它的 href 属性都存在
        if a_tag and a_tag.has_attr('href'):
            title = a_tag.get_text().strip()
            # urljoin 会智能地将基础URL和相对路径拼接成一个完整的URL
            relative_url = a_tag['href']
            full_url = urljoin(base_url, relative_url)
            chapters.append({'title': title, 'url': full_url})
            
    return chapters


def get_chapter_content(chapter_html):
    """从章节页面HTML中解析出正文内容"""
    soup = BeautifulSoup(chapter_html, 'html.parser')
    
    # 根据最新的截图分析，正文在 class="body-content" 的 div 中
    # 我们使用 class_='body-content' 来定位它
    content_div = soup.find('div', class_='body-content')
    
    if not content_div:
        # 如果找不到，打印警告信息，方便调试
        print("【警告】: 在当前章节页面未找到正文容器 (div with class='body-content')！")
        return "【错误】本章内容获取失败，可能是网站结构已更新。"
    
    # 获取所有文本，并用换行符分隔，同时去除首尾空白
    content = content_div.get_text(separator='\n', strip=True)
    
    # 简单清理一下网站可能加的广告语
    # 你可以根据实际情况修改或增加清理规则
    content = content.replace("雨忆文学网 www.ghjun.com，最快更新十日终焉最新章节！", "").strip()

    # 还可以清理掉章节标题，因为我们已经有了
    chapter_title_in_content = soup.find('h1')
    if chapter_title_in_content:
        content = content.replace(chapter_title_in_content.get_text(strip=True), "", 1).strip()
    
    return content


def get_novel_title(toc_html):
    """从目录页获取小说标题"""
    soup = BeautifulSoup(toc_html, 'html.parser')
    # 小说标题通常在 h1 标签里
    title_tag = soup.find('h1')
    if title_tag:
        return title_tag.get_text().strip()
    return "未知小说"


# --- 3. 主逻辑 ---

if __name__ == '__main__':
    print("开始爬取小说...")
    
    # 1. 获取所有章节链接
    all_chapters = []
    current_page = 1
    
    # 获取小说标题，只在第一页获取一次
    first_page_html = get_html(TOC_URL)
    if not first_page_html:
        print("无法获取小说首页，程序退出。")
        exit()
        
    novel_title = get_novel_title(first_page_html)
    print(f"小说标题: 《{novel_title}》")
    
    # 循环处理所有目录页
    while True:
        # 构造当前页的URL，这个网站的翻页逻辑是最后的数字变化
        page_url = TOC_URL.rsplit('/', 2)[0] + f"/{current_page}/"
        print(f"正在获取目录页: {page_url}")
        
        toc_html = get_html(page_url)
        if not toc_html:
            break # 如果页面获取失败，就停止

        chapters_on_page = get_chapter_links(toc_html, TOC_URL)
        
        if not chapters_on_page:
            print("当前页没有找到章节，可能已是最后一页。")
            break # 如果当前页没有章节，说明已经爬完了所有目录页
        
        all_chapters.extend(chapters_on_page)
        current_page += 1
        time.sleep(1) # 礼貌地等待1秒，避免给服务器太大压力

    print(f"共找到 {len(all_chapters)} 个章节。")

        # 2. 逐章爬取内容并保存
    
    # 自动创建保存目录 (如果不存在)
    if not os.path.exists(SAVE_PATH):
        os.makedirs(SAVE_PATH)
        print(f"已创建文件夹: {SAVE_PATH}")

    # 使用 os.path.join 来拼接完整的保存路径和文件名
    filename = os.path.join(SAVE_PATH, f"{novel_title}.txt")
    print(f"开始写入文件: {filename}")
    
    with open(filename, 'w', encoding='utf-8') as f:

        f.write(f"《{novel_title}》\n\n")
        
        # 使用 tqdm 创建一个进度条
        for chapter in tqdm(all_chapters, desc="正在下载章节"):
            chapter_title = chapter['title']
            chapter_url = chapter['url']
            
            chapter_html = get_html(chapter_url)
            if chapter_html:
                content = get_chapter_content(chapter_html)
                
                # 写入章节标题和内容
                f.write(f"【{chapter_title}】\n\n")
                f.write(content)
                f.write("\n\n\n") # 章节之间多空几行，方便阅读
            else:
                f.write(f"【{chapter_title}】 - (本章内容获取失败)\n\n")
                
            time.sleep(0.5) # 同样，每次请求后等待一下

    print(f"任务完成！小说已保存为 《{filename}》")

