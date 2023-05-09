import tkinter as tk
from tkinter import *
from tkinter import ttk
from tkinter import font
from tkinter import messagebox
from tkinter import filedialog
from mtcnn import MTCNN
from PIL import Image, ImageDraw, ImageFont
import PIL.Image, PIL.ImageTk
import configparser as conf
import subprocess as sub
import webbrowser as web
import datetime, time
import numpy as np
import sys, os
import schedule
import cv2

class Application(tk.Frame):
    def __init__(self,master, video_source=0):
        super().__init__(master)

        self.detector = MTCNN()

        self.master.geometry("700x700")
        self.master.iconbitmap("icon.ico")
        self.master.title("プロビデンスの目")
        self.master.resizable(width=False, height=False)

        self.font_frame = font.Font( family="Meiryo UI", size=15, weight="normal" )
        self.font_btn_big = font.Font( family="Meiryo UI", size=20, weight="bold" )
        self.font_btn_small = font.Font( family="Meiryo UI", size=15, weight="bold" )

        self.font_lbl_bigger = font.Font( family="Meiryo UI", size=45, weight="bold" )
        self.font_lbl_big = font.Font( family="Meiryo UI", size=30, weight="bold" )
        self.font_lbl_middle = font.Font( family="Meiryo UI", size=15, weight="bold" )
        self.font_lbl_small = font.Font( family="Meiryo UI", size=12, weight="normal" )

        self.camera = cv2.VideoCapture( video_source )
        self.width = self.camera.get( cv2.CAP_PROP_FRAME_WIDTH )    # カメラの横幅を取得
        self.height = self.camera.get( cv2.CAP_PROP_FRAME_HEIGHT )  # カメラの縦幅を取得

        #カメラ未接続の場合
        if self.camera.isOpened() is False:
            messagebox.showerror("エラー", "カメラが接続されていません")
            sys.exit()

        #初期設定読み込み
        self.read_setting()

        #画面作成
        self.create_widgets()
        self.create_menubar()

        #動かす部分
        self.delay = 15 #[mili seconds]
        self.update()

        #設定読み込み
    def read_setting(self):
        #configファイルの呼び出し
        self.config = conf.ConfigParser()
        self.config.read("config.ini")
        #書き出し
        try:
            self.dir = self.config["dir_path"]["dir"]
            self.phot_bool = eval(self.config["camera_function"]["camera_phot"])
            self.video_bool = eval(self.config["camera_function"]["camera_video"])
        except:
            messagebox.showerror("エラー", "設定ファイルが破損しています\n設定を初期化します\n後にアプリを起動しなおしてください")
            self.reset()
            sys.exit()

        #ファイルの設定
        ymd=datetime.datetime.now().strftime("%Y"+"-"+"%m"+"-"+"%d")# 日付とか
        hm=datetime.datetime.now().strftime("%H%M")                # 時間とか
        self.dir_path = self.dir + "/data_" + ymd# ファイル作成用パス
        os.makedirs(self.dir_path, exist_ok=True)                  # ファイルをいじることを許可
        video_path = os.path.join(self.dir_path, "video")          # ビデオ用パス
        self.pic_path = os.path.join(self.dir_path, "pic")         # 写真用パス

        # 動画ファイル保存用の設定
        fps = 15 #int(self.camera.get(cv2.CAP_PROP_FPS))           # カメラのFPSを取得
        fourcc = cv2.VideoWriter_fourcc("m", "p", "4", "v")        # 動画保存時のfourcc設定（mp4用）
        if self.video_bool:
            self.video = cv2.VideoWriter("{}_{}.{}".format(video_path, hm, "mp4"), fourcc, fps, (int(self.width), int(self.height)))  # 動画の仕様（ファイル名、fourcc, FPS, サイズ）
        self.move_cam = False                                      # 動的な動画の保存用bloom
        self.fgbg = cv2.createBackgroundSubtractorKNN()            # 背景オブジェクト
        self.moment = 0

        #自動撮影用定義
        def print_camera():
            _, frame = self.camera.read()
            cv2.imwrite("{}_{}.{}".format(self.pic_path, datetime.datetime.now().strftime("%Y"+"-"+"%m"+"-"+"%d"+" "+"%H"+""+"%M"+""+"%S"), "jpg"), frame)   #撮影

        #スケジュール
        schedule.every(2).seconds.do(print_camera)

        #メニューバー
    def create_menubar(self):

        # メニューバーの作成
        menu_bar = tk.Menu(self.master)

        # メニューバーに「ファイル」を作成
        menu_file = tk.Menu(self.master, tearoff=0)
        menu_bar.add_cascade(label="設定(S)", menu=menu_file)
        menu_help = tk.Menu(self.master, tearoff=0)
        menu_bar.add_cascade(label="ヘルプ(H)", menu=menu_help)

        # メニューバーの欄
        menu_file.add_command(label="環境設定", command=self.setting)
        menu_file.add_command(label="環境設定のリセット", command=self.reset_btn)
        menu_file.add_command(label="保存先を開く", command=self.open_folda)
        menu_file.add_command(label="アプリを閉じる", command=self.press_close_button)

        menu_help.add_command(label="FQAとか使い方", command=self.faq)
        menu_help.add_command(label="開発者Twitter", command=self.twitter)

        # メニューバーを画面にセット
        self.master.config(menu=menu_bar)
        
        #ディレクトリ指定でフォルダを開く
    def open_folda(self):
        table = str.maketrans("/","\"")
        sub.Popen(["explorer", r"{}".format(self.dir.translate(table))], shell=True)

        # フォルダ指定の関数
    def dir_click(self):
        dir = os.path.abspath(os.path.dirname(__file__))
        self.dir_path = filedialog.askdirectory(initialdir = dir)
        self.entry1.set(self.dir_path)

        #初期化ボタンのメッセージ
    def reset_btn(self):
            ret = messagebox.askyesno("リセット確認", "環境設定を初期化しますか？")
            if ret == True:
                self.reset()

        #設定の初期化
    def reset(self):
        self.config["dir_path"] = {
            "dir" : "photgrah"
        }
        self.config["camera_function"] = {
            "camera_phot" : False,
            "camera_video" : False
        }
        with open("config.ini", "w") as file:
            self.config.write(file)
        self.read_setting()

        #設定の保存
    def save(self):
        entry1_value = self.entry1.get()
        check1_bool = self.check1.get()
        check2_bool = self.check2.get()
        self.config["dir_path"] = {
            "dir" : entry1_value
        }
        self.config["camera_function"] = {
            "camera_phot" : check1_bool,
            "camera_video" : check2_bool
        }
        with open("config.ini", "w") as file:
            try:
                self.config.write(file)
            except UnicodeEncodeError as e:
                self.config["dir_path"] = {
                    "dir" : self.dir
                }
                with open("config.ini", "w") as file:
                    self.config.write(file)
                messagebox.showerror("エラー", "使用できない文字が含まれています")
            else:
                messagebox.showinfo("保存完了", "設定を保存しました")
        self.read_setting()

    def quit(self):
        self.setting_dlg.destroy()

        #設定画面
    def setting(self):
        self.setting_dlg = tk.Toplevel(self)
        self.setting_dlg.title("環境設定")
        self.setting_dlg.iconbitmap("icon.ico")
        self.setting_dlg.geometry("390x150")
        self.setting_dlg.resizable(width=False, height=False)

        frame=tk.LabelFrame(self.setting_dlg,text="フォルダ設定",foreground="black")
        frame.grid(row=0, column=0, padx=10, pady=0)

        # モーダルにする設定
        self.setting_dlg.grab_set()               # モーダルにする
        self.setting_dlg.focus_set()              # フォーカスを新しいウィンドウをへ移す
        self.setting_dlg.transient(self.master)   # タスクバーに表示しない

        # 「保存先参照」ラベルの作成
        dirLabel1 = ttk.Label(frame, text="保存先参照")
        dirLabel1.grid(row=0,column=0, padx=3, pady=3)

        # 「保存先参照」エントリーの作成
        self.entry1 = StringVar()
        self.entry1.set(self.dir)
        dirEntry1 = ttk.Entry(frame, textvariable=self.entry1, width=30)
        dirEntry1.grid(row=0,column=1, padx=3, pady=3)

        # 「保存先参照」ボタンの作成
        dirButton1 = ttk.Button(frame, text="参照", command=self.dir_click)
        dirButton1.grid(row=0,column=2, padx=3, pady=3)

        #チェックボタン作成
        self.check1 = BooleanVar()
        self.check1.set(self.phot_bool)
        checkbtn1 = ttk.Checkbutton(frame, variable=self.check1, text="写真撮影機能を使う")
        checkbtn1.grid(row=2, column=1, padx=10, pady=3)

        self.check2 = BooleanVar()
        self.check2.set(self.video_bool)
        checkbtn2 = ttk.Checkbutton(frame, variable=self.check2, text="映像撮影機能を使う")
        checkbtn2.grid(row=3, column=1, padx=10, pady=3)

        # ボタン作成
        button_frame = ttk.Frame(self.setting_dlg, padding=10)
        button_frame.grid(row=5,column=0,sticky=W)

        # 保存ボタンの設置
        savebtn = ttk.Button(button_frame, text="保存", command=self.save)
        savebtn.pack(fill = "x", padx=50, side = "left")

        # 閉じるボタンの設置
        cancel = ttk.Button(button_frame, text=("閉じる"), command=self.quit)
        cancel.pack(fill = "x", padx=50, side = "left")

        # ダイアログが閉じられるまで待つ
        self.master.wait_window(self.setting_dlg)

    def faq(self):
        sub.Popen(["start", r"readme.txt"], shell=True)
    
    def twitter(self):
        web.open("https://twitter.com/Miko_s4N")

        #GUI設定一覧
    def create_widgets(self):
        #映像用設定
        self.frame_cam = tk.LabelFrame(self.master, text = "映像", font=self.font_frame)
        self.frame_cam.place(x = 10, y = 10)
        self.frame_cam.configure(width = self.width+30, height = self.height+50)
        self.frame_cam.grid_propagate(0)

        #囲い
        self.canvas1 = tk.Canvas(self.frame_cam)
        self.canvas1.configure( width= self.width, height=self.height)
        self.canvas1.grid(column= 0, row=0,padx = 10, pady=10)

        #操作用一覧の囲い
        self.frame_btn = tk.LabelFrame( self.master, text="操作", font=self.font_frame )
        self.frame_btn.place( x=10, y=550 )
        self.frame_btn.configure( width=self.width + 30, height=120 )
        self.frame_btn.grid_propagate( 0 )

        #手動撮影用のボタン
        self.btn_snapshot = tk.Button( self.frame_btn, text="保存先を開く", font=self.font_btn_big)
        self.btn_snapshot.configure(width = 8, height = 1, command=self.open_folda)
        self.btn_snapshot.grid(column=0, row=0, padx=30, pady= 10)

        #手動撮影用のボタン
        self.btn_snapshot = tk.Button( self.frame_btn, text="手動撮影", font=self.font_btn_big)
        self.btn_snapshot.configure(width = 8, height = 1, command=self.snapshot_cam)
        self.btn_snapshot.grid(column=1, row=0, padx=30, pady= 10)

        #閉じるボタン
        self.btn_close = tk.Button( self.frame_btn, text="閉じる", font=self.font_btn_big )
        self.btn_close.configure( width=8, height=1, command=self.press_close_button )
        self.btn_close.grid( column=2, row=0, padx=30, pady=10 )

        #常に動かすループ部分
    def update(self):

        strdate=datetime.datetime.now().strftime("%Y"+"-"+"%m"+"-"+"%d"+" "+"%H"+":"+"%M"+":"+"%S")  #日付とかいろいろ
        _, frame = self.camera.read()

        frame_process = frame

        #画面上の日付表示
        cv2.putText(frame,text=strdate,
            org=(200, 25),
            fontFace=cv2.FONT_HERSHEY_SIMPLEX,
            fontScale=0.60,
            color=(255, 255, 255),
            thickness=2,
            lineType=cv2.LINE_4)

        video_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        if self.move_cam and self.video_bool:
            self.video.write(frame)                               # 動画を1フレームずつ保存する
            #撮影中表示(REC)
            cv2.putText(video_frame,text="REC",
            org=(600, 470),
            fontFace=cv2.FONT_HERSHEY_SIMPLEX,
            fontScale=0.50,
            color=(255, 0, 0),
            thickness=2,
            lineType=cv2.LINE_4)

        #動態検知

        if self.phot_bool or self.video_bool:
            fgmask = self.fgbg.apply(frame_process)                           # 前景領域のマスクを取得
            self.moment = cv2.countNonZero(fgmask)                         # 動体検知した画素数を取得

        if self.moment >= 10000:                                       # 動態検知の範囲(10000～15000がおすすめ範囲)
            self.move_cam = True

            # MTCNN顔検出
            # カメラのデータをmtcnnに読み込ませる変換工程
            image = cv2.cvtColor(frame_process, cv2.COLOR_BGR2RGB)
            mtcnn_datas = self.detector.detect_faces(image)
            if mtcnn_datas != [] and self.phot_bool:
                schedule.run_pending()
        else:
            self.move_cam = False

        #画面を更新し続ける処理
        self.photo = PIL.ImageTk.PhotoImage(image = PIL.Image.fromarray(video_frame))
        self.canvas1.create_image(0,0, image= self.photo, anchor = tk.NW)
        self.master.after(self.delay, self.update)

        #写真を手動で撮る処理
    def snapshot_cam(self):
        _, cam_frame = self.camera.read()
        cv2.imwrite("{}_{}.{}".format(self.pic_path, datetime.datetime.now().strftime("%Y"+"-"+"%m"+"-"+"%d"+"-"+"%H"+""+"%M"+""+"%S"), "jpg"), cam_frame)   #撮影

    def press_close_button(self):
        self.master.destroy()
        self.camera.release()

def main():
    root = tk.Tk()
    app = Application(master=root)
    app.mainloop()

if __name__ == "__main__":
    main()