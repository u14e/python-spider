#!/usr/bin/env python3
# _*_ coding:utf-8 _*_

from urllib import request, error, parse
import re
import json
import itertools


def download(url, user_agent=None, num_retries=2):
    if user_agent is None:
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
                            AppleWebKit/537.36 (KHTML, like Gecko) \
                            Chrome/58.0.3029.110 Safari/537.36'
    print('开始下载......', url)
    headers = {
        'User-Agent': user_agent
    }
    req = request.Request(url, headers=headers)
    try:
        html = request.urlopen(req).read()
        html = html.decode('utf-8')
    except error.URLError as e:
        print('Error:', e.reason)
        html = None
        # 当遇到5XX错误时，重试下载，默认重试2次
        if num_retries > 0:
            if hasattr(e, 'code') and 500 <= e.code < 600:
                return download(url, user_agent, num_retries - 1)
    return html


def link_crawler(seed_url, link_regex):
    """
    只爬取所有国家的链接
    形如'http://example.webscraping.com/places/default/view/Zimbabwe-252'之类
    保存在chapter_1.json
    :param seed_url:
    :param link_regex:
    :return:
    """
    crawl_queue = [seed_url]
    seen = set(crawl_queue)
    while crawl_queue:
        m = re.match(r'.*?/index/(\d+)$', crawl_queue[-1])
        if not m and crawl_queue[-1] != seed_url:
            print('爬虫结束......')
            save_as_json(crawl_queue)
            break
        url = crawl_queue.pop()
        html = download(url)
        for link in get_links(html):
            if re.match(link_regex, link):
                link = parse.urljoin(seed_url, link)
                if link not in seen:
                    seen.add(link)
                    crawl_queue.append(link)


def get_links(html):
    """
    获取html中所有的a链接的href
    :param html: str
    :return: list[url]
    """
    webpage_regex = re.compile(r'<a[^>]+href=["\'](.*?)["\']', re.I)
    return webpage_regex.findall(html)


def save_as_json(data):
    with open('chapter_1.json', 'wt', encoding='utf-8') as fout:
        # 需要指定ensure_ascii为False，否则对于non-ASCII characters全部转义
        json.dump({'data': data}, fout, ensure_ascii=False)
        print('输出到chapter_1.json文件。。。')


if __name__ == '__main__':
    # download('http://httpstat.us/500')
    # download('https://www.meetup.com/')
    link_crawler('http://example.webscraping.com', '/places/default/(index|view)')


def crawl_sitemap(url):
    """
    1. 通过网站的sitemap.xml爬虫
    :param url:
    :return:
    """
    sitemap = download(url)
    links = re.findall('<loc>(.*?)</loc>', sitemap)
    for link in links:
        html = download(link)
        # scrape html here


def crawl_by_id():
    """
    2. 通过ID遍历爬虫
    默认id连续，不连续会返回None
    如果不连续，尝试5次，5个id都不连续，爬虫停止
    :return:
    """
    max_errors = 5
    num_errors = 0
    for page in itertools.count(1):
        url = 'http://example.webscraping.com/places/default/view/%d' % page
        html = download(url)
        if html is None:
            num_errors += 1
            if num_errors == max_errors:
                break
        else:
            num_errors = 0
