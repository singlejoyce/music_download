# -*- coding:utf-8 -*-

import datetime
import os
import json
import requests
import time
from myapi import formatString, startDownload, saveJsonFile
import html
from logger import Logger

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
    'Cookie': '_ntes_nnid=769c1ff9d5294ef308057f1a185e2c28,1577249142312; _ntes_nuid=769c1ff9d5294ef308057f1a185e2c28; WM_TID=uxyRWSrnyrpEUQREAAJt%2Bh6LKUBVWk0k; _iuqxldmzr_=32; ntes_kaola_ad=1; JSESSIONID-WYYY=Ja0moAH7i5j64I8IVthkrbsxeoe4K36BoNmnoVktMF%2FQ7ITgNOe7ldUOpB0WWgQs8tzho2h40miu9aJTBGUiPboFFn76hfKfS4Wcpi%2BA8jfnqAfdPhNJz6FUh2MVAWSfX9U4HZQ26fFi2KEYwYl%2BJ0BKYsnaba8HeTRvM%5CmmDibRqNXJ%3A1590632972384; WM_NI=6KWB1rzI7OwdnIVokMHMlbLyr6%2BurXLwrobbyfeNPIz2%2BTVqolm61YoxDtNiBNh%2B0TiOk4E8AeA9ADPljiLelP%2B3YMfXhaXL%2BKnA0EN2iszE3SSKKyBpBEydoLnHwWKgYzk%3D; WM_NIKE=9ca17ae2e6ffcda170e2e6eedaf6478fb7ac85b2448dbc8ea2c44b978f8faef1608cba99a6d16fa8908694b22af0fea7c3b92af69599a3b47aba97f9b0f670ae979a90ea478c93a483cf73b2eae596f15490a9be90e16abbbaabafd343baeee5b5d57badb4a3d7b453ada88c95cd638292a8ccb360ab91a5d5c83483bb8fdac45094b4a68acf6fb090e5d4dc47a688a882db48e995a2a2b34f8eeea794f94ff18d9dacca7382b08ea6fc70ad94a2a9f65d89b9979bea37e2a3; MUSIC_U=edd4f7453a44f3b6cacff1ec272675b38672ffefed2613720ee2aef326c85ee133a649814e309366; __remember_me=true; __csrf=a2016837a0b1be13b68d2963db3aa726',
    'Referer': 'https://music.163.com/',
}


# 时间戳格式转换
def stamp_to_time(stamp):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(float(str(stamp)[0:10]))) + '.' + str(stamp)[10:]


def get_lyric(songid):
    lyric_url = "https://music.163.com/api/song/media?id="
    # 歌词下载地址
    music_lyric_url = lyric_url + str(songid)
    res2 = requests.get(music_lyric_url, headers=netease_header)
    lyric_json = json.loads(res2.text)
    # 由于一部分歌曲是没有上传歌词，因此没有默认为空
    if 'lyric' in lyric_json.keys():
        lyric = html.unescape(lyric_json['lyric'])
    else:
        lyric = ""
    return lyric


def get_download_url(songid):
    down_url = "https://music.163.com/song/media/outer/url?id="
    music_down_url = down_url + str(songid) + ".mp3"  # 歌曲下载地址
    # !!!!!重要!!!!! 用requests爬虫拒绝301/302页面的重定向而拿到Location(重定向页面URL)的方法
    # allow_redirects=False的意义为拒绝默认的301/302重定向从而可以通过r.headers[‘Location’]拿到重定向的URL。
    music_down_url_new = requests.get(music_down_url, headers=netease_header, allow_redirects=False).headers[
            'Location']
    return music_down_url_new


def getSongfromCd(disstid):
    cd_url = 'http://music.163.com/api/playlist/detail?id='
    # 获取歌单中歌曲数据
    try:
        res = requests.get(cd_url + str(disstid), headers=netease_header)
        music_list = res.json()['result']['tracks']
        cdname = formatString(res.json()['result']['name'])
        # 遍历获取歌单中每首歌的信息
        mylogger.info(" getSongfromCd 开始爬虫...")
        for song in music_list:
            music_publish_year = stamp_to_time(song['album']['publishTime'])[:4]  # 发行年份
            music_down_url = get_download_url(song['id'])
            lyric = get_lyric(song['id'])
            song_dict = dict(id=song['id'], name=formatString (song['name']), trackNumber=song['no'],
                             artist='&'.join([formatString(artist['name']) for artist in song['artists']]),
                             albumName=song['album']['name'], publishYear=music_publish_year,
                             pic_url=song['album']['picUrl'], down_url=music_down_url, lyric=lyric)
            resultList.append(song_dict)
        mylogger.info(" getSongfromCd 爬虫完成.")
        return cdname
    except:
        mylogger.error(" getSongfromCd 爬虫异常...")


def search(keyword):
    # 获取搜索结果中歌曲信息
    params = {
        's': keyword,
        'type': 1,
        'limit': 50,
        'total': 'true',
    }

    url = "http://music.163.com/api/cloudsearch/pc?"
    res = requests.get(url=url, params=params, headers=netease_header)
    search_data = json.loads(res.text)['result']['songs']
    mylogger.info(" search 开始爬虫...")
    for data in search_data:
        music_publish_year = stamp_to_time(data['publishTime'])[:4]  # 发行年份
        music_down_url = get_download_url(data['id'])
        lyric = get_lyric(data['id'])
        song_info = dict(id=data['id'], name=formatString(data['name']), trackNumber=data['no'],
                         artist='&'.join([formatString(artist['name']) for artist in data['ar']]),
                         albumName=data['al']['name'], publishYear=music_publish_year,
                         pic_url=data['al']['picUrl'], down_url=music_down_url, lyric=lyric)
        resultList.append(song_info)
    mylogger.info(" search 爬虫完成.")
    return keyword


def start(down_path, callbackfunc):
    result_name = callbackfunc

    file_path = down_path + result_name + '\\'
    if not os.path.isdir(file_path):
        os.makedirs(file_path)
    saveJsonFile(resultList, file_path + "result.json")
    for item in resultList:
        startDownload(item, file_path, server='netease')
    resultList.clear()


# 固定几大榜单
cd_lists = {
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
    "Kor^^": 2645448750,
    "Jan~": 2268867905,
    "relax": 2309729918,
    # "狭窄世界的少年喜欢的音乐": 448851414,
    # "民谣精选 愿你在这个孤独的世界不寂寞": 2516053542,
    # "新概念英语(全四册 课文朗读)": 102796148,
    # "老友记（六人行）全10季": 102769145,
}


if __name__ == '__main__':
    mylogger = Logger(logger='netease').getlog()
    downpath = 'D:\\music-down\\netease\\'
    resultList = []
    # for music in cd_lists.keys():
    #     start(downpath, getSongfromCd(cd_lists.get(music)))
    start(downpath, search("薛之谦"))
    start(downpath, search("五月天"))
    # start(downpath, getSongfromCd(2645448750))
