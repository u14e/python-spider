#!/usr/bin/env python3
# _*_ coding:utf-8 _*_

from urllib import request, error, parse, robotparser
import re
import json
import itertools
import datetime
import time


def download(url, headers, proxy, num_retries, data=None):
    print('开始下载......', url)
    req = request.Request(url, headers=headers, data=data)
    try:
        # 代理
        if proxy:
            proxy_params = {
                parse.urlparse(url).scheme: proxy  # 类似'http': '192.168.0.0'
            }
            proxy_handler = request.ProxyHandler(proxy_params)
            opener = request.build_opener(proxy_handler)
            request.install_opener(opener)
            html = opener.open(req).read()
        else:
            html = request.urlopen(req).read()
        html = html.decode('utf-8')
    except error.URLError as e:
        print('下载出错:', e.reason)
        html = None
        # 当遇到5XX错误时，重试下载，默认重试2次
        if num_retries > 0:
            if hasattr(e, 'code') and 500 <= e.code < 600:
                return download(url, headers, proxy, num_retries - 1, data)
    return html


class Throttle:
    """
    在同一domain下，添加相邻两次请求的延迟
    """

    def __init__(self, delay):
        self.delay = delay
        self.domains = {}

    def wait(self, url):
        domain = parse.urlparse(url).netloc
        last_accessed = self.domains.get(domain)
        if self.delay > 0 and last_accessed is not None:
            sleep_secs = self.delay - (datetime.datetime.now() - last_accessed).seconds
            if sleep_secs > 0:
                print('will wait %ds' % sleep_secs)
                time.sleep(sleep_secs)
        self.domains[domain] = datetime.datetime.now()


def link_crawler(seed_url, link_regex=None, delay=0, proxy=None, headers=None, user_agent='wswp', num_retries=2):
    """
    只爬取所有国家的链接
    形如'http://example.webscraping.com/places/default/view/Zimbabwe-252'之类
    保存在chapter_1.json
    :param seed_url:
    :param link_regex:
    :param delay:
    :param proxy:
    :param headers:
    :param user_agent:
    :param num_retries:
    :return:
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


def get_links(html):
    """
    获取html中所有的a链接的href
    :param html: str
    :return: list[url]
    """
    webpage_regex = re.compile(r'<a[^>]+href=["\'](.*?)["\']', re.I)
    return webpage_regex.findall(html)


def get_robots(url):
    """
    为该链接初始化robots
    :param url:
    :return:
    """
    rp = robotparser.RobotFileParser()
    rp.set_url(parse.urljoin(url, '/robots.txt'))
    rp.read()
    return rp


def same_domain(url1, url2):
    """
    判断两个url是否属于同一域名下
    :param url1:
    :param url2:
    :return:
    """
    return parse.urlparse(url1).netloc == parse.urlparse(url2).netloc


def save_as_json(data):
    with open('chapter_1.json', 'wt', encoding='utf-8') as fout:
        # 需要指定ensure_ascii为False，否则对于non-ASCII characters全部转义
        json.dump({'data': data}, fout, ensure_ascii=False)
        print('输出到chapter_1.json文件。。。')


if __name__ == '__main__':
    # download('http://httpstat.us/500')
    # download('https://www.meetup.com/')
    user_agent_main = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
                                AppleWebKit/537.36 (KHTML, like Gecko) \
                                Chrome/58.0.3029.110 Safari/537.36'
    link_crawler('http://example.webscraping.com', '/places/default/(index|view)', user_agent=user_agent_main)


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
