
import requests
import re
from fake_useragent import UserAgent
import json
import os
from concurrent.futures import ThreadPoolExecutor
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


def download_epub(url):
    book = epub.EpubBook()
    book.set_identifier(f'pixiv-novel-{url[0]["seriesTitle"]}')
    book.set_title(url[0]["seriesTitle"])
    book.set_language('en')
    book.add_author('pixiv downloader')
    ...

def download(url):
    if novelurl in url["url"]:
        print("Downloading " + url["title"])
        r = requests.get(url["url"], headers=header)
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
        if not os.path.exists(f"novels/{url['seriesTitle']}"):
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
            else:
                urls = []
                for i in series:
                    urls.append(
                        {
                            "url": novelurl + str(i["id"]),
                            "title": i["title"],
                            "seriesTitle": url['seriesTitle']
                        }
                    )
                download_epub(urls)
            now += 30


def main():
    userid = input("Please enter userid: ")
    now = 0
    while True:
        book = requests.get(
            f"https://www.pixiv.net/ajax/user/{str(userid)}/novels/bookmarks?tag=&offset={str(now)}&limit=48&rest=show&lang=zh_tw#", headers=header).json()
        bookmark = book["body"]["works"]
        if bookmark == []:
            break
        urls = []
        for i in bookmark:
            if not data["download_nsfw"] and "R-18" in i["tags"]:
                continue
            else:
                if "seriesId" in i:
                    if data["download_series"]:
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
        with ThreadPoolExecutor(max_workers=10) as executor:
            executor.map(download, urls)
        now += 48


if __name__ == '__main__':
    main()
