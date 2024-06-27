import cv2

cam_id = 2 # 自分の仮想カメラのデバイスID (大体0～3)
cap = cv2.VideoCapture(cam_id)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920) # カメラ画像の横幅を1920に設定
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080) # カメラ画像の縦幅を1080に設定

while True:
    # 各フレームの画像を取得
    ret, frame = cap.read()

    # ここで何らかのエフェクトをかける

    # 画像を表示
    # 表示先を仮想Webカメラにしたい
    cv2.imshow("Window Name", frame)

    # 30フレーム表示して，Enterキーが入力されたら表示を終了する
    if cv2.waitKey(30) == 13:
        break

# 終了処理
cv2.destroyAllWindows()
cap.release()
