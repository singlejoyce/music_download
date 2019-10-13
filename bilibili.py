import json
import os
import sys
from datetime import datetime
import requests
import multiprocessing

from multiprocessing import Queue


class BilibiliCrawler:
    def __init__(self, qn=80, output=''):
        # 初始化

        if output:
            path = os.getcwd() + '\\'
            path += output
            if not os.path.exists(path):
                os.mkdir(path)
                output = path + '\\'
        self.output = output
        self.output_av = ''
        self.percent = 0.0
        self.resultList = []
        self.chunk_size = 1024
        self.qn = qn
        self.cid_url = 'https://api.bilibili.com/x/player/pagelist?aid={}&jsonp=jsonp'
        self.flv_url = 'https://api.bilibili.com/x/player/playurl?avid={}&cid={}&qn={}&type=&otype=json'
        self.headers1 = {
            'host': 'api.bilibili.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/70.0.3538.25 Safari/537.36 Core/1.70.3722.400 QQBrowser/10.5.3751.400',
            'Cookie': 'SESSDATA = 0da81169%2C1571985072%2Cae38dc91;',
        }
        self.headers2 = {
            'host': '',
            'Origin': 'https://www.bilibili.com',
            'Referer': 'https://www.bilibili.com/video/ac{}',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/70.0.3538.25 Safari/537.36 Core/1.70.3722.400 QQBrowser/10.5.3751.400',
            'Cookie': 'SESSDATA = 0da81169%2C1571985072%2Cae38dc91;',
        }

    def get_cid(self, url):
        # 获取AV中所有的p集信息
        try:
            print("%s: get_cid数据获取中..." % (datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            data = requests.get(url, headers=self.headers1).json()
            detail_list = data['data']
            for detail in detail_list:
                av_dict = dict(cid=detail['cid'], name=detail['part'], duration=detail['duration'], flv_down_url='')
                self.resultList.append(av_dict)
        except:
            print("pagelist 获取失败")

    def get_flv_down_url(self, av):
        # 得到对应的flv下载地址
        self.get_cid(self.cid_url.format(av))
        print("%s: av:%s get_flv_down_url数据获取中..." % (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), av))
        for i in range(len(self.resultList)):
            cid = self.resultList[i]['cid']
            duration = self.resultList[i]['duration']
            data = requests.get(self.flv_url.format(av, cid, self.qn), headers=self.headers1).json()
            durl = data['data']['durl'][0]
            self.resultList[i]['flv_down_url'] = durl['url']
            self.headers2['host'] = durl['url'].split('/')[2]
            minutes = int(duration / 60)
            seconds = int(duration - minutes * 60.0)
            self.resultList[i]['duration'] = '{}m{}s'.format(minutes, seconds)

    def show_progress(self, queue):
        while True:
            per = queue.get()
            if self.percent != per:
                # print('  [%s 下载进度]:%.1f%%' % (datetime.now().strftime("%Y%m%d %H:%M:%S"), per) + '\r')
                print(' [%s 下载进度]: %s' % (datetime.now().strftime("%Y%m%d %H:%M:%S"), per) + '%\r')
                self.percent = per

    def download(self, queue, url, filename='None.flv'):
        # 下载
        size = 0
        response = requests.get(url, headers=self.headers2, stream=True, verify=False)
        chunk_size = 1024
        content_size = int(response.headers['content-length'])
        if response.status_code == 200:
            sys.stdout.write(' [文件大小]:%0.2f MB\n' % (content_size / chunk_size / 1024))
            filename = os.path.join(self.output_av, filename)
            with open(filename, 'wb') as file:
                for data in response.iter_content(chunk_size=chunk_size):
                    file.write(data)
                    size += len(data)
                    file.flush()
                    # per = float('%.1f' % float(size / content_size * 100))
                    per = int(size / content_size * 100)
                    queue.put(per)
        else:
            print('%s 下载出错.' % datetime.now().strftime("%Y%m%d %H:%M:%S"))

    def startDownload(self, data):
        # 父进程创建my_queue，并传给各个子进程：
        my_queue = Queue()
        down_url = data['flv_down_url']
        if data['name'] != '':
            filename = data['name'].replace(' ', '_') + '.flv'
            p1 = multiprocessing.Process(target=self.download, args=(my_queue, down_url, filename))
        else:
            p1 = multiprocessing.Process(target=self.download, args=(my_queue, down_url))
        p2 = multiprocessing.Process(target=self.show_progress, args=(my_queue,))
        # 启动子进程p1，开始下载:
        p1.start()
        # 启动子进程p2，开始打印下载进度:
        p2.start()
        # 等待p1结束:
        p1.join()
        # p2进程里是死循环，无法等待其结束，只能强行终止:
        p2.terminate()

    # 中文写入json，但json文件中显示"\u6731\u5fb7\u57f9",不是中文。
    # 解决方法：加入ensure_ascii = False
    # 当目标json文件内容为空时，出现json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
    # 解决方法：新增一个异常
    def saveJsonFile(self, source, file_path):
        print("%s: json文件写入中..." % datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        try:
            with open(file_path, 'w', encoding='utf-8') as f_obj:
                json.dump(source, f_obj, ensure_ascii=False, indent=4)
        except json.decoder.JSONDecodeError:
            print("json文件内容为空.")
        print("%s: json文件写入完成." % datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    def start(self, av):
        # 开始
        self.resultList.clear()
        self.output_av = os.path.join(self.output, av)
        if not os.path.exists(self.output_av):
            os.mkdir(self.output_av)
        self.get_flv_down_url(av)
        self.saveJsonFile(self.resultList, self.output_av + "\\result.json")
        for data in self.resultList:
            self.startDownload(data)


if __name__ == '__main__':
    # avlist = ['39031994', '34904005']
    bilibili = BilibiliCrawler(qn=80, output="download")
    avlist = ['70945937', '70851464']
    for i in avlist:
        bilibili.start(av=i)
