import datetime
import os
import random
import re
import string
import urllib
import urllib.request
import urllib.response
from bs4 import BeautifulSoup
# import HTMLParser
# 在python3.X版本使用pip isntall HTMLParser后，发现引入失败，
# 提示：ModuleNotFoundError: No module named ‘markupbase’。
# 解决方法：
# 去网站下载，https://pypi.org/project/micropython-_markupbase/3.3.3-1/#files
# 将micropython-_markupbase-3.3.3-1.tar.gz中_markupbase.py解压到python目录下/Lib/site-packages下
# 重命名为markupbase.py即可
import html
import requests
import json
import time
from myapi import formatString, saveJsonFile, startDownload


# HTMLParser.unescape 方法在 Python3.4 就已经被废弃掉不推荐使用
# lyric = HTMLParser.HTMLParser().unescape()
def getLyric(music_info):
    url = 'https://c.y.qq.com/lyric/fcgi-bin/fcg_query_lyric.fcg'
    params = {
        'nobase64': 1,
        'musicid': music_info['songid'],  # 传入之前获取到的id
        'callback': 'jsonp1',
        'g_tk': '1134533366',
        'jsonpCallback': 'jsonp1',
        'loginUin': '0',
        'hostUin': '0',
        'format': 'jsonp',
        'inCharset': 'utf8',
        'outCharset': 'utf-8',
        'notice': '0',
        'platform': 'yqq',
        'needNewCode': '0'
    }
    header = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/59.0.3071.115 Safari/537.36',
        'referer': 'https://y.qq.com/n/yqq/song/{}.html'.format(music_info["songmid"])
    }
    res = requests.get(url=url, params=params, headers=header)
    lyric_json = json.loads(res.text.lstrip('jsonp1(').rstrip(')'))
    # 由于一部分歌曲是没有上传歌词，因此没有默认为空
    if 'lyric' in lyric_json.keys():
        # 对歌词内容做稍微清洗 去掉时间戳
        # dr1 = re.compile(r'&#\d.;', re.S)
        # dr2 = re.compile(r'\[\d+\]', re.S)
        # songdata['lyric'] = dr2.sub(r'\n', dr1.sub(r'', dd)).replace('\n\n', '\n')

        # 处理换行符号
        # s.replace('\r\n', '\\r\\n')
        # s.replace('\n', '\r\n')
        lyric = html.unescape(lyric_json['lyric'])
        return res.url, lyric
    else:
        return res.url, ""


def getDownUrl(music_info):
    url = 'https://c.y.qq.com/base/fcgi-bin/fcg_music_express_mobile3.fcg'
    guid = int(random.random() * 2147483647) * int(time.time() * 1000) % 10000000000
    filename = "C400" + str(music_info["songmid"]) + ".m4a"
    params = {
        'format': 'jsonp',
        'callback': 'getOneSongInfoCallback',
        'jsonpCallback': 'getOneSongInfoCallback',
        'cid': 205361747,
        'uin': 0,
        'songmid': music_info["songmid"],
        'filename': filename,
        'guid': guid,
        'g_tk': 5381,
        'loginUin': 0,
        'hostUin': 0,
        'notice': '0',
        'platform': 'yqq',
        'needNewCode': '0',
    }
    # 获取vkey
    res = requests.get(url=url, params=params)
    # res2.text = getOneSongInfoCallback({"code":0,"cid":205361747,"userip":"222.65.108.95",
    # "data":{"expiration":80400,"items":[{"subcode":0,"songmid":"004Z8Ihr0JIu5s",
    # "filename":"C400004Z8Ihr0JIu5s.m4a",
    # "vkey":"35E84A7EFC1D347A0148F5DCF7449EAB91B370F142E253CDC5AF32B0809D0FB050E13E0A9447E101587B177FDFE5E8E1A48BDCB1A598E271"}]}})
    vkey = json.loads(res.text.lstrip('getOneSongInfoCallback(').rstrip(')'))['data']['items'][0]['vkey']
    if vkey:
        down_url = 'http://dl.stream.qqmusic.qq.com/%s?vkey=%s&guid=%s&uin=0&fromtag=30' % (
            filename, vkey, guid)
        return down_url
    else:
        return ""


def getPicUrl(music_info):
    url = "https://y.gtimg.cn/music/photo_new/T002R300x300M000%s.jpg?max_age=2592000" % music_info["pic_id"]
    return url


def search(keyword):
    # 获取搜索结果中歌曲信息
    params = {
        'format': 'json',
        'p': 1,
        'n': 50,  # 数量
        'w': keyword,
        # 'aggr': 1,
        'lossless': 1,
        'cr': 1,
        'new_json': 1,
    }
    header = {
        'Host': 'c.y.qq.com',
        'Referer': 'https://y.qq.com/portal/search.html',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/58.0.3029.110 Safari/537.36 SE 2.X MetaSr 1.0',
    }
    url = "https://c.y.qq.com/soso/fcgi-bin/client_search_cp?"
    res = requests.get(url=url, params=params, headers=header)
    search_data = json.loads(res.text.strip('callback()[]'))['data']['song']['list']
    for data in search_data:
        song_info = dict(songid=data['id'],
                         songmid=data['mid'],
                         name=formatString(data['name']),
                         artist='&'.join([formatString(i['name']) for i in data['singer']]),
                         albumName=data['album']['title'],
                         pub_time='',
                         subtitle='',
                         company='',
                         genre='',
                         lan='',
                         pic_id=data['album']['mid'],
                         down_url='',
                         pic_url='',
                         lyric_url='',
                         lyric='')
        resultList.append(song_info)
    return keyword


def getAlbumList(keyword, jsonpath):
    # 16位随机数
    searchid = int(random.random() * 2147483647) * int(time.time() * 1000) % 10000000000000000
    # 获取搜索结果中专辑信息
    album_resultList = []
    params = {
        'ct': '24',
        'qqmusic_ver': '1298',
        'remoteplace': 'txt.yqq.album',
        'searchid': searchid,
        'aggr': '0',
        'catZhida': '1',
        'lossless': '0',
        'sem': '10',
        't': '8',
        'p': '1',
        'n': '30',
        'w': keyword,
        'g_tk': '5381',
        'jsonpCallback': 'MusicJsonCallback',
        'loginUin': '0',
        'hostUin': '0',
        'format': 'jsonp',
        'inCharset': 'utf8',
        'outCharset': 'utf-8',
        'notice': '0',
        'platform': 'yqq',
        'needNewCode': '0',
    }
    header = {
        'Host': 'c.y.qq.com',
        'Referer': 'https://y.qq.com/portal/search.html',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/58.0.3029.110 Safari/537.36 SE 2.X MetaSr 1.0',
    }
    url = "https://c.y.qq.com/soso/fcgi-bin/client_search_cp?"
    res = requests.get(url=url, params=params, headers=header)
    search_data = json.loads(res.text.lstrip('MusicJsonCallback(').rstrip(')'))['data']['album']['list']
    for data in search_data:
        album_info = dict(albumid=data['albumID'],
                          albummid=data['albumMID'],
                          artist='&'.join([formatString(i['name']) for i in data['singer_list']]),
                          albumName=data['albumName'],
                          pub_time=data['publicTime'],
                          pic_url=data['albumPic'])
        album_resultList.append(album_info)
    if not os.path.isdir(jsonpath):
        os.makedirs(jsonpath)
    saveJsonFile(album_resultList, jsonpath + keyword + "_album.json")


def getRankList(jsonpath):
    # 获取所有榜单title信息
    topList = []
    url = 'https://c.y.qq.com/v8/fcg-bin/fcg_v8_toplist_opt.fcg'
    params = {
        'page': 'index',
        'format': 'html',
        'tpl': 'macv4',
        'v8debug': '1',
        'jsonCallback': 'jsonCallback',
    }
    header = {
        'Host': 'c.y.qq.com',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/58.0.3029.110 Safari/537.36 SE 2.X MetaSr 1.0',
    }
    res = requests.get(url=url, params=params, headers=header)
    group = json.loads(res.text.lstrip(' jsonCallback(').rstrip(')'))
    for i in group:
        for j in i['List']:
            top_info = dict(ListName=j['ListName'], topID=j['topID'], update_key=j['update_key'])
            topList.append(top_info)

    if not os.path.isdir(jsonpath):
        os.makedirs(jsonpath)
    saveJsonFile(topList, jsonpath + "Rank.json")


def getSongfromRankList(name, topid, date):
    url = 'https://szc.y.qq.com/v8/fcg-bin/fcg_v8_toplist_cp.fcg'
    # 如果排行榜是按天统计，日期统计到昨天，格式为“2017-09-12”
    # 如果排行榜是按周统计，统计到上周的星期四，格式为“2017_36”,标示2017年的第36周
    # 具体怎么取，主要取“排行榜分类”接口返回的“update_key”字段值
    params = {
        'tpl': '3',
        'page': 'detail',
        'date': date,
        'topid': topid,
        'type': 'top',
        'song_begin': '0',
        'song_num': '100',
        'g_tk': '5381',
        'jsonpCallback': 'MusicJsonCallbacktoplist',
        'loginUin': '0',
        'hostUin': '0',
        'format': 'jsonp',
        'inCharset': 'utf8',
        'outCharset': 'utf-8',
        'notice': '0',
        'platform': 'yqq',
        'needNewCode': '0',
    }

    header = {
        'Host': 'szc.y.qq.com',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/58.0.3029.110 Safari/537.36 SE 2.X MetaSr 1.0',
        'referer': 'https://y.qq.com/n/yqq/toplist/{}.html'.format(topid)

    }
    res2 = requests.get(url=url, params=params, headers=header)
    songs = json.loads(res2.text.lstrip(' MusicJsonCallbacktoplist(').rstrip(')'))['songlist']
    for song in songs:
        song_info = dict(songid=song['data']['songid'],
                         songmid=song['data']['songmid'],
                         name=formatString(song['data']['songname']),
                         albumName=song['data']['albumname'],
                         artist='&'.join([formatString(singer['name']) for singer in song['data']['singer']]),
                         subtitle='',
                         company='',
                         genre='',
                         pub_time='',
                         lan='',
                         pic_id=song['data']['albummid'],
                         down_url='',
                         pic_url='',
                         lyric_url='',
                         lyric='')
        resultList.append(song_info)
    return name


def getSongfromPlaylist(disst_id):
    # 获取歌单中歌曲数据
    url = 'https://c.y.qq.com/qzone/fcg-bin/fcg_ucc_getcdinfo_byids_cp.fcg'
    header = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/59.0.3071.115 Safari/537.36',
        'referer': 'https://y.qq.com/n/yqq/playlist/{}.html'.format(disst_id)
    }
    params = {
        'type': '1',
        'json': '1',
        'utf8': '1',
        'onlysong': '0',
        'disstid': disst_id,
        'format': 'jsonp',
        'g_tk': '1089387893',
        'jsonpCallback': 'playlistinfoCallback',
        'loginUin': '857193777',
        'hostUin': '0',
        'inCharset': 'utf8',
        'outCharset': 'utf-8',
        'notice': 0,
        'platform': 'yqq',
        'needNewCode': 0
    }
    res = requests.get(url=url, params=params, headers=header)
    cdlist = json.loads(res.text.lstrip('playlistinfoCallback(').rstrip(')'))['cdlist']
    if len(cdlist) >= 1:
        cdlist = cdlist[0]
    cdname = formatString(cdlist['dissname'])
    for song in cdlist['songlist']:
        song_info = dict(songid=song['songid'],
                         songmid=song['songmid'],
                         name=formatString(song['songname']),
                         artist='&'.join([formatString(singer['name']) for singer in song['singer']]),
                         albumName=song['albumname'],
                         subtitle='',
                         company='',
                         genre='',
                         pub_time='',
                         lan='',
                         pic_id=song['albummid'],
                         down_url='',
                         pic_url='',
                         lyric_url='',
                         lyric='')
        resultList.append(song_info)
    return cdname


def getSongDetail(songid, songmid):
    # 获取歌曲详细信息，例如：发行公司，发行年月，流派等等
    url = 'https://u.y.qq.com/cgi-bin/musicu.fcg'
    header = {
        'Cookie': 'pgv_pvi=4843290624; pgv_si=s226910208; pgv_info=ssid=s7098549414; '
                  'ts_last=y.qq.com/n/yqq/playsquare/4533656999.html; pgv_pvid=658516924; ts_uid=926388995; '
                  'yqq_stat=0',
        'Host': 'u.y.qq.com',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/59.0.3071.115 Safari/537.36',
        'referer': 'https://y.qq.com/n/yqq/song/{}.html'.format(songmid)
    }
    data = '{"songinfo":{"method":"get_song_detail_yqq","param":{"song_type":0,"song_mid":"%s",' \
           '"song_id":%s},"module":"music.pf_song_detail_svr"}}' % (songmid, songid)

    # 16位随机数
    random_id = int(random.random() * 2147483647) * int(time.time() * 1000) % 10000000000000000
    callback = 'getUCGI' + str(random_id)
    params = {
        'callback': callback,
        'g_tk': '5381',
        'jsonpCallback': callback,
        'loginUin': '0',
        'hostUin': '0',
        'format': 'jsonp',
        'inCharset': 'utf8',
        'outCharset': 'utf-8',
        'notice': '0',
        'platform': 'yqq',
        'needNewCode': '0',
        'data': data,
    }
    res = requests.get(url=url, params=params, headers=header)
    time.sleep(3)
    details = json.loads(res.text.lstrip(callback + '(').rstrip(')'))['songinfo']['data']
    return details


def getSongfromAlbum(album_mid):
    url = 'https://c.y.qq.com/v8/fcg-bin/fcg_v8_album_info_cp.fcg'
    header = {
        'Host': 'c.y.qq.com',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/58.0.3029.110 Safari/537.36 SE 2.X MetaSr 1.0',
    }
    params = {
        'albummid': album_mid,
        'g_tk': '5381',
        'loginUin': '0',
        'hostUin': '0',
        'format': 'json',
        'inCharset': 'utf8',
        'outCharset': 'utf-8',
        'notice': '0',
        'platform': 'yqq',
        'needNewCode': '0',
    }
    res = requests.get(url=url, params=params, headers=header)
    album = json.loads(res.text)['data']
    for song in album['list']:
        song_info = dict(songid=song['songid'],
                         songmid=song['songmid'],
                         name=formatString(song['songname']),
                         artist='&'.join([formatString(singer['name']) for singer in song['singer']]),
                         albumName=song['albumname'],
                         subtitle='',
                         company='',
                         genre='',
                         pub_time='',
                         lan='',
                         pic_id=song['albummid'],
                         down_url='',
                         pic_url='',
                         lyric_url='',
                         lyric='')
        resultList.append(song_info)
    return album['name']


def start(down_path, callbackfunc):
    header = {
        'Host': 'dl.stream.qqmusic.qq.com',
        'Referer': 'http://y.qq.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/58.0.3029.110 Safari/537.36 SE 2.X MetaSr 1.0',
    }

    print("%s: 歌曲信息数据获取中..." % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    file_path = down_path + callbackfunc + '\\'
    # 补齐歌曲具体信息
    for i in range(len(resultList)):
        filename = '%s - %s' % (resultList[i]['artist'], resultList[i]['name'])
        print("%s: %s >>补充歌曲信息..." % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), filename))
        templist = getLyric(resultList[i])
        resultList[i]['lyric_url'] = templist[0]
        resultList[i]['lyric'] = templist[1]
        resultList[i]['down_url'] = getDownUrl(resultList[i])
        resultList[i]['pic_url'] = getPicUrl(resultList[i])
        # details = getSongDetail(resultList[i]['songid'], resultList[i]['songmid'])
        # resultList[i]['subtitle'] = details['track_info']['subtitle']
        # if 'company' in details['info'].keys():
        #     resultList[i]['company'] = details['info']['company']['content'][0]['value']
        # if 'pub_time' in details['info'].keys():
        #     resultList[i]['pub_time'] = details['info']['pub_time']['content'][0]['value']
        # if 'genre' in details['info'].keys():
        #     resultList[i]['genre'] = details['info']['genre']['content'][0]['value'].strip()
        # if 'lan' in details['info'].keys():
        #     resultList[i]['lan'] = details['info']['lan']['content'][0]['value']

        # 开始下载歌曲并修改歌曲属性信息
        startDownload(resultList[i], file_path, server='tencent', header=header)
    print("%s: All完成." % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    # 保存歌曲数据结果至json文件
    if not os.path.isdir(file_path):
        os.makedirs(file_path)
    saveJsonFile(resultList, file_path + "result.json")

    resultList.clear()


if __name__ == '__main__':
    downpath = 'D:\\music-down\\tencent\\'
    resultList = []
    # getRankList(downpath)
    # getAlbumList('梁静茹', downpath)
    # getAlbumList('陈奕迅', downpath)
    start(downpath, search('庄心妍'))
    # start(downpath, getSongfromPlaylist('3651099683'))
    # start(downpath, getSongfromRankList('巅峰榜·新歌', '27', '2018-12-18'))
    # start(downpath, getSongfromAlbum('0032ezFm3F53yO'))
