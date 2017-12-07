#!/usr/bin/env python3
# _*_ coding:utf-8 _*_

from pprint import pprint
import json
import re
import requests
from bs4 import BeautifulSoup


class BDTB:
    def __init__(self, base_url):
        self.base_url = base_url
        self.see_lz = 1
        self.title = ''
        self.page_total = 0

    def get_page(self, page_num):
        """
        获取每个url的<class 'bs4.BeautifulSoup'>
        :param page_num: int
        :return: <class 'bs4.BeautifulSoup'>
        """
        playload = {
            'see_lz': self.see_lz,
            'pn': page_num
        }
        html = requests.get(self.base_url, params=playload)
        pprint(html.url)
        return BeautifulSoup(html.text, 'lxml')

    def get_page_items(self, page_num):
        """

        :param page_num:
        :return:
        """

        soup_text = self.get_page(page_num)
        if page_num == 1:
            self.title = self.get_title(soup_text)
            self.page_total = self.get_page_total(soup_text)
        # items_content = soup_text.find_all(id=re.compile(r'post_content_\d*'))
        items = soup_text.find_all('div', 'd_post_content_main')
        for item in items:
            layer_info = self.get_layer_info(item)
            pprint(layer_info)

    def get_title(self, soup_text):
        """
        获取标题
        :param soup_text:
        :return: str
        """
        return soup_text.select('.core_title_txt')[0]['title']

    def get_page_total(self, soup_text):
        """
        获取总页数
        :param soup_text:
        :return: int
        """
        link_href = soup_text.find(id='thread_theme_5').find(class_='pb_list_pager').find_all('a')[-1]['href']
        m = re.search(r'[\?\&]pn=(\d+)$', link_href)
        if m:
            return int(m.group(1))
        pprint('。。。总页数获取失败')
        return 0

    def get_layer_info(self, soup_text):
        """
        获取楼层
        :param soup_text:
        :return: dict
        """
        tails = soup_text.find(class_='core_reply_tail') \
            .find(class_='post-tail-wrap') \
            .find_all('span', 'tail-info', recursive=False)
        layer_num = tails[0].get_text(strip=True)[:-1]
        layer_num = int(layer_num)
        layer_datetime = tails[1].get_text(strip=True)
        layer_markup = soup_text.find(id=re.compile(r'post_content_\d*'))
        br_tags = layer_markup.find_all('br')
        for tag in br_tags:
            tag.replace_with('\n')
        content_list = layer_markup.get_text().split('\n')
        content_list = list(filter(lambda item: bool(item.strip()), content_list))
        content_list = map(lambda item: item.strip(), content_list)
        layer_content = '\n'.join(content_list)

        return {
            'num': layer_num,
            'datetime': layer_datetime,
            'content': layer_content
        }


url = 'https://tieba.baidu.com/p/3138733512/'
bdtb = BDTB(url)
text = bdtb.get_page_items(1)
