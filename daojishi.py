from tkinter import *
from datetime import datetime
from tkinter.messagebox import *


class TestTime(object):
    def __init__(self, master=None):
        self.root = master
        self.root.geometry('200x200')
        self.root.resizable(width=False, height=False)
        self.updatetime()

    def updatetime(self):
        self.labelA = Label(self.root, text='当前本地时间为：\t\t')
        self.labelA.pack()
        self.labelB = Label(self.root, text="")
        self.labelB.pack()
        self.labelC = Label(self.root, text='\n距离中午吃饭还有：\t\t')
        self.labelC.pack()
        self.labelD = Label(self.root, text="")
        self.labelD.pack()
        self.labelE = Label(self.root, text='\n距离今天下班还有：\t\t')
        self.labelE.pack()
        self.labelF = Label(self.root, text="")
        self.labelF.pack()

        self.updateA()
        self.updateB()
        self.updateC()

    def updateA(self):
        self.now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.labelB.configure(text=self.now)
        self.root.after(1000, self.updateA)

    def updateB(self):
        # 获取当日日期，不包含时间，str
        self.nowday = datetime.now().strftime("%Y-%m-%d")
        # 字符串拼接，组成当日12点
        a = self.nowday + ' 12:00:00'
        self.newtime = datetime.strptime(a, "%Y-%m-%d %H:%M:%S")
        t = self.newtime - datetime.now()
        self.labelD.configure(text=t)
        self.root.after(1000, self.updateB)

    def updateC(self):
        # 获取当日日期，不包含时间，str
        self.nowday = datetime.now().strftime("%Y-%m-%d")
        # 字符串拼接，组成当日12点
        a = self.nowday + ' 18:00:00'
        self.newtime = datetime.strptime(a, "%Y-%m-%d %H:%M:%S")
        t = self.newtime - datetime.now()
        self.labelF.configure(text=t)
        self.root.after(1000, self.updateC)

    def updateD(self):
        self.nowTime = datetime.now().strftime("%H:%M:%S")
        if self.nowTime >= '11:00:00' and self.nowTime <= '11:30:00':
            showinfo(title='吃饭/喝水提醒', message='该吃饭了！！！！该喝水了！！！！')
        else:
            pass
        self.root.after(300000, self.updateD)  # 单位毫秒

if __name__ == '__main__':
    root = Tk()
    root.title('计时小界面')
    # 窗口置顶.
    root.wm_attributes('-topmost', 1)
    TestTime(root)
    root.mainloop()

