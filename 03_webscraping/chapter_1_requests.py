#!/usr/bin/env python3
# _*_ coding:utf-8 _*_

from urllib import parse
import requests
import re
import json
import itertools
import datetime
import time

from chapter_1 import Throttle, get_links, get_robots, same_domain, save_as_json


def download(url, headers={}, proxy=None, num_retries=2, data=None, timeout=5):
    print('开始下载......', url)
    if proxy:
        res = requests.get(url, headers=headers, proxies={
            parse.urlparse(url).scheme: proxy
        })
    else:
        res = requests.get(url, headers=headers)
    
    html = res.text

    if 500 <= res.status_code < 600:
        # 当遇到5XX错误时，重试下载，默认重试2次
        print('下载出错:', e.response)
        html = None
        if num_retries > 0:
            return download(url, headers, proxy,
                            num_retries - 1, data, timeout)
    return html    


def link_crawler(seed_url, link_regex=None, delay=0, proxy=None, headers=None, user_agent='wswp', num_retries=2):
    """
    只爬取所有国家的链接
    形如'http://example.webscraping.com/places/default/view/Zimbabwe-252'之类
    保存在chapter_1.json
    """
    rp = get_robots(seed_url)
    throttle = Throttle(delay)

    headers = headers or {}
    if user_agent:
        headers['User-Agent'] = user_agent

    crawl_queue = [seed_url]
    seen = set(crawl_queue)

    while crawl_queue:
        # 没有index索引页时代表爬虫结束
        m = re.match(r'.*?/index/(\d+)$', crawl_queue[-1])
        if not m and crawl_queue[-1] != seed_url:
            print('爬虫结束......')
            save_as_json(crawl_queue)
            break

        url = crawl_queue.pop()
        # 检查robots.txt禁止爬虫的url
        if rp.can_fetch(headers['User-Agent'], url):
            throttle.wait(url)
            html = download(url, headers, proxy, num_retries)
            for link in get_links(html):
                if re.match(link_regex, link):
                    link = parse.urljoin(seed_url, link)
                    if link not in seen:
                        seen.add(link)
                        if same_domain(seed_url, link):
                            crawl_queue.append(link)
        else:
            print('Blocked by robots.txt:', url)

if __name__ == '__main__':
    user_agent_main = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
                                AppleWebKit/537.36 (KHTML, like Gecko) \
                                Chrome/58.0.3029.110 Safari/537.36'
    link_crawler('http://example.webscraping.com', '/places/default/(index|view)', user_agent=user_agent_main)