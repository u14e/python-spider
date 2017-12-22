# coding: utf-8
import os
import requests
from requests.exceptions import RequestException
from hashlib import md5
import pymongo
import re
from multiprocessing import Pool
import json
from bs4 import BeautifulSoup

from config import *

client = pymongo.MongoClient(MONGO_URL, connect=False)
db = client[MONGO_DB]

headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
                    AppleWebKit/537.36 (KHTML, like Gecko) \
                    Chrome/58.0.3029.110 Safari/537.36'
}

proxies = {
    'https': '124.152.32.140:53281'
}


def get_page_index(offset, keyword):
    print('请求第{}个索引页'.format(offset // 20 + 1))
    payload = {
        'offset': offset,
        'format': 'json',
        'keyword': keyword,
        'autoload': True,
        'count': 20,
        'cur_tab': 3,
        'from': 'gallery'
    }
    url = 'https://www.toutiao.com/search_content/'

    try:
        response = requests.get(url, params=payload, headers=headers)
        if response.status_code == 200:
            return response.text
        return None
    except RequestException:
        print('请求索引页{}失败'.format(offset))
        return None


def parse_page_index(html):
    data = json.loads(html)
    if data and 'data' in data.keys():
        for item in data.get('data'):
            yield item.get('url')


def get_page_detail(url):
    print('---请求详情页', url)
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.text
        return None
    except RequestException:
        print('请求详情页失败: {}'.format(url))
        return None


def parse_page_detail(html, url):
    soup = BeautifulSoup(html, 'lxml')
    title = soup.select('title')[0].get_text()
    images_pattern = re.compile(r'BASE_DATA.galleryInfo = {.*?gallery:\s*?JSON.parse\((.*?)\)', re.S)
    result = images_pattern.search(html)
    if result:
        data = json.loads(json.loads(result.group(1)))  # loads两次~~~
        if data and 'sub_images' in data.keys():
            sub_images = data.get('sub_images')
            images = [image.get('url') for image in sub_images]
            for image in images:
                download_image(image)
            return {
                'title': title,
                'url': url,
                'images': images
            }


def save_to_mongo(result):
    if db[MONGO_TABLE].insert(result):
        print('存入数据库成功', result)
        return True
    return False


def download_image(url):
    print('下载图片', url)
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            save_image(response.content, url)
        return None
    except RequestException:
        print('请求图片失败', url)
        return None


def save_image(content, url):
    file_path = '{0}/images/{1}.{2}'.format(os.getcwd(), md5(content).hexdigest(), 'jpg')
    if not os.path.exists(file_path):
        with open(file_path, 'wb') as f:
            f.write(content)


def main(offset=0):
    html_index = get_page_index(offset, KEYWORD)
    for url in parse_page_index(html_index):
        html_detail = get_page_detail(url)
        if html_detail:
            result = parse_page_detail(html_detail, url)
            if result:
                save_to_mongo(result)
            else:
                print('解析详情页失败', url)
        else:
            print('请求详情页失败:', url)


if __name__ == '__main__':
    main()
    groups = [x * 20 for x in range(GROUP_STRAT, GROUP_END+1)]

    pool = Pool()
    pool.map(main, groups)
