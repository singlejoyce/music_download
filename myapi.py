# -*- coding:utf-8 -*-
import datetime
import json
import os
import re

import requests
from mutagen.mp4 import MP4, MP4Cover
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB, TRCK, TCOP, TYER, TDRC


def setSongInfo(song_path, music_info, pic_path, media_type):
    if media_type == 'm4a':
        tags = MP4(song_path).tags
        tags['\xa9nam'] = music_info['name']
        tags['\xa9alb'] = music_info['albumName']
        tags['\xa9ART'] = music_info['artist']
        tags['\xa9day'] = music_info['pub_time']
        tags['\xa9cmt'] = music_info['subtitle']
        tags['\xa9gen'] = music_info['genre']
        with open(pic_path, 'rb') as img:
            tags["covr"] = [MP4Cover(img.read(), imageformat=MP4Cover.FORMAT_JPEG)]
        tags.save(song_path)
    elif media_type == 'mp3':
        # 用eyed3库只支持英文歌名，对utf-8格式的文件无法修改；所以使用mutagen库替代修改mp3信息
        # 传入mp3、jpg的url路径以及其他字符串
        tags = ID3(song_path)
        tags.update_to_v23()  # 把可能存在的旧版本升级为2.3
        # 插入歌名
        tags['TIT2'] = TIT2(encoding=3, text=[music_info['name']])
        # 插入歌曲艺术家
        tags['TPE1'] = TPE1(encoding=3, text=[music_info['artist']])
        # 插入专辑名称
        tags['TALB'] = TALB(encoding=3, text=[music_info['albumName']])
        # 插入专辑公司
        # tags['TCOP'] = TCOP(encoding=3, text=[music_info['Company']])
        # 插入声道数
        tags['TRCK'] = TRCK(encoding=3, text=[music_info['trackNumber']])
        # 插入发行时间
        tags['TYER'] = TYER(encoding=3, text=[music_info['publishYear']])
        tags["TDRC"] = TDRC(encoding=3, text=music_info['publishYear'])
        # 插入专辑图片
        # response = urllib.request.urlopen(mp3_header_info['albumPicDownUrl'])
        # tags['APIC'] = APIC(encoding=3, mime='image/jpeg', type=3, desc=u'Cover', data=response.data)
        with open(pic_path, 'rb') as img:
            tags['APIC'] = APIC(encoding=3, mime='image/jpeg', type=3, desc=u'Cover', data=img.read())
        tags.save()
    else:
        print("%s: %s 类型不支持." % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), song_path))


# 下载接口
# 分2种类型处理：1、字符串 2、2进制数据
def downloadFile(source, save_path, file_type=None, header=None):
    if not os.path.exists(save_path):
        if file_type == 'str':
            with open(save_path, 'w', encoding='utf-8') as file:
                file.write(source)
        else:
            res = requests.get(source, headers=header)
            with open(save_path, 'wb') as file:
                for chunk in res.iter_content(chunk_size=128):
                    file.write(chunk)
    else:
        print("%s: %s 文件已存在." % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), save_path))


# 格式化字符串，去掉非法字符
# 部分日文歌名及歌手包含特殊字符需要处理，否则无法正常下载
def formatString(string):
    return re.sub(r'[\\/:#*?"<>|\r\n]+', '', string)


# 中文写入json，但json文件中显示"\u6731\u5fb7\u57f9",不是中文。
# 解决方法：加入ensure_ascii = False
# 当目标json文件内容为空时，出现json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
# 解决方法：新增一个异常
def saveJsonFile(source, file_path):
    print("%s: json文件写入中..." % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    try:
        with open(file_path, 'w', encoding='utf-8') as f_obj:
            json.dump(source, f_obj, ensure_ascii=False, indent=4)
    except json.decoder.JSONDecodeError:
        print("json文件内容为空.")
    print("%s: json文件写入完成." % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))


def startDownload(music_info, down_path, server, header=None):
    song_down_path = down_path + "\\downmp3\\"
    if not os.path.isdir(song_down_path):
        os.makedirs(song_down_path)

    pic_down_path = down_path + "\\downpic\\"
    if not os.path.isdir(pic_down_path):
        os.makedirs(pic_down_path)

    filename = '%s - %s' % (music_info['artist'], music_info['name'])
    lyric_save_path = song_down_path + filename + ".lrc"
    pic_save_path = pic_down_path + filename + ".jpg"

    print("%s: %s >>开始下载歌曲..." % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), filename))
    if server == 'tencent':
        song_save_path = song_down_path + filename + ".m4a"

        # qq音乐m4a：必须带headers，否则返回304错误
        # qq专辑图片：不需要带headers，否则返回404错误
        try:  # 下载音乐文件
            downloadFile(music_info['down_url'], song_save_path, header=header)
        except:
            print("%s: %s >>音乐文件下载失败." % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                          song_save_path))

        try:  # 下载歌词
            downloadFile(music_info['lyric'], lyric_save_path, file_type='str')
        except:
            print("%s: %s >>歌词下载失败." % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                        lyric_save_path))

        try:  # 下载专辑图片
            downloadFile(music_info['pic_url'], pic_save_path)
        except:
            print("%s: %s >>专辑图片下载失败." % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                          pic_save_path))
        # 修改m4a相关信息
        if os.path.exists(song_save_path):
            try:
                setSongInfo(song_save_path, music_info, pic_save_path, media_type='m4a')
            except:
                print("%s: %s >>信息修改失败." % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), song_save_path))
        else:
            print("%s: %s >>信息修改失败，音乐文件不存在." % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), song_save_path))

    elif server == 'netease':
        song_save_path = song_down_path + filename + ".mp3"

        # 网易音乐和专辑图片：不需要带headers
        # 网易歌词：必须带headers，否则返回304错误
        try:  # 下载mp3文件
            downloadFile(music_info['down_url'], song_save_path)
        except:
            print("%s: %s >>音乐文件下载失败. music_id=%s" % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                                      song_save_path, str(music_info['id'])))
        try:  # 下载专辑图片
            downloadFile(music_info['pic_url'], pic_save_path)
        except:
            print("%s: %s >>专辑图片下载失败. music_id=%s" % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                                      pic_save_path, str(music_info['id'])))
        try:  # 下载歌词
            downloadFile(music_info['lyric'], lyric_save_path, file_type='str')
        except:
            print("%s: %s >>歌词下载失败. music_id=%s" % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                                    lyric_save_path, str(music_info['id'])))
        # 修改mp3相关信息
        if os.path.exists(song_save_path):
            try:
                setSongInfo(song_save_path, music_info, pic_save_path, media_type='mp3')
            except:
                print("%s: %s >>信息修改失败." % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), song_save_path))
        else:
            print("%s: %s >>信息修改失败，音乐文件不存在." % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), song_save_path))
