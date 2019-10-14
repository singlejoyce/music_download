import tkinter
import time

star = time.time()


def gettime():
    elap = time.time() - star  # 获取时间差
    minutes = int(elap / 60)
    seconds = int(elap - minutes * 60.0)
    hseconds = int((elap - minutes * 60.0 - seconds) * 1000)
    var.set('%02d:%02d:%03d' % (minutes, seconds, hseconds))
    root.after(1, gettime)  # 每隔1ms调用函数自身获取时间


root = tkinter.Tk()
root.title('电子时钟')
var = tkinter.StringVar()
lb = tkinter.Label(root, textvariable=var, fg='blue', font=("微软雅黑", 100))  # 设置字体大小颜色
lb.pack()
gettime()
root.mainloop()
