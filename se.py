# -*- encoding:utf-8 -*-
import urllib
import urllib2
import re
import gzip
import StringIO
import time
import codecs
import random
from datetime import *
import tushare as ts
import pandas as pd


# 本地化股票列表
def get_stocks_list():
    df = ts.get_stock_basics()
    print df
    df.to_csv('stocks_list.dat')


# 访问目标URL
def request2url(url, header, data):
    request = urllib2.Request(url, headers=header, data=data)
    response = urllib2.urlopen(request)
    return response.read()


# 打开文件
def open_file(path):
    return codecs.open(path, 'w', encoding='utf-8')


# 写入文件
def write(f, line):
    f.write(line+'\n')


# 关闭文件
def close_file(f):
    f.close()


# 龙虎榜数据
def get_longhubang():
    today = datetime.today().strftime('%Y-%m-%d')
    longhubang_list = []
    url = 'http://www.szse.cn/main/disclosure/news/xxlb/'
    request = urllib2.Request(url)
    response = urllib2.urlopen(request)
    result = response.read().decode('gbk')
    pattern = re.compile(r'<td  align=\'center\'  >([\d]{6})?</td>')
    longhubang_list += set(pattern.findall(result))
    # 获取总页数
    pattern_pages = re.compile(ur'<td align="left" width="128px">.*\u7b2c(\d+)?.*\u5171(\d+)?\u9875.*</td>')
    # page_num = int(pattern_pages.findall(result)[0])
    pages_find = pattern_pages.findall(result)
    if len(pages_find[0]) == 2:
        current_page = int(pages_find[0][0])    # 当前页
        total_pages = int(pages_find[0][1])     # 总页数
        if current_page < total_pages:
            headers = {'Accept': '*/*', 'Accept-Encoding': 'gzip,deflate', 'Accept-Language': 'zh-CN,zh;q=0.8',
                       'Connection': 'keep-alive', 'Content-Length': '166',
                       'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                       'Host': 'www.szse.cn',
                       'Origin': 'http://www.szse.cn', 'Referer': 'http://www.szse.cn/main/disclosure/news/xxlb/',
                       'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36'}
            url = 'http://www.szse.cn/szseWeb/FrontController.szse'
            data = urllib.urlencode({'ACTIONID': '7', 'AJAX': 'AJAX-TRUE', 'CATALOGID': '1842_xxpl',
                                     'TABKEY': 'tab1', 'txtStart': today, 'txtEnd': today,
                                     'tab1PAGENO': '2', 'tab1PAGECOUNT': '2', 'tab1RECORDCOUNT': '37',
                                     'REPORT_ACTION': 'navigate'})
            request = urllib2.Request(url, headers=headers, data=data)
            response = urllib2.urlopen(request)
            result = response.read()
            longhubang_list += set(pattern.findall(result))
            # gzipper = gzip.GzipFile(fileobj=StringIO.StringIO(result))
            # result = gzipper.read()
            # print result
            print list(set(longhubang_list))
            print(u'共'+str(len(list(set(longhubang_list))))+u'只上榜')


# 获取上市公司公告
def get_announcement():
    date_now = datetime.today()
    time_now = int(datetime.today().strftime('%H'))
    if time_now >= 16:
        date_now = date_now + timedelta(1)
    url = 'http://disclosure.szse.cn/m/search0425.jsp'
    request = urllib2.Request(url)
    response = urllib2.urlopen(request)
    result = response.read().decode('gbk')
    p_total_pages = re.compile(ur'\u5171 <span>(\d+)</span> \u9875')
    # p_cur_page = re.compile(ur'\u5f53\u524d\u7b2c <span>(\d+)</span> \u9875')
    total_page = int(p_total_pages.findall(result)[0])  # 总页数
    # cur_page = int(p_cur_page.findall(result)[0])     # 当前页数
    print(total_page)
    headers = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
               'Accept-Encoding': 'gzip, deflate',
               'Accept-Language': 'zh-CN,zh;q=0.8',
               'Cache-Control': 'max-age=0',
               'Connection': 'keep-alive',
               # 'Content-Length': '104',
               'Content-Type': 'application/x-www-form-urlencoded',
               'Host': 'disclosure.szse.cn',
               'Origin': 'http://disclosure.szse.cn',
               'Referer': 'http://disclosure.szse.cn/m/search0425.jsp',
               'Upgrade-Insecure-Requests': '1',
               'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36'}
    f = open_file('announcement' + date_now.strftime('%Y%m%d_%H') + '.dat')
    i = 1
    while i <= total_page:
        print i
        # for i in range(1, total_page+1):
        data = urllib.urlencode({'leftid': '1',
                                 'lmid': 'drgg',
                                 'pageNo': str(i),
                                 'stockCode': '',
                                 'keyword': '',
                                 'noticeType': '',
                                 'startTime': date_now.strftime('%Y-%m-%d'),
                                 'endTime': date_now.strftime('%Y-%m-%d'),
                                 'tzy': ''})
        try:
            result = request2url(url, headers, data)
            result = result.decode('gbk')
            pattern = re.compile(r'target="new">(.*)</a>')
            for j in pattern.findall(result):
                write(f, j)
            i += 1
            time.sleep(round(random.uniform(2, 5), 2))
        except Exception as e:
            print(str(i)+' failed! Try again!')
            continue
    close_file(f)


def get_announcement_list():
    f = open('announcement20170824_08.dat', 'r')
    stocks_list = []
    for line in f.readlines():
        stocks_list.append(line.split('：')[0])
    print len(list(set(stocks_list)))


def get_announcement_2():
    url = 'http://disclosure.szse.cn//disclosure/fulltext/plate/szlatest_24h.js?ver=201708241718'
    headers = {'Accept': '*/*',
               'Accept-Encoding': 'gzip, deflate, sdch',
               'Accept-Language': 'zh-CN,zh;q=0.8',
               'Connection': 'keep-alive',
               'Host': 'disclosure.szse.cn',
               'Referer': 'http://disclosure.szse.cn/m/unit/drggxxpllist.html?s=%2Fdisclosure%2Ffulltext%2Fplate%2Fszlatest_24h.js',
               'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36'}
    data = urllib.urlencode({'ver': '201708241726'})
    result = request2url(url, headers, data)
    result = result.decode('gbk')
    print result

# get_announcement()
# get_longhubang()
# get_announcement_list()
# get_announcement_2()
get_stocks_list()