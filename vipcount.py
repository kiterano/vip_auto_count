import cv2
import pyocr
import pyocr.builders
from PIL import Image
import numpy as np
import os

def get_wins() -> str:
    ## vipc.txtから連勝数を取得する
    with open('vipc.txt',"r",encoding="utf-8") as f:
        return f.read()

def add_commas(rate: str) -> str:
    ## 数字をカンマ区切りにする
    rate = "{:,}".format(int(rate))
    return rate

def remove_non_numbers(rate: str) -> str:
    ## 数字以外を削除する
    return ''.join(filter(str.isdigit, rate))

def get_rate() -> str:
    ## rate.txtから戦闘力を取得する
    with open('rate.txt',"r",encoding="utf-8") as f:
        return f.read()

def read_rate_from_image(frame) -> str:
    crop = frame[265:300, 667:854]
    rate_img = Image.fromarray(crop)
    return remove_non_numbers(tool.image_to_string(rate_img, lang="eng", builder=builder))

def read_first_rate_from_image(frame) -> str:
    crop = frame[722:770, 1544:1797]
    rate_img = Image.fromarray(crop)
    return remove_non_numbers(tool.image_to_string(rate_img, lang="eng", builder=builder))

def write_wins(wins: int):
    with open('vipc.txt',"w",encoding="utf-8") as f:
        f.write("%s連勝" % wins)

def reset_wins():
    ## 連勝数をリセットする
    write_wins(0)

def write_rate(rate: str):
    with open('rate.txt',"w",encoding="utf-8") as f:
        f.write(add_commas(rate))

os.chdir(os.path.dirname(os.path.abspath(__file__))) #実行ファイルのあるディレクトリに移動
builder = pyocr.builders.TextBuilder()

# OCRエンジンの取得
tools = pyocr.get_available_tools()
tool = tools[0]

cam_id = 2 # 自分の仮想カメラのデバイスID 大体(0～3)
cap = cv2.VideoCapture(cam_id)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920) # カメラ画像の横幅を1920に設定
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080) # カメラ画像の縦幅を1080に設定

win_image = cv2.imread('win.png') # 自分が勝ったときのリザルト
lose_image = cv2.imread('lose.png') #　自分が負けたときのリザルト

print(cap.isOpened())

# if(os.path.exists('vipc.txt')): #もしテキストファイルが存在していれば、読み込んで現在の連勝数と戦闘力を表示
#     print(get_wins())
#     print(get_rate())

# else: #もしテキストファイルが存在しなければ、新しくテキストファイルを作り0連勝を書き込む
#     reset_wins()
#     print('0連勝')

print(get_wins())

win_is_counted: bool = False
first_rate_is_counted: bool = False

while True:
    ret, frame = cap.read()

    # cv2.imshow('video', frame)

    # print('width:' + str(cap.get(cv2.CAP_PROP_FRAME_WIDTH)))
    # print('height:' + str(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))

    if not first_rate_is_counted:
        first_rate = read_first_rate_from_image(frame)
        write_rate(first_rate)
        print(get_rate())
        first_rate_is_counted = True
        
    win_frame = frame[14:194, 682:784] # キャプチャしているフレームをwin_imageと同じ領域に切り取る
    lose_frame = frame[39:189, 720:825] # キャプチャしているフレームをlose_imageと同じ領域に切り取る
    # frame[y:y, x:x]

    # cv2.imwrite('win3.png', win_frame)
    # cv2.imwrite('lose3.png', lose_frame)

    # print('win:' + str(np.count_nonzero(win_image == win_frame) / win_image.size))
    # print('lose:' + str(np.count_nonzero(lose_image == lose_frame) / lose_image.size))

    if np.count_nonzero(win_image == win_frame) / win_image.size > 0.8: # もしwin_imageとwin_frameの一致率が0.8以上だった場合
        result = read_rate_from_image(frame)

        write_rate(result)
        print(add_commas(result))

        if not win_is_counted: # win_is_countedは一度連勝を＋1したらそれ以降そのリザルトではカウントしないようにするため

            s = get_wins()
            index = s.find('連勝')
            r = s[:index]
            wins = int(r) + 1
            write_wins(wins)
            print(wins, "連勝")

            win_is_counted = True

    elif np.count_nonzero(lose_image == lose_frame) / lose_image.size > 0.8: # もしlose_imageとlose_frameの一致率が0.8以上だった場合
        result = read_rate_from_image(frame)

        write_rate(result)
        print(add_commas(result))

        if not win_is_counted:
            reset_wins()
            print("0 連勝")
            win_is_counted = True

    else:
        win_is_counted = False
