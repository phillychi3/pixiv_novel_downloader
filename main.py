
import requests
import re
from fake_useragent import UserAgent
import json
import os
# from concurrent.futures import ThreadPoolExecutor
import multiprocessing as mp
import tqdm
from ebooklib import epub
novelurl = "https://www.pixiv.net/novel/show.php?id="
seriesurl = "https://www.pixiv.net/novel/series/"
if not os.path.exists("novels"):
    os.mkdir("novels")
if not os.path.exists("novel.json"):
    with open("novel.json", "w") as f:
        data = {
            "download_nsfw": False,
            "download_series": False,
            "cookie": "",
            "download_mod": "txt" # txt or epub
        }
        json.dump(data, f, indent=4)
    print("Please read README and edit the novel.json")
    exit()
with open("novel.json", "r") as f:
    data = json.load(f)
    #TODO
    data["download_mod"] = "txt" 

if data["cookie"] == "":
    header = {
        "User-Agent": UserAgent().random,
        "Referer": "https://www.pixiv.net"
    }
else:
    header = {
        "User-Agent": UserAgent().random,
        "Referer": "https://www.pixiv.net",
        "Cookie": data["cookie"]
    }


# def download_epub(url):
#     book = epub.EpubBook()
#     book.set_identifier(f'pixiv-novel-{url[0]["seriesTitle"]}')
#     book.set_title(url[0]["seriesTitle"])
#     book.set_language('en')
#     book.add_author('pixiv downloader')
#     ct = 0
#     for i in url:
#         r = requests.get(i["url"], headers=header)
#         text = re.findall(r'"content":"(.*?)","coverUrl"', r.text)[0]
#         print("ttt")
#         sp = text.split(r'\n\n')
#         eptext = ""
#         if len(sp)< 10:
#             sp = text.split(r'\n')
#         for i in sp:
#             i = "<p>" + i + "</p>"
#             eptext += i
#         i["title"] = re.sub('[\/:*?"<>|，]', '-', i["title"])
#         c1 = epub.EpubHtml(title=i["title"], file_name=f'{ct}.xhtml', lang='en')
#         c1.content = eptext
        
#         book.add_item(c1)
        
#         ct+=1
#     epub.write_epub(f'novels/{url[0]["seriesTitle"]}.epub', book, {})

def download(url):
    if novelurl in url["url"]:
        # print("Downloading " + url["title"])
        r = requests.get(url["url"], headers=header)

        if re.findall(r'cloudflare', r.text):
            print("Cloudflare detected, please change your IP")
            return
        # print(r.text)
        text = re.findall(r'"content":"(.*?)","coverUrl"', r.text)[0]
        text = text.replace(r"\n", "\n")
        url["title"] = re.sub('[\/:*?"<>|，]', '-', url["title"])
        if "seriesTitle" in url:
            with open(f"novels/{url['seriesTitle']}/{url['title']}.txt", "w", encoding="utf-8") as f:
                f.write(text)
        else:
            with open(f"novels/{url['title']}.txt", "w", encoding="utf-8") as f:
                f.write(text)
    else:
        now = 0
        if not os.path.exists(f"novels/{url['seriesTitle']}") and data["download_mod"] == "txt":
            os.mkdir(f"novels/{url['seriesTitle']}")
        while True:
            series = []
            series = requests.get(f"{url['url']}?limit=30&last_order={str(now)}&order_by=asc&lang=zh_tw", headers=header).json()[
                "body"]["seriesContents"]
            if series == []:
                break
            if data["download_mod"] == "txt":
                for i in series:
                    download(
                        {
                            "url": novelurl + str(i["id"]),
                            "title": i["title"],
                            "seriesTitle": url['seriesTitle']
                        }
                    )
            # else:
            #     urls = []
            #     for i in series:
            #         urls.append(
            #             {
            #                 "url": novelurl + str(i["id"]),
            #                 "title": i["title"],
            #                 "seriesTitle": url['seriesTitle']
            #             }
            #         )
            #     download_epub(urls)
            now += 30


def main():
    userid = input("Please enter userid: ")
    now = 0
    urls = []
    while True:
        book = requests.get(
            f"https://www.pixiv.net/ajax/user/{str(userid)}/novels/bookmarks?tag=&offset={str(now)}&limit=48&rest=show&lang=zh_tw#", headers=header).json()
        bookmark = book["body"]["works"]
        if bookmark == []:
            break
        for i in bookmark:
            if not data["download_nsfw"] and "R-18" in i["tags"]:
                continue
            else:
                if "seriesId" in i:
                    if data["download_series"]:
                        if i["seriesTitle"] in os.listdir("novels"):
                            continue
                        urls.append(
                            {
                                "url": f"https://www.pixiv.net/ajax/novel/series_content/{i['seriesId']}",
                                "seriesTitle": i["seriesTitle"]
                            }
                        )
                    else:
                        urls.append(
                            {
                                "url": novelurl + str(i["id"]),
                                "title": i["title"],
                                "seriesId": i["seriesId"],
                                "seriesTitle": i["seriesTitle"]
                            }
                        )
                else:
                    urls.append(
                        {
                            "url": novelurl + str(i["id"]),
                            "title": i["title"]
                        }
                    )
        # with ThreadPoolExecutor(max_workers=10) as executor:
        #     executor.map(download, urls)

        now += 48
    pool = mp.Pool(processes=4)
    for i in tqdm.tqdm(pool.imap_unordered(download, urls), total=len(urls)):
        pass

if __name__ == '__main__':
    main()
