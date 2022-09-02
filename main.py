
import requests
import re
from fake_useragent import UserAgent
import json
import os
from concurrent.futures import ThreadPoolExecutor
novelurl = "https://www.pixiv.net/novel/show.php?id="
seriesurl = "https://www.pixiv.net/novel/series/"
if not os.path.exists("novels"):
    os.mkdir("novels")
if not os.path.exists("novel.json"):
    with open("novel.json", "w") as f:
        data = {
            "download_nsfw": False,
            "download_series": False,
            "cookie": ""
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


def download(url):
    if novelurl in url["url"]:
        print("Downloading " + url["title"])
        r = requests.get(url["url"], headers=header)
        text = re.findall(r'"content":"(.*?)","coverUrl"', r.text)[0]
        text = text.replace(r"\n", "\n")
        if "seriesTitle" in url:
            with open(f"novels/{url['seriesTitle']}/{url['title']}.txt", "w", encoding="utf-8") as f:
                f.write(text)
        else:
            with open(f"novels/{url['title']}.txt", "w", encoding="utf-8") as f:
                f.write(text)

        return
    else:
        now = 0
        if not os.path.exists(f"novels/{url['seriesTitle']}"):
            os.mkdir(f"novels/{url['seriesTitle']}")
        while True:
            series = requests.get(f"{url['url']}?limit=30&last_order{str(now)}&order_by=asc&lang=zh_tw", headers=header).json()[
                "body"]["seriesContents"]
            if series == []:
                break
            urls = []
            for i in series:
                urls.append(
                    {
                        "url": novelurl + str(i["id"]),
                        "title": i["title"],
                        "seriesTitle": url['seriesTitle']
                    }
                )
            with ThreadPoolExecutor(max_workers=5) as executor:
                executor.map(download, urls)
            now += 30
        return


def main():
    userid = input("Please enter userid: ")
    now = 0
    while True:
        book = requests.get(
            # f"https://www.pixiv.net/ajax/user/{str(userid)}/novels/bookmarks?tag=&offset={str(now)}&limit=48&rest=show&lang=zh_tw#", headers=header).json()
            f"https://www.pixiv.net/ajax/user/{str(userid)}/novels/bookmarks?tag=&offset={str(now)}&limit=10&rest=show&lang=zh_tw#", headers=header).json()
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
                with ThreadPoolExecutor(max_workers=5) as executor:
                    executor.map(download, urls)
        now += 48


if __name__ == '__main__':
    main()