#!/usr/bin/env python3
# _*_ coding:utf-8 _*_

import requests
from urllib import parse
import os
import re
from bs4 import BeautifulSoup


class TaoBaoMM:
    def __init__(self):
        self.siteURL = 'http://mm.taobao.com/json/request_top_list.htm'
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
                    AppleWebKit/537.36 (KHTML, like Gecko) \
                    Chrome/58.0.3029.110 Safari/537.36'
        }

    def get_page(self, pn):
        """
        获取索引页的内容
        """
        res = requests.get(self.siteURL, params={'page': pn}, headers=self.headers, timeout=5)
        print('下载...索引页', res.url)
        return res.text

    def get_content(self, pn):
        """
        获取索引页所有MM的信息， 返回list
        """
        html = self.get_page(pn)
        if not html:
            raise NoneError('获取索引页%d为空...' % pn)
        soup = BeautifulSoup(html, 'lxml')
        items = soup.find_all(class_="list-item")
        contents = []
        for item in items:
            avatar_tag = item.find(class_="lady-avatar")
            user_url = avatar_tag['href']
            logo_tag = avatar_tag.find('img', recursive=False)
            logo = logo_tag['src']
            info_tag = item.find(class_="top")
            name = info_tag.find(class_="lady-name").get_text()
            user_info_url = info_tag.find(class_="lady-name")['href']
            age = info_tag.find('em', recursive=False).find('strong', recursive=False).get_text()
            city = info_tag.find('span', recursive=False).get_text()
            contents.append([user_url, logo, name, age, city, user_info_url])
        return contents

    def get_detail_page(self, url):
        """
        获取MM个人详情页的内容
        """
        url_parsed = parse.urlparse(url)
        query = parse.parse_qs(url_parsed.query)
        user_id = query['user_id']
        # 个人资料页因为是js动态加载的页面，所以需要在https://mm.taobao.com/self/info/model_info_show.htm找到域名
        show_res = requests.get('https://mm.taobao.com/self/info/model_info_show.htm', params={'user_id': user_id})
        # 通过show_html查找到里面的域名
        soup = BeautifulSoup(show_res.text, 'lxml')
        domain_wrapper = soup.find(class_='mm-p-domain-info')
        if not domain_wrapper:
            print('没有个人域名233')
            return None
        domain = domain_wrapper.find(class_='mm-p-info-cell').find('span').get_text()
        detail_url = 'https:' + domain
        res = requests.get(detail_url, headers=self.headers, timeout=5)
        print('下载详情页...', detail_url)
        return res.text

    def get_all_img(self, html):
        """
        获取MM个人详情页的所有图片地址
        """
        soup = BeautifulSoup(html, 'lxml')
        wrapper = soup.find(id='J_ScaleImg')
        imgs = wrapper.find_all('img', src=re.compile(r'.\w{3,4}$'))
        img_url_list = []
        for img in imgs:
            img_url = img['src']
            img_url_list.append(img_url)
        return img_url_list

    def save_all_img(self, img_url_list, name):
        print('发现 {} 共有 {} 张照片'.format(name, len(img_url_list)))
        for num, img_url in enumerate(img_url_list):
            regex = re.compile(r'(.*?).(\w{3,4})$')
            tail = regex.search(img_url).group(2)
            filename = name + '/' + str(num + 1) + '.' + tail
            self.save_img(img_url, filename)

    def save_logo(self, logo, name):
        regex = re.compile(r'(.*?).(\w{3,4})$')
        tail = regex.search(logo).group(2)
        filename = name + '/logo.' + tail
        self.save_img(logo, filename)

    def save_img(self, image_url, filename):
        res = requests.get('https:' + image_url)
        with open(filename, 'wb') as fout:
            fout.write(res.content)
            print('保存图片...{}'.format(filename))

    def save_brief(self, content, name):
        filename = name + '/' + name + '.txt'
        with open(filename, 'wt', encoding='utf-8') as fout:
            fout.write(content)

    def mkdir(self, path):
        """
        创建新目录
        """
        path = path.strip()
        isExists = os.path.exists(path)
        if not isExists:
            print('新建 {} 文件夹'.format(path))
            os.makedirs(path)
            return True
        else:
            print('文件夹{}已经存在'.format(path))
            return False

    def save_page_content(self, pn):
        """
        保存一页的MM的信息
        """
        contents = self.get_content(pn)
        for item in contents:
            print('获取模特: {item[2]}, 年龄: {item[3]}, 城市: {item[4]}'.format(item=item))
            user_html = self.get_detail_page('https:' + item[5])  # 个人详情页的内容
            if not user_html:
                print('获取MM-%s的信息为空' % item[2])
            else:
                imgs = self.get_all_img(user_html)  # 获取个人的所有图片
                if not self.mkdir(item[2]):  # 创建目录
                    continue
                self.save_logo(item[1], item[2])  # 保存头像
                self.save_all_img(imgs, item[2])

    def save_pages_content(self, start, end):
        """
        保存多页的MM的信息
        """
        for i in range(start, end + 1):
            print('++++++++开始保存第%d页MM的信息++++++++' % i)
            self.save_page_content(i)


mm = TaoBaoMM()
mm.save_pages_content(1, 10)


class NoneError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)
