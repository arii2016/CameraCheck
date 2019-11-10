# coding: UTF-8

import sys, os, time
import serial
from serial.tools import list_ports
import Tkinter
from PIL import Image, ImageTk
#from PIL import Image
import threading
from io import BytesIO

SERIAL_PORT = ""
DEF_IMG_W = 1600
DEF_IMG_H = 1200

def get_command(device):
    rx_buffer = ""
    timeout = time.time()
    while True:
        if (time.time() - timeout) > 5.0:
            return "NG"
        chars = device.read()
        if chars == ",":
            break
        rx_buffer += chars
    return rx_buffer

def get_line(device):
    rx_buffer = ""
    timeout = time.time()
    while True:
        if (time.time() - timeout) > 3.0:
            return "NG"
        chars = device.read()
        if chars == "\n":
            break
        rx_buffer += chars
    return rx_buffer

# 撮像
def capture():
    device = serial.Serial(SERIAL_PORT, 921600, timeout=1, writeTimeout=0.1)

    # コマンドモードに変更
    device.write(chr(0x13))

    # 再起動
    device.write("S01\n")
    strRet = get_line(device)
    if strRet != "OK":
        Lb_Judge.configure(text='reboot1失敗')
        return False

    timeout = time.time()
    while True:
        if (time.time() - timeout) > 5.0:
            Lb_Judge.configure(text='reboot2失敗')
            return False
        device.write(chr(0x16))
        chars = device.read()
        if chars == chr(0x06):
            device.flushInput()
            break

    # コマンドモードに変更
    device.write(chr(0x13))

    # カメラエラーチェック
    device.write("E01\n")
    strRet = get_line(device)
    if strRet == "NG":
        Lb_Judge.configure(text=u'初期化')
        return False

    num = 0
    while num < 1:
        # 撮像
        device.write("C01\n")
        strRet = get_command(device)
        if strRet == "NG":
            Lb_Judge.configure(text=u'撮影')
            return False

        iSize = int(strRet)
        iCnt = 0
        datas = ""
        while True:
            chars = device.read(30000)
            if len(chars) > 0:
                datas = datas + chars
                iCnt = iCnt + len(chars)
            if iSize <= iCnt:
                break

        try:
            img = Image.open(BytesIO(datas))
        except:
            Lb_Judge.configure(text=u'転送')
            return False

        num = num + 1

    device.close()

    img = img.resize((IMG_W, IMG_H))
    canvas.photo = ImageTk.PhotoImage(img)
    canvas.create_image(0, 0, image=canvas.photo, anchor=Tkinter.NW)

    return True

def f(event):
    Lb_Judge.configure(text='--', foreground='#000000', background='#eeeeee')
    canvas.delete("all")

    if capture() == True:
        Lb_Judge.configure(text='OK', foreground='#00ff00', background='#aaffcc')
    else:
        Lb_Judge.configure(foreground='#ff0000', background='#ffaacc')

    lock.release()


def key(event):
    if event.char != ' ':
        return
    if lock.acquire(False):
        th = threading.Thread(target=f, args=(event,))
        th.start()

# ポート番号を取得する##################################
if sys.platform == "linux" or sys.platform == "linux2":
    matched_ports = list_ports.grep("ttyUSB")
elif sys.platform == "darwin":
    matched_ports = list_ports.grep("cu.usbserial-")
for match_tuple in matched_ports:
    SERIAL_PORT = match_tuple[0]
    break
#####################################################

lock = threading.Lock()

root = Tkinter.Tk()
root.geometry("{0}x{1}+0+0".format(root.winfo_screenwidth(), root.winfo_screenheight()))
root.bind("<Key>", key)

Lb_Judge = Tkinter.Label(root, text='--', foreground='#000000', background='#eeeeee', height=5, font=("", 50))
Lb_Judge.pack(side='left', expand=True, fill="x")

IMG_W = root.winfo_screenwidth() / 4 * 3
IMG_H = int(round(DEF_IMG_H * IMG_W / DEF_IMG_W))

canvas = Tkinter.Canvas(bg = "black", width=IMG_W, height=IMG_H)
canvas.pack(side='right')

root.mainloop()



