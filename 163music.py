# -*- coding:utf-8 -*-

import datetime
import os
import json
import requests
import time
from myapi import formatString, startDownload, saveJsonFile
import html


# url example
# https://music.163.com/#/playlist?id=2538430210
# http://music.163.com/api/playlist/detail?id=2403593442
# https://music.163.com/song/media/outer/url?id=1294889112.mp3
# https://music.163.com/api/song/media?id=863046037


# 网络头
netease_header = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Connection': 'keep-alive',
    'Host': 'music.163.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/68.0.3440.106 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest',
    'Cookie': 'appver=1.5.0.75771;',
    'Referer': 'https://music.163.com/',
}


# 时间戳格式转换
def stamp_to_time(stamp):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(float(str(stamp)[0:10]))) + '.' + str(stamp)[10:]


def getSongfromCd(disstid):
    # 获取歌单中歌曲数据
    res = requests.get('http://music.163.com/api/playlist/detail?id=' + str(disstid), headers=netease_header)
    music_list = res.json()['result']['tracks']
    cdname = formatString(res.json()['result']['name'])
    # 遍历获取歌单中每首歌的信息
    for song in music_list:
        music_publish_year = stamp_to_time(song['album']['publishTime'])[:4]  # 发行年份
        music_down_url = "https://music.163.com/song/media/outer/url?id=" + str(song['id']) + ".mp3"  # 歌曲下载地址
        # !!!!!重要!!!!! 用requests爬虫拒绝301/302页面的重定向而拿到Location(重定向页面URL)的方法
        # allow_redirects=False的意义为拒绝默认的301/302重定向从而可以通过r.headers[‘Location’]拿到重定向的URL。
        music_down_url_new = requests.get(music_down_url, headers=netease_header, allow_redirects=False).headers['Location']

        # 歌词下载地址
        music_lyric_url = "https://music.163.com/api/song/media?id=" + str(song['id'])
        res2 = requests.get(music_lyric_url, headers=netease_header)
        lyric_json = json.loads(res2.text)
        # 由于一部分歌曲是没有上传歌词，因此没有默认为空
        if 'lyric' in lyric_json.keys():
            lyric = html.unescape(lyric_json['lyric'])
        else:
            lyric = ""
        song_dict = dict(id=song['id'], name=formatString(song['name']), trackNumber=song['no'],
                         artist='&'.join([formatString(artist['name']) for artist in song['artists']]),
                         albumName=song['album']['name'], Company=song['album']['company'],
                         publishYear=music_publish_year, pic_url=song['album']['picUrl'],
                         lyric_url=music_lyric_url, down_url=music_down_url_new, lyric=lyric)
        resultList.append(song_dict)

    return cdname


def start(down_path, callbackfunc):
    print("%s: 数据获取中..." % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    result_name = callbackfunc
    print("%s: 获取完成." % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    file_path = down_path + result_name + '\\'
    if not os.path.isdir(file_path):
        os.makedirs(file_path)
    saveJsonFile(resultList, file_path + "result.json")

    print("%s: 开始下载..." % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    for item in resultList:
        startDownload(item, file_path, server='netease')
    print("%s: 下载完成." % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))


# 固定几大榜单
song_lists = {
    # "云音乐热歌榜": 3778678,
    # "云音乐新歌榜": 3779629,
    # "云音乐飙升榜": 19723756,
    # "网易原创歌曲榜": 2884035,
    # "抖音排行榜": 2250011882,
    # "云音乐韩语榜": 745956260,
    # "中国TOP排行榜（港台榜）": 112504,
    # "中国TOP排行榜（内地榜）": 64016,
    # "iTunes榜": 11641012,
    # "美国Billboard周榜": 60198,
    # "Eng~": 2268910083,     # 自己的歌单-位置
    # "MyGod!!": 2538430210,
    # "Ohhhhh~": 2146349057,
    # "Jan~": 2268867905,
    # "狭窄世界的少年喜欢的音乐": 448851414,
    # "民谣精选 愿你在这个孤独的世界不寂寞": 2516053542,
    # "新概念英语(全四册 课文朗读)": 102796148,
    "老友记（六人行）全10季": 102769145,
}

if __name__ == '__main__':
    downpath = 'D:\\music-down\\netease\\'
    for music in song_lists.keys():
        resultList = []
        start(downpath, getSongfromCd(song_lists.get(music)))

