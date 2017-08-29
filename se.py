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
# @update: 8.29
# @param: start_date: 开始日期(%Y-%m-%d)
#           end_date: 结束日期(%Y-%m-%d)
# @return: 查询区间的所有上榜股票
def get_longhubang(start_date, end_date):
    longhubang_list = []
    url = 'http://www.szse.cn/szseWeb/FrontController.szse'
    headers = {'Accept': '*/*', 'Accept-Encoding': 'gzip, deflate', 'Accept-Language': 'zh-CN,zh;q=0.8',
               'Connection': 'keep-alive', 'Content-Length': '116',
               'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
               'Host': 'www.szse.cn',
               'Origin': 'http://www.szse.cn',
               'Referer': 'http://www.szse.cn/main/disclosure/news/xxlb/'}
    data = urllib.urlencode({'ACTIONID': '7', 'AJAX': 'AJAX-TRUE', 'CATALOGID': '1842_xxpl',
                             'TABKEY': 'tab1', 'txtStart': start_date, 'txtEnd': end_date,
                             'REPORT_ACTION': 'search'})
    request = urllib2.Request(url, headers=headers, data=data)
    response = urllib2.urlopen(request)
    result = response.read().decode('gbk')
    pattern_code = re.compile(r'<td  align=\'center\'  >([\d]{6})?</td>')
    longhubang_list += set(pattern_code.findall(result))
    # 获取总页数
    pattern_pages = re.compile(ur'<td align="left" width="128px">.*\u7b2c(\d+)?.*\u5171(\d+)?\u9875.*</td>')
    total_pages = int(pattern_pages.findall(result)[0][1])
    cur_page = 2
    headers['Content-Length'] = 166
    while cur_page <= total_pages:
        data = urllib.urlencode({'ACTIONID': '7', 'AJAX': 'AJAX-TRUE', 'CATALOGID': '1842_xxpl',
                                 'TABKEY': 'tab1', 'txtStart': start_date, 'txtEnd': end_date,
                                 'tab1PAGENO': str(cur_page), 'tab1PAGECOUNT': str(total_pages),
                                 'tab1RECORDCOUNT': '30', 'REPORT_ACTION': 'navigate'})
        request = urllib2.Request(url, headers=headers, data=data)
        response = urllib2.urlopen(request)
        result = response.read()
        longhubang_list += set(pattern_code.findall(result))
        cur_page += 1
    print list(set(longhubang_list))
    print(u'共'+str(len(list(set(longhubang_list))))+u'只上榜')


# 获取指定日期的上市公司公告
# @update: 8.29
# @param: start_date: 开始日期(%Y-%m-%d)
#           end_date: 结束日期(%Y-%m-%d)
# @return: 查询区间的所有公告信息
def get_announcement_range(start_date, end_date):
    url = 'http://disclosure.szse.cn/m/search0425.jsp'  # 目标URL
    p_title = re.compile(r'target="new">(.*)</a>')      # 匹配公告标题
    p_total_pages = re.compile(ur'\u5171 <span>(\d+)</span> \u9875')        # 匹配总页数
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
               'Upgrade-Insecure-Requests': '1'}    # 生成访问头
    f = open_file('announcement_' + start_date + '_' + end_date + '.dat')   # 打开目标文件
    cur_page = 1
    total_pages = None
    while cur_page <= total_pages or total_pages is None:   # 访问每一页
        data = urllib.urlencode({'leftid': '1',
                                 'lmid': 'drgg',
                                 'pageNo': str(cur_page),
                                 'startTime': start_date,
                                 'endTime': end_date})      # 生成请求数据
        try:
            result = request2url(url, headers, data)        # 访问目标页面
            result = result.decode('gbk')                   # 解码
            if total_pages is None:
                total_pages = int(p_total_pages.findall(result)[0])  # 获取总页数
                print total_pages
            for j in p_title.findall(result):               # 匹配公告标题
                write(f, j)
            print(str(cur_page)+' success!')
            cur_page += 1                                   # 更新访问页面
            time.sleep(round(random.uniform(2, 4), 2))      # 随机休眠若干秒
        except Exception as e:
            print(str(cur_page)+' failed! Try again!')
            continue
    close_file(f)


# 读取公告存储文件
def get_announcement_list(path):
    f = open(path, 'r')
    stocks_list = []
    for line in f.readlines():
        stocks_list.append(line.split('：')[0])
    print len(list(set(stocks_list)))


# 获取当前交易所网站上显示的所有上市公司公告
# @update: 8.29
# @return: 当前交易所网站上显示的所有上市公司公告信息
def get_announcement_all():
    today = datetime.now().strftime('%Y%m%d%H%M')   # 当前日期时间
    url = 'http://disclosure.szse.cn//disclosure/fulltext/plate/szlatest_24h.js?ver='+today     # 访问目标URL
    headers = {'Accept': '*/*',
               'Accept-Encoding': 'gzip, deflate, sdch',
               'Accept-Language': 'zh-CN,zh;q=0.8',
               'Connection': 'keep-alive',
               'Host': 'disclosure.szse.cn',
               'Referer': 'http://disclosure.szse.cn/m/unit/drggxxpllist.html? \
                          s=%2Fdisclosure%2Ffulltext%2Fplate%2Fszlatest_24h.js'}    # 生成访问头
    data = urllib.urlencode({'ver': today})             # 生成访问数据
    result = request2url(url, headers, data)            # 请求目标网页
    result = result.decode('gbk')                       # 转换编码
    pattern = re.compile(ur'\[(.*?)\]')                 # 匹配每条公告
    pattern_result = pattern.findall(result)            # 匹配结果
    f = open_file('announcement_' + today + '.dat')      # 新建文件
    for s in pattern_result:
        splits = s.split(',')                           # 切割公告信息
        info_code = splits[0].strip('[').strip('"')     # 分离股票代码
        info_title = splits[2].strip('"')               # 公告标题
        info_time = splits[-1].strip('"').strip(']')    # 公告时间戳
        line = info_code+' '+info_title+' '+info_time   # 拼接一条公告
        write(f, line)                                  # 写入文件
    close_file(f)

# get_announcement_range('2017-08-28', '2017-08-28')
# get_announcement_all()
get_longhubang('2017-08-25', '2017-08-25')
# get_announcement_list()
# get_stocks_list()

