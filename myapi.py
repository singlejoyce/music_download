# -*- coding:utf-8 -*-
import datetime
import json
import os
import re
from logger import Logger
import requests
from mutagen.mp4 import MP4, MP4Cover
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB, TRCK, TCOP, TYER, TDRC, USLT
mylogger = Logger(logger='myapi').getlog()


def setSongInfo(song_path, music_info, lyr_path, pic_path, media_type):
    lyrics = open(lyr_path, encoding='utf-8').read().strip()
    # try to find the right encoding
    for enc in ('utf8', 'iso-8859-1', 'iso-8859-15', 'cp1252', 'cp1251', 'latin1'):
        try:
            lyrics = lyrics.decode(enc)
            print(enc, )
            break
        except:
            pass

    if media_type == 'mp3':
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
        # 插入歌词
        # remove old unsychronized lyrics
        if len(tags.getall(u"USLT::'en'")) != 0:
            mylogger.info("Removing Lyrics.")
            tags.delall(u"USLT::'en'")
            tags.save()

        # tags.add(USLT(encoding=3, lang=u'eng', desc=u'desc', text=lyrics))
        # apparently the description is important when more than one
        # USLT frames are present
        tags[u"USLT::'eng'"] = (USLT(encoding=3, lang=u'eng', desc=u'desc', text=lyrics))
        tags.save()

    elif media_type == 'm4a':
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
    else:
        mylogger.error("%s 类型不支持." % song_path)


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
        mylogger.error(" %s 文件已存在." % save_path)


# 格式化字符串，去掉非法字符
# 部分日文歌名及歌手包含特殊字符需要处理，否则无法正常下载
def formatString(string):
    return re.sub(r'[\\/:#*?"<>|\r\n]+', '', string)


# 中文写入json，但json文件中显示"\u6731\u5fb7\u57f9",不是中文。
# 解决方法：加入ensure_ascii = False
# 当目标json文件内容为空时，出现json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
# 解决方法：新增一个异常
def saveJsonFile(source, file_path):
    mylogger.info("json文件写入中...")
    try:
        with open(file_path, 'w', encoding='utf-8') as f_obj:
            json.dump(source, f_obj, ensure_ascii=False, indent=4)
    except json.decoder.JSONDecodeError:
        mylogger.error("json文件内容为空.")
    mylogger.info("json文件写入完成.")


def startDownload(music_info, down_path, server, header=None):
    song_down_path = down_path + "\\downmp3\\"
    if not os.path.isdir(song_down_path):
        os.makedirs(song_down_path)

    lyric_down_path = down_path + "\\downlyric\\"
    if not os.path.isdir(lyric_down_path):
        os.makedirs(lyric_down_path)

    pic_down_path = down_path + "\\downpic\\"
    if not os.path.isdir(pic_down_path):
        os.makedirs(pic_down_path)

    filename = '%s - %s' % (music_info['artist'], music_info['name'])
    lyric_save_path = lyric_down_path + filename + ".lrc"
    pic_save_path = pic_down_path + filename + ".jpg"

    if server == 'tencent':
        song_save_path = song_down_path + filename + ".m4a"
        mylogger.info(">>%s 开始下载..." % song_save_path)
        # qq音乐m4a：必须带headers，否则返回304错误
        # qq专辑图片：不需要带headers，否则返回404错误
        try:  # 下载音乐文件
            downloadFile(music_info['down_url'], song_save_path, header=header)
        except:
            mylogger.error(">>音乐文件下载失败.")

        try:  # 下载歌词
            downloadFile(music_info['lyric'], lyric_save_path, file_type='str')
        except:
            mylogger.error(">>lyric文件下载失败.")

        try:  # 下载专辑图片
            downloadFile(music_info['pic_url'], pic_save_path)
        except:
            mylogger.error(">>pic文件下载失败.")
        # 修改m4a相关信息
        if os.path.exists(song_save_path):
            try:
                setSongInfo(song_save_path, music_info, lyric_save_path, pic_save_path, media_type='m4a')
            except:
                mylogger.error(">>信息修改失败.")
        else:
            mylogger.erro(">>信息修改失败，音乐文件不存在.")

    elif server == 'netease':
        song_save_path = song_down_path + filename + ".mp3"

        # 网易音乐和专辑图片：不需要带headers
        # 网易歌词：必须带headers，否则返回304错误
        if ".mp3" in music_info['down_url']:
            mylogger.info(">>%s 开始下载..." % song_save_path)
            try:  # 下载mp3文件
                downloadFile(music_info['down_url'], song_save_path)
            except:
                mylogger.error(">>音乐文件下载失败")
            try:  # 下载专辑图片
                downloadFile(music_info['pic_url'], pic_save_path)
            except:
                mylogger.error(">>pic下载失败.")
            try:  # 下载歌词
                downloadFile(music_info['lyric'], lyric_save_path, file_type='str')
            except:
                mylogger.error(">>歌词下载失败.")
            # 修改mp3相关信息
            if os.path.exists(song_save_path):
                try:
                    setSongInfo(song_save_path, music_info, lyric_save_path, pic_save_path, media_type='mp3')
                except:
                    mylogger.error(">>信息修改失败." )
            else:
                mylogger.error(">>信息修改失败，音乐文件不存在.")
        else:
            mylogger.error(">> %s 的下载地址无效." % song_save_path)