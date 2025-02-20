import cv2
import easyocr
from PIL import Image
import numpy as np
import os
import requests
from bs4 import BeautifulSoup
import re
import time


def get_wins() -> str:
    ## vipc.txtから連勝数を取得する
    with open('vipc.txt',"r",encoding="utf-8") as f:
        wins_str = f.read()
    return int(wins_str[0])

def add_wins():
    # vipc.txtの連勝数に+1してまた書き込む
    wins = get_wins() + 1
    wins_str = str(wins) + "連勝"
    write_file('vipc.txt', wins_str)

def reset_wins():
    # 連勝数をリセットする
    wins_str = "0連勝"
    write_file('vipc.txt', wins_str)

def read_first_rate_from_image(frame, reader) -> str:
    # キャラ選択画面から戦闘力を取得する
    crop = frame[722:770, 1544:1797]
    rate_img = Image.fromarray(crop)
    result = reader.readtext(np.array(rate_img), detail=0)
    result = result[0]
    print(result)
    return remove_non_numbers(result)


def read_rate_from_image(frame, reader) -> str:
    # リザルト画面から戦闘力を取得する
    crop = frame[265:300, 667:854]
    rate_img = Image.fromarray(crop)
    result = reader.readtext(np.array(rate_img), detail=0)
    result = result[0]
    return remove_non_numbers(result)

def write_rate(rate: str):
    # rate.txtに戦闘力を書き込む
    return write_file('rate.txt', add_commas(rate))

def get_rate() -> str:
    # rate.txtから戦闘力を取得する
    return read_file('rate.txt')

def remove_non_numbers(rate: str) -> str:
    ## 数字以外を削除する
    return ''.join(filter(str.isdigit, rate))

def add_commas(rate: str) -> str:
    ## 数字をカンマ区切りにする
    rate = "{:,}".format(int(rate))
    return rate

def kumamate_get_rate(soup) -> dict:
    # クマメイトから戦闘力の辞書を作成
    kuma_dict = {}

    for i in range(27):

        if i == 0:
            continue

        for kuma_name in soup.find_all("td")[1+i*3]:

            if "VIP到達！" in kuma_name:
                kuma_name = "VIP到達！"

            kuma_dict[kuma_name] = 0

        for element in soup.find_all("td")[2+i*3]:

            result = int(re.sub(r"\D", "", str(element)))
            kuma_dict[kuma_name] = result
    
    return kuma_dict

def rate_comparison(rate, kuma_dict):
    # 現在の戦闘力とクマメイトの戦闘力を比較
    kuma_rate_list = list(kuma_dict.values())

    current_status = None
    next_status = None

    for i, kuma_rate in enumerate(kuma_rate_list):

        if kuma_rate < rate:
            current_kuma_name = [k for k, v in kuma_dict.items() if v == kuma_rate]
            next_kuma_name = [k for k, v in kuma_dict.items() if v == kuma_rate_list[i-1]]
            
            diff_rate = add_commas(int(kuma_rate_list[i-1]) - rate)
            current_status = "現在：" + str(*current_kuma_name)
            next_status = str(*next_kuma_name) + "まであと" + str(diff_rate)

            break
    
    return current_status, next_status

def write_status(current: str, next: str):
    # 現在の段位と次の段位をテキストファイルに保存
    write_file('current_status.txt', current)
    write_file('next_status.txt', next)

def calc_ssim(frame, image):
    # 画像の類似度をSSIMで計算
    SSIM_opencv, _ = cv2.quality.QualitySSIM_compute(frame, image)
    ssim = np.average(SSIM_opencv)
    return ssim

# ファイル名と変数を引数とし、その変数をファイルに保存する関数
def write_file(file_name: str, data) -> bool:
    read_data = read_file(file_name)
    if read_data == data:
        return False
    else:
        with open(file_name, 'w') as f:
            f.write(data)
        return True

# ファイル名を引数とし、そのファイルを読み込む関数
def read_file(file_name: str) -> str:
    with open(file_name, 'r', encoding="utf-8") as f:
        return f.read()


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__))) #実行ファイルのあるディレクトリに移動

    # クマメイトの情報を取得
    load_url = "https://kumamate.net/vip/"
    html = requests.get(load_url)
    soup = BeautifulSoup(html.content, "html.parser")

    # 時間設定:5分置き(絶対変更しないで)
    access_timeout_sec = 300
    start_time = int(time.time())

    # クマメイトの世界戦闘力辞書を取得
    kuma_dict = kumamate_get_rate(soup)

    # OCRエンジンの取得
    reader = easyocr.Reader(['ja', 'en']) # 文字の選択一回だけでいい

    cam_id = 0 # 自分の仮想カメラのデバイスID (大体0～3)
    cap = cv2.VideoCapture(cam_id)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920) # カメラ画像の横幅を1920に設定
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080) # カメラ画像の縦幅を1080に設定

    win_image = cv2.imread('win.png') # 自分が勝ったときのリザルト
    lose_image = cv2.imread('lose.png') #　自分が負けたときのリザルト

    win_is_counted: bool = False
    first_rate_is_counted: bool = False

    while True:
        ret, frame = cap.read()

        if access_timeout_sec <= int(time.time()) - start_time:
            kuma_dict = kumamate_get_rate(soup)
            # print(kuma_dict)
            start_time = int(time.time())

        # もしvipc.txtがなかったら作成
        if not os.path.exists('vipc.txt'):
            reset_wins()

        if not first_rate_is_counted: # キャラ選択画面で戦闘力を取得する
            try:
                first_rate = read_first_rate_from_image(frame, reader)
            except IndexError: # もしキャラ選択画面で戦闘力が取得できなかったら
                first_rate = remove_non_numbers(get_rate())
                if first_rate == "":
                    first_rate = 0
            print(True)
            current_status, next_status = rate_comparison(int(first_rate), kuma_dict)
            write_rate(first_rate)
            write_status(current_status, next_status)
            print(f'{get_wins()}連勝')
            print(get_rate())
            first_rate_is_counted = True
            
        win_frame = frame[14:194, 682:784] # キャプチャしているフレームをwin_imageと同じ領域に切り取る
        lose_frame = frame[39:189, 720:825] # キャプチャしているフレームをlose_imageと同じ領域に切り取る
        # frame[y:y, x:x]

        # 勝利後、敗北後のフレームが切り取れているか確認
        # cv2.imshow("win_frame", win_frame)
        # cv2.imshow("lose_frame", lose_frame)

        # 勝利後、敗北後のフレームを新しく保存
        # cv2.imwrite("win.png", win_frame)
        # cv2.imwrite("lose.png", lose_frame)

        win_match_rate = calc_ssim(win_frame, win_image)
        lose_match_rate = calc_ssim(lose_frame, lose_image)

        if win_match_rate > 0.6: # もしwin_imageとwin_frameの類似度が0.6以上だった場合
            if not win_is_counted:
                add_wins() # 連勝数+1
                print(f'{get_wins()}連勝')
                win_is_counted = True

            result = read_rate_from_image(frame, reader) # 戦闘力取得
            current_status, next_status = rate_comparison(int(result), kuma_dict) # 段位取得
            if write_rate(result):
                write_status(current_status, next_status)
                print(get_rate())
                print(current_status)
                print(next_status)

        elif lose_match_rate > 0.6: # もしlose_imageとlose_frameの類似度が0.6以上だった場合
            if not win_is_counted:
                reset_wins() # 連勝数=0
                print(f'{get_wins()}連勝')
                win_is_counted = True

            result = read_rate_from_image(frame, reader) # 戦闘力取得
            current_status, next_status = rate_comparison(int(result), kuma_dict)
            if write_rate(result):
                write_status(current_status, next_status)
                print(get_rate())
                print(current_status)
                print(next_status)

        else:
            win_is_counted = False

if __name__ == "__main__":
    main()