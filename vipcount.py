import cv2
import pyocr
import pyocr.builders
from PIL import Image
import numpy as np
import os

def write_wins(wins: int):
    # vipc.txtに連勝数を書き込む
    with open('vipc.txt',"w",encoding="utf-8") as f:
        f.write("%s連勝" % wins)

def get_wins() -> str:
    ## vipc.txtから連勝数を取得する
    with open('vipc.txt',"r",encoding="utf-8") as f:
        return f.read()

def add_wins():
    # vipc.txtの連勝数に+1してまた書き込む
    s = get_wins()
    index = s.find('連勝')
    r = s[:index]
    wins = int(r) + 1
    write_wins(wins)

def reset_wins():
    # 連勝数をリセットする
    write_wins(0)

def read_first_rate_from_image(frame) -> str:
    # キャラ選択画面から戦闘力を取得する
    crop = frame[722:770, 1544:1797]
    rate_img = Image.fromarray(crop)
    return remove_non_numbers(tool.image_to_string(rate_img, lang="eng", builder=builder))

def read_rate_from_image(frame) -> str:
    # リザルト画面から戦闘力を取得する
    crop = frame[265:300, 667:854]
    rate_img = Image.fromarray(crop)
    return remove_non_numbers(tool.image_to_string(rate_img, lang="eng", builder=builder))

def write_rate(rate: str):
    # rate.txtに戦闘力を書き込む
    with open('rate.txt',"w",encoding="utf-8") as f:
        f.write(add_commas(rate))

def get_rate() -> str:
    ## rate.txtから戦闘力を取得する
    with open('rate.txt',"r",encoding="utf-8") as f:
        return f.read()

def remove_non_numbers(rate: str) -> str:
    ## 数字以外を削除する
    return ''.join(filter(str.isdigit, rate))

def add_commas(rate: str) -> str:
    ## 数字をカンマ区切りにする
    rate = "{:,}".format(int(rate))
    return rate


os.chdir(os.path.dirname(os.path.abspath(__file__))) #実行ファイルのあるディレクトリに移動

# OCRエンジンの取得
tools = pyocr.get_available_tools()
tool = tools[0]
builder = pyocr.builders.TextBuilder()

cam_id = 2 # 自分の仮想カメラのデバイスID (大体0～3)
cap = cv2.VideoCapture(cam_id)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920) # カメラ画像の横幅を1920に設定
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080) # カメラ画像の縦幅を1080に設定

win_image = cv2.imread('win.png') # 自分が勝ったときのリザルト
lose_image = cv2.imread('lose.png') #　自分が負けたときのリザルト

win_is_counted: bool = False
first_rate_is_counted: bool = False

while True:
    ret, frame = cap.read()

    # 読み込んでいるWebカメラを表示
    # cv2.imshow('video', frame)

    # 読み込んでいるwebカメラの縦横幅を表示
    # print('width:' + str(cap.get(cv2.CAP_PROP_FRAME_WIDTH)))
    # print('height:' + str(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))

    if not first_rate_is_counted: # キャラ選択画面で戦闘力を取得する
        first_rate = read_first_rate_from_image(frame)
        write_rate(first_rate)
        print(True)
        print(get_wins())
        print(get_rate())
        first_rate_is_counted = True
        
    win_frame = frame[14:194, 682:784] # キャプチャしているフレームをwin_imageと同じ領域に切り取る
    lose_frame = frame[39:189, 720:825] # キャプチャしているフレームをlose_imageと同じ領域に切り取る
    # frame[y:y, x:x]

    # win_frameとlose_frameを画像として保存。win_imageとlose_imageはこの2つのフレームから切り取った画像である。
    # cv2.imwrite('win_frame.png', win_frame)
    # cv2.imwrite('lose_frame.png', lose_frame)

    # imageとframeの一致率を表示
    # print('win:' + str(np.count_nonzero(win_image == win_frame) / win_image.size))
    # print('lose:' + str(np.count_nonzero(lose_image == lose_frame) / lose_image.size))

    if np.count_nonzero(win_image == win_frame) / win_image.size > 0.8: # もしwin_imageとwin_frameの一致率が0.8以上だった場合
        result = read_rate_from_image(frame)
        write_rate(result)
        print(add_commas(result))

        if not win_is_counted: # win_is_countedは一度連勝を＋1したらそれ以降そのリザルトではカウントしないようにするため
            add_wins()
            print(get_wins())
            win_is_counted = True

    elif np.count_nonzero(lose_image == lose_frame) / lose_image.size > 0.8: # もしlose_imageとlose_frameの一致率が0.8以上だった場合
        result = read_rate_from_image(frame)
        write_rate(result)
        print(add_commas(result))

        if not win_is_counted:
            reset_wins()
            print(get_wins())
            win_is_counted = True

    else:
        win_is_counted = False
