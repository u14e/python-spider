#!/usr/bin/env python3
# _*_ coding:utf-8 _*_

import re
from bs4 import BeautifulSoup
from urllib import parse


if __name__ == '__main__':
    html = """
        <div>
    <img src="hh" alt="">
    <img src="hh.jpg" alt="">
    <img alt="">
</div>
    """
    soup = BeautifulSoup(html, 'lxml')
    imgs = soup.find_all('img', src=re.compile(r'.\w{3,4}$'))
    print(imgs)