import tempfile

import win32con
import win32com.client as comclt
from win32gui import GetDesktopWindow, GetWindowDC
from win32ui import CreateDCFromHandle, CreateBitmap
from win32api import GetSystemMetrics, SetCursorPos, mouse_event


def get_screenshot():
    hdesktop = GetDesktopWindow()
        
    width = GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
    height = GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
    left = GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
    top = GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)
        
    hdc = GetWindowDC(hdesktop)
    source_dc = CreateDCFromHandle(hdc)
    target_dc = source_dc.CreateCompatibleDC()

    bmp = CreateBitmap()
    bmp.CreateCompatibleBitmap(source_dc, width, height)

    target_dc.SelectObject(bmp)
    target_dc.BitBlt((0, 0), (width, height), source_dc, (left, top), win32con.SRCCOPY)

    tmp = tempfile.NamedTemporaryFile(suffix='.bmp')
    bmp.SaveBitmapFile(target_dc, tmp.name)
    return tmp            


def send_keyboard_event(letter):
    shell = comclt.Dispatch("WScript.Shell")
    shell.SendKeys(letter)


def send_mouse_event(x, y):
    SetCursorPos((x, y))
    mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, x, y, 0, 0)
    mouse_event(win32con.MOUSEEVENTF_LEFTUP, x, y, 0, 0)