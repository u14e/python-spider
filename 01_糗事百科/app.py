#!/usr/bin/env python3
# _*_ coding:utf-8 _*_

from pprint import pprint
import json
import requests
from bs4 import BeautifulSoup


class QSBK:
    def __init__(self):
        self.page_index = 1
        self.page_max = 10
        self.url = 'http://www.qiushibaike.com/hot/page/'
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
                    AppleWebKit/537.36 (KHTML, like Gecko) \
                    Chrome/58.0.3029.110 Safari/537.36'
        self.headers = {
            'user-agent': self.user_agent
        }
        self.stories = []
        self.enable = False

    def get_page(self, page_index):
        """
        获取每个url的<class 'bs4.BeautifulSoup'>
        :return: <class 'bs4.BeautifulSoup'>
        """
        url = self.url + str(page_index)
        html = requests.get(url, headers=self.headers)
        soup_text = BeautifulSoup(html.text, 'lxml')
        return soup_text

    def get_page_items(self, page_index):
        """
        获取每个页面处理好的list
        :param page_index: int
        :return: list
        """
        soup_text = self.get_page(page_index)
        story_list = []
        content = soup_text.find(id='content-left')
        airticles = content.find_all(class_="article")
        airticles = list(filter(lambda airticle: not airticle.find(class_='thumb'), airticles))
        for airtile in airticles:
            author = airtile.find('h2').get_text(strip=True)
            content = airtile.find(class_='content').find('span').get_text(strip=True)
            comments = airtile.find(class_='stats').find(class_='number').get_text(strip=True)
            story_list.append({
                'author': author,
                'content': content,
                'comments': int(comments)
            })
        return story_list

    def loadPage(self):
        if self.enable is True:
            story_list = self.get_page_items(self.page_index)
            if story_list:
                self.stories.extend(story_list)
                self.page_index += 1

    def start(self):
        print('。。。。。。。开始读取糗事百科。。。。。。')
        self.enable = True
        current_page = 0
        while self.enable is True:
            self.loadPage()
            current_page += 1
            pprint('loaded page %d' % current_page)
            if current_page >= self.page_max:
                self.enable = False
                self.end()

    def end(self):
        if self.enable is False:
            print('。。。。。。。。。爬虫结束。。。。。。。。。')
            self.json_out()

    def json_out(self):
        """
        输出到json文件
        :return:
        """
        with open('app.json', 'wt', encoding='utf-8') as fout:
            # 需要指定ensure_ascii为False，否则对于non-ASCII characters全部转义
            json.dump({'stories': self.stories}, fout, ensure_ascii=False)
            print('输出到json文件。。。')


spider = QSBK()
spider.start()
