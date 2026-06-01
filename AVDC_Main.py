#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import threading
import json
from PyQt5 import QtWidgets
from PyQt5.QtGui import QPixmap
from PyQt5.QtGui import QTextCursor, QCursor
from PyQt5.QtWidgets import QMainWindow, QTreeWidgetItem, QApplication
from PyQt5.QtCore import pyqtSignal, Qt
import sys
import time
import os.path
import requests
import shutil
import base64
import re
from aip import AipBodyAnalysis
from PIL import Image, ImageFilter
import os
from configparser import ConfigParser
from Ui.AVDC import Ui_AVDV
from Function.Function import save_config, movie_lists, get_info, getDataFromJSON, escapePath, getNumber, check_pic
from Function.getHtml import get_html, get_proxies, get_config


class MyMAinWindow(QMainWindow, Ui_AVDV):
    progressBarValue = pyqtSignal(int)  # 进度条信号量
    textSignal = pyqtSignal(str)  # 日志文本信号量
    labelInfoSignal = pyqtSignal(dict)  # 标签信息更新信号量
    
    def __init__(self, parent=None):
        super(MyMAinWindow, self).__init__(parent)
        self.Ui = Ui_AVDV()  # 实例化 Ui
        self.Ui.setupUi(self)  # 初始化Ui
        self.Init_Ui()
        self.set_style()
        # 初始化需要的变量
        self.version = '3.964'
        self.m_drag = False
        self.m_DragPosition = 0
        self.count_claw = 0  # 批量刮削次数
        self.item_succ = self.Ui.treeWidget_number.topLevelItem(0)
        self.item_fail = self.Ui.treeWidget_number.topLevelItem(1)
        self.select_file_path = ''
        self.json_array = {}
        self.scrape_results = []  # 存储刮削结果用于最终报告
        self.Init()
        self.Load_Config()
        self.show_version()
        # ========================================================================打开日志文件
        if self.Ui.radioButton_log_on.isChecked():
            if not os.path.exists('Log'):
                os.makedirs('Log')
            log_name = 'Log/' + time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime()) + '.txt'
            self.log_txt = open(log_name, "wb", buffering=0)
            self.add_text_main('[-]Created log file: ' + log_name)
            self.add_text_main("[*]======================================================")

    def Init_Ui(self):
        ico_path = ''
        if os.path.exists('AVDC-ico.png'):
            ico_path = 'AVDC-ico.png'
        elif os.path.exists('Img/AVDC-ico.png'):
            ico_path = 'Img/AVDC-ico.png'
        pix = QPixmap(ico_path)
        self.Ui.label_ico.setScaledContents(True)
        self.Ui.label_ico.setPixmap(pix)  # 添加图标
        self.Ui.progressBar_avdc.setValue(0)  # 进度条清0
        self.progressBarValue.connect(self.set_processbar)
        self.Ui.progressBar_avdc.setTextVisible(False)  # 不显示进度条文字
        self.setWindowFlag(Qt.FramelessWindowHint)  # 隐藏边框
        # self.setWindowOpacity(0.9)  # 设置窗口透明度
        self.setAttribute(Qt.WA_TranslucentBackground)  # 设置窗口背景透明
        self.Ui.treeWidget_number.expandAll()

    def set_style(self):
        # 控件美化
        self.Ui.widget_setting.setStyleSheet(
            '''
            QWidget#widget_setting{
                    background:#F0F8FF;
                    border-radius:20px;
                    padding:2px 4px;
            }
            QPushButton{
                    font-size:15px;
                    background:gray;
                    border:9px solid gray;
                    border-radius:15px;
                    padding:2px 4px;
            }
            
            ''')
        self.Ui.centralwidget.setStyleSheet(
            '''
            * {
                    font-size:15px;
            }            
            QWidget#centralwidget{
                    background:gray;
                    border:1px solid gray;
                    width:300px;
                    border-radius:20px;
                    padding:2px 4px;
            }            
            QTextBrowser{
                    border:1px solid gray;
                    background:white;
                    width:300px;
                    border-radius:10px;
                    padding:2px 4px;
            }
            QLineEdit{
                    background:white;
                    border:1px solid gray;
                    width:300px;
                    border-radius:10px;
                    padding:2px 4px;
            }            
            QTextBrowser#textBrowser_about{
                    background:white;
                    border:1px solid white;
                    width:300px;
                    border-radius:10px;
                    padding:2px 4px;
            }            
            QTextBrowser#textBrowser_warning{
                    background:gray;
                    border:1px solid gray;
                    width:300px;
                    border-radius:10px;
                    padding:2px 4px;
            }            
            QPushButton#pushButton_start_cap,#pushButton_move_mp4,#pushButton_select_file,#pushButton_select_thumb{
                    font-size:20px;
                    background:#F0F8FF;
                    border:2px solid white;
                    width:300px;
                    border-radius:20px;
                    padding:2px 4px;
            }
            QPushButton#pushButton_add_actor_pic,#pushButton_start_single_file{
                    font-size:20px;
                    background:#F0F8FF;
                    border:2px solid white;
                    width:300px;
                    border-radius:20px;
                    padding:2px 4px;
            }
            QPushButton#pushButton_save_config,#pushButton_show_pic_actor,#pushButton_init_config{
                    background:#F0F8FF;
                    border:2px solid white;
                    width:300px;
                    border-radius:13px;
                    padding:2px 4px;
            }
            QProgressBar::chunk{
                    background-color: #2196F3;
                    width: 5px; /*区块宽度*/
                    margin: 0.5px;
            }
            ''')

    # ========================================================================按钮点击事件
    def Init(self):
        self.Ui.stackedWidget.setCurrentIndex(0)
        self.Ui.treeWidget_number.clicked.connect(self.treeWidget_number_clicked)
        self.Ui.pushButton_close.clicked.connect(self.close_win)
        self.Ui.pushButton_min.clicked.connect(self.min_win)
        self.Ui.pushButton_main.clicked.connect(self.pushButton_main_clicked)
        self.Ui.pushButton_tool.clicked.connect(self.pushButton_tool_clicked)
        self.Ui.pushButton_setting.clicked.connect(self.pushButton_setting_clicked)
        self.Ui.pushButton_select_file.clicked.connect(self.pushButton_select_file_clicked)
        self.Ui.pushButton_about.clicked.connect(self.pushButton_about_clicked)
        self.Ui.pushButton_start_cap.clicked.connect(self.pushButton_start_cap_clicked)
        self.Ui.pushButton_save_config.clicked.connect(self.pushButton_save_config_clicked)
        self.Ui.pushButton_init_config.clicked.connect(self.pushButton_init_config_clicked)
        self.Ui.pushButton_move_mp4.clicked.connect(self.move_file)
        self.Ui.pushButton_add_actor_pic.clicked.connect(self.pushButton_add_actor_pic_clicked)
        self.Ui.pushButton_show_pic_actor.clicked.connect(self.pushButton_show_pic_actor_clicked)
        self.Ui.pushButton_select_thumb.clicked.connect(self.pushButton_select_thumb_clicked)
        self.Ui.pushButton_log.clicked.connect(self.pushButton_show_log_clicked)
        self.Ui.pushButton_start_single_file.clicked.connect(self.pushButton_start_single_file_clicked)
        self.Ui.checkBox_cover.stateChanged.connect(self.cover_change)
        self.Ui.horizontalSlider_timeout.valueChanged.connect(self.lcdNumber_timeout_change)
        self.Ui.horizontalSlider_retry.valueChanged.connect(self.lcdNumber_retry_change)
        self.Ui.horizontalSlider_mark_size.valueChanged.connect(self.lcdNumber_mark_size_change)
        # 连接日志信号到槽函数
        self.textSignal.connect(self._add_text_main_slot)
        # 连接标签信息信号到槽函数
        self.labelInfoSignal.connect(self._update_label_info_slot)

    # ========================================================================显示版本号
    def show_version(self):
        self.Ui.textBrowser_log_main.append('[*]======================== AVDC ========================')
        self.Ui.textBrowser_log_main.append('[*]                     Version ' + self.version)
        self.Ui.textBrowser_log_main.append('[*]======================================================')

    # ========================================================================鼠标拖动窗口
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.m_drag = True
            self.m_DragPosition = e.globalPos() - self.pos()
            self.setCursor(QCursor(Qt.OpenHandCursor))  # 按下左键改变鼠标指针样式为手掌

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.m_drag = False
            self.setCursor(QCursor(Qt.ArrowCursor))  # 释放左键改变鼠标指针样式为箭头

    def mouseMoveEvent(self, e):
        if Qt.LeftButton and self.m_drag:
            self.move(e.globalPos() - self.m_DragPosition)
            e.accept()

    # ========================================================================左侧按钮点击事件响应函数
    def close_win(self):
        os._exit(0)

    def min_win(self):
        self.setWindowState(Qt.WindowMinimized)

    def pushButton_main_clicked(self):
        self.Ui.stackedWidget.setCurrentIndex(0)

    def pushButton_tool_clicked(self):
        self.Ui.stackedWidget.setCurrentIndex(1)

    def pushButton_setting_clicked(self):
        self.Ui.stackedWidget.setCurrentIndex(2)

    def pushButton_about_clicked(self):
        self.Ui.stackedWidget.setCurrentIndex(3)

    def pushButton_show_log_clicked(self):
        self.Ui.stackedWidget.setCurrentIndex(4)

    def lcdNumber_timeout_change(self):
        timeout = self.Ui.horizontalSlider_timeout.value()
        self.Ui.lcdNumber_timeout.display(timeout)

    def lcdNumber_retry_change(self):
        retry = self.Ui.horizontalSlider_retry.value()
        self.Ui.lcdNumber_retry.display(retry)

    def lcdNumber_mark_size_change(self):
        mark_size = self.Ui.horizontalSlider_mark_size.value()
        self.Ui.lcdNumber_mark_size.display(mark_size)

    def cover_change(self):
        if not self.Ui.checkBox_cover.isChecked():
            self.Ui.label_poster.setText("封面图")
            self.Ui.label_thumb.setText("缩略图")

    def treeWidget_number_clicked(self, qmodeLindex):
        item = self.Ui.treeWidget_number.currentItem()
        if item.text(0) != '成功' and item.text(0) != '失败':
            try:
                index_json = str(item.text(0)).split('.')[0]
                self.add_label_info(self.json_array[str(index_json)])
            except:
                print(item.text(0) + ': No info!')

    def pushButton_start_cap_clicked(self):
        self.Ui.pushButton_start_cap.setEnabled(False)
        self.progressBarValue.emit(int(0))
        try:
            self.count_claw += 1
            t = threading.Thread(target=self.AVDC_Main)
            t.start()  # 启动线程,即让线程开始执行
        except Exception as error_info:
            self.add_text_main('[-]Error in pushButton_start_cap_clicked: ' + str(error_info))

    # ========================================================================恢复默认config.ini
    def pushButton_init_config_clicked(self):
        try:
            t = threading.Thread(target=self.init_config_clicked)
            t.start()  # 启动线程,即让线程开始执行
        except Exception as error_info:
            self.add_text_main('[-]Error in pushButton_save_config_clicked: ' + str(error_info))

    def init_config_clicked(self):
        json_config = {
            'show_poster': 1,
            'main_mode': 1,
            'soft_link': 0,
            'switch_debug': 1,
            'failed_file_move': 1,
            'update_check': 1,
            'save_log': 1,
            'website': 'all',
            'failed_output_folder': 'failed',
            'success_output_folder': 'JAV_output',
            'proxy': '',
            'timeout': 7,
            'retry': 3,
            'folder_name': 'actor/number-title-release',
            'naming_media': 'number-title',
            'naming_file': 'number',
            'literals': r'\()',
            'folders': 'failed,JAV_output',
            'string': '1080p,720p,22-sht.me,-HD',
            'emby_url': 'localhost:8096',
            'api_key': '',
            'media_path': 'E:/TEMP',
            'media_type': '.mp4|.avi|.rmvb|.wmv|.mov|.mkv|.flv|.ts|.webm|.MP4|.AVI|.RMVB|.WMV|.MOV|.MKV|.FLV|.TS|.WEBM',
            'sub_type': '.smi|.srt|.idx|.sub|.sup|.psb|.ssa|.ass|.txt|.usf|.xss|.ssf|.rt|.lrc|.sbv|.vtt|.ttml',
            'poster_mark': 1,
            'thumb_mark': 1,
            'mark_size': 3,
            'mark_type': 'SUB,LEAK,UNCENSORED',
            'mark_pos': 'top_left',
            'uncensored_poster': 0,
            'uncensored_prefix': 'S2M|BT|LAF|SMD',
            'nfo_download': 1,
            'poster_download': 1,
            'fanart_download': 1,
            'thumb_download': 1,
            'extrafanart_download': 0,
            'extrafanart_folder': 'extrafanart',
            'language_priority': 'sc,tc,ja',  # 默认简体中文优先
            'no_file_move': 0,  # 默认关闭仅刮削模式（0=正常移动文件，1=只刮削不移动）
        }
        save_config(json_config)
        self.Load_Config()

    # ========================================================================加载config
    def Load_Config(self):
        config_file = 'config.ini'
        config = ConfigParser()
        config.read(config_file, encoding='UTF-8')
        # ========================================================================common
        if int(config['common']['main_mode']) == 1:
            self.Ui.radioButton_common.setChecked(True)
        elif int(config['common']['main_mode']) == 2:
            self.Ui.radioButton_sort.setChecked(True)
        if int(config['common']['soft_link']) == 1:
            self.Ui.radioButton_soft_on.setChecked(True)
        elif int(config['common']['soft_link']) == 0:
            self.Ui.radioButton_soft_off.setChecked(True)
        if int(config['common']['failed_file_move']) == 1:
            self.Ui.radioButton_fail_move_on.setChecked(True)
        elif int(config['common']['failed_file_move']) == 0:
            self.Ui.radioButton_fail_move_off.setChecked(True)
        if int(config['common']['show_poster']) == 1:
            self.Ui.checkBox_cover.setChecked(True)
        elif int(config['common']['show_poster']) == 0:
            self.Ui.checkBox_cover.setChecked(False)
        if config['common']['website'] == 'all':
            self.Ui.comboBox_website_all.setCurrentIndex(0)
        elif config['common']['website'] == 'mgstage':
            self.Ui.comboBox_website_all.setCurrentIndex(1)
        elif config['common']['website'] == 'javbus':
            self.Ui.comboBox_website_all.setCurrentIndex(2)
        elif config['common']['website'] == 'jav321':
            self.Ui.comboBox_website_all.setCurrentIndex(3)
        elif config['common']['website'] == 'javdb':
            self.Ui.comboBox_website_all.setCurrentIndex(4)
        elif config['common']['website'] == 'avsox':
            self.Ui.comboBox_website_all.setCurrentIndex(5)
        elif config['common']['website'] == 'xcity':
            self.Ui.comboBox_website_all.setCurrentIndex(6)
        elif config['common']['website'] == 'dmm':
            self.Ui.comboBox_website_all.setCurrentIndex(7)
        self.Ui.lineEdit_success.setText(config['common']['success_output_folder'])
        self.Ui.lineEdit_fail.setText(config['common']['failed_output_folder'])
        # ========================================================================proxy
        if config['proxy']['type'] == 'no' or config['proxy']['type'] == '':
            self.Ui.radioButton_proxy_nouse.setChecked(True)
        elif config['proxy']['type'] == 'http':
            self.Ui.radioButton_proxy_http.setChecked(True)
        elif config['proxy']['type'] == 'socks5':
            self.Ui.radioButton_proxy_socks5.setChecked(True)
        self.Ui.lineEdit_proxy.setText(config['proxy']['proxy'])
        self.Ui.horizontalSlider_timeout.setValue(int(config['proxy']['timeout']))
        self.Ui.horizontalSlider_retry.setValue(int(config['proxy']['retry']))
        # ========================================================================Name_Rule
        self.Ui.lineEdit_dir_name.setText(config['Name_Rule']['folder_name'])
        self.Ui.lineEdit_media_name.setText(config['Name_Rule']['naming_media'])
        self.Ui.lineEdit_local_name.setText(config['Name_Rule']['naming_file'])
        # ========================================================================update
        if int(config['update']['update_check']) == 1:
            self.Ui.radioButton_update_on.setChecked(True)
        elif int(config['update']['update_check']) == 0:
            self.Ui.radioButton_update_off.setChecked(True)
        # ========================================================================log
        if int(config['log']['save_log']) == 1:
            self.Ui.radioButton_log_on.setChecked(True)
        elif int(config['log']['save_log']) == 0:
            self.Ui.radioButton_log_off.setChecked(True)
        # ========================================================================media
        self.Ui.lineEdit_movie_type.setText(config['media']['media_type'])
        self.Ui.lineEdit_sub_type.setText(config['media']['sub_type'])
        self.Ui.lineEdit_movie_path.setText(str(config['media']['media_path']).replace('\\', '/'))
        # ========================================================================escape
        self.Ui.lineEdit_escape_dir.setText(config['escape']['folders'])
        self.Ui.lineEdit_escape_char.setText(config['escape']['literals'])
        self.Ui.lineEdit_escape_dir_move.setText(config['escape']['folders'])
        self.Ui.lineEdit_escape_string.setText(config['escape']['string'])
        # ========================================================================debug_mode
        if int(config['debug_mode']['switch']) == 1:
            self.Ui.radioButton_debug_on.setChecked(True)
        elif int(config['debug_mode']['switch']) == 0:
            self.Ui.radioButton_debug_off.setChecked(True)
        # ========================================================================emby
        self.Ui.lineEdit_emby_url.setText(config['emby']['emby_url'])
        self.Ui.lineEdit_api_key.setText(config['emby']['api_key'])
        # ========================================================================mark
        if int(config['mark']['poster_mark']) == 1:
            self.Ui.radioButton_poster_mark_on.setChecked(True)
        elif int(config['mark']['poster_mark']) == 0:
            self.Ui.radioButton_poster_mark_off.setChecked(True)
        if int(config['mark']['thumb_mark']) == 1:
            self.Ui.radioButton_thumb_mark_on.setChecked(True)
        elif int(config['mark']['thumb_mark']) == 0:
            self.Ui.radioButton_thumb_mark_off.setChecked(True)
        self.Ui.horizontalSlider_mark_size.setValue(int(config['mark']['mark_size']))
        if 'SUB' in str(config['mark']['mark_type']).upper():
            self.Ui.checkBox_sub.setChecked(True)
        if 'LEAK' in str(config['mark']['mark_type']).upper():
            self.Ui.checkBox_leak.setChecked(True)
        if 'UNCENSORED' in str(config['mark']['mark_type']).upper():
            self.Ui.checkBox_uncensored.setChecked(True)
        if 'top_left' == config['mark']['mark_pos']:
            self.Ui.radioButton_top_left.setChecked(True)
        elif 'bottom_left' == config['mark']['mark_pos']:
            self.Ui.radioButton_bottom_left.setChecked(True)
        elif 'top_right' == config['mark']['mark_pos']:
            self.Ui.radioButton_top_right.setChecked(True)
        elif 'bottom_right' == config['mark']['mark_pos']:
            self.Ui.radioButton_bottom_right.setChecked(True)
        # ========================================================================uncensored
        if int(config['uncensored']['uncensored_poster']) == 1:
            self.Ui.radioButton_poster_cut.setChecked(True)
        elif int(config['uncensored']['uncensored_poster']) == 0:
            self.Ui.radioButton_poster_official.setChecked(True)
        self.Ui.lineEdit_uncensored_prefix.setText(config['uncensored']['uncensored_prefix'])
        # ========================================================================file_download
        if int(config['file_download']['nfo']) == 1:
            self.Ui.checkBox_download_nfo.setChecked(True)
        elif int(config['file_download']['nfo']) == 0:
            self.Ui.checkBox_download_nfo.setChecked(False)
        if int(config['file_download']['poster']) == 1:
            self.Ui.checkBox_download_poster.setChecked(True)
        elif int(config['file_download']['poster']) == 0:
            self.Ui.checkBox_download_poster.setChecked(False)
        if int(config['file_download']['fanart']) == 1:
            self.Ui.checkBox_download_fanart.setChecked(True)
        elif int(config['file_download']['fanart']) == 0:
            self.Ui.checkBox_download_fanart.setChecked(False)
        if int(config['file_download']['thumb']) == 1:
            self.Ui.checkBox_download_thumb.setChecked(True)
        elif int(config['file_download']['thumb']) == 0:
            self.Ui.checkBox_download_thumb.setChecked(False)
        # ========================================================================extrafanart
        if int(config['extrafanart']['extrafanart_download']) == 1:
            self.Ui.radioButton_extrafanart_download_on.setChecked(True)
        elif int(config['extrafanart']['extrafanart_download']) == 0:
            self.Ui.radioButton_extrafanart_download_off.setChecked(True)
        self.Ui.lineEdit_extrafanart_dir.setText(config['extrafanart']['extrafanart_folder'])

    # ========================================================================读取设置页设置，保存在config.ini
    def pushButton_save_config_clicked(self):
        try:
            t = threading.Thread(target=self.save_config_clicked)
            t.start()  # 启动线程,即让线程开始执行
        except Exception as error_info:
            self.add_text_main('[-]Error in pushButton_save_config_clicked: ' + str(error_info))

    def save_config_clicked(self):
        main_mode = 1
        failed_file_move = 1
        soft_link = 0
        show_poster = 0
        switch_debug = 0
        update_check = 0
        save_log = 0
        website = ''
        add_mark = 1
        mark_size = 3
        mark_type = ''
        mark_pos = ''
        uncensored_poster = 0
        nfo_download = 0
        poster_download = 0
        fanart_download = 0
        thumb_download = 0
        extrafanart_download = 0
        extrafanart_folder = ''
        proxy_type = ''
        # ========================================================================common
        if self.Ui.radioButton_common.isChecked():  # 普通模式
            main_mode = 1
        elif self.Ui.radioButton_sort.isChecked():  # 整理模式
            main_mode = 2
        if self.Ui.radioButton_soft_on.isChecked():  # 软链接开
            soft_link = 1
        elif self.Ui.radioButton_soft_off.isChecked():  # 软链接关
            soft_link = 0
        if self.Ui.radioButton_debug_on.isChecked():  # 调试模式开
            switch_debug = 1
        elif self.Ui.radioButton_debug_off.isChecked():  # 调试模式关
            switch_debug = 0
        if self.Ui.radioButton_update_on.isChecked():  # 检查更新
            update_check = 1
        elif self.Ui.radioButton_update_off.isChecked():  # 不检查更新
            update_check = 0
        if self.Ui.radioButton_log_on.isChecked():  # 开启日志
            save_log = 1
        elif self.Ui.radioButton_log_off.isChecked():  # 关闭日志
            save_log = 0
        if self.Ui.checkBox_cover.isChecked():  # 显示封面
            show_poster = 1
        else:  # 关闭封面
            show_poster = 0
        if self.Ui.radioButton_fail_move_on.isChecked():  # 失败移动开
            failed_file_move = 1
        elif self.Ui.radioButton_fail_move_off.isChecked():  # 失败移动关
            failed_file_move = 0
        if self.Ui.comboBox_website_all.currentText() == 'All websites':  # all
            website = 'all'
        elif self.Ui.comboBox_website_all.currentText() == 'mgstage':  # mgstage
            website = 'mgstage'
        elif self.Ui.comboBox_website_all.currentText() == 'javbus':  # javbus
            website = 'javbus'
        elif self.Ui.comboBox_website_all.currentText() == 'jav321':  # jav321
            website = 'jav321'
        elif self.Ui.comboBox_website_all.currentText() == 'javdb':  # javdb
            website = 'javdb'
        elif self.Ui.comboBox_website_all.currentText() == 'avsox':  # avsox
            website = 'avsox'
        elif self.Ui.comboBox_website_all.currentText() == 'xcity':  # xcity
            website = 'xcity'
        elif self.Ui.comboBox_website_all.currentText() == 'dmm':  # dmm
            website = 'dmm'
        # ========================================================================proxy
        if self.Ui.radioButton_proxy_http.isChecked():  # http proxy
            proxy_type = 'http'
        elif self.Ui.radioButton_proxy_socks5.isChecked():  # socks5 proxy
            proxy_type = 'socks5'
        elif self.Ui.radioButton_proxy_nouse.isChecked():  # nouse proxy
            proxy_type = 'no'
        # ========================================================================水印
        if self.Ui.radioButton_poster_mark_on.isChecked():  # 封面添加水印
            poster_mark = 1
        else:  # 关闭封面添加水印
            poster_mark = 0
        if self.Ui.radioButton_thumb_mark_on.isChecked():  # 缩略图添加水印
            thumb_mark = 1
        else:  # 关闭缩略图添加水印
            thumb_mark = 0
        if self.Ui.checkBox_sub.isChecked():  # 字幕
            mark_type += ',SUB'
        if self.Ui.checkBox_leak.isChecked():  # 流出
            mark_type += ',LEAK'
        if self.Ui.checkBox_uncensored.isChecked():  # 无码
            mark_type += ',UNCENSORED'
        if self.Ui.radioButton_top_left.isChecked():  # 左上
            mark_pos = 'top_left'
        elif self.Ui.radioButton_bottom_left.isChecked():  # 左下
            mark_pos = 'bottom_left'
        elif self.Ui.radioButton_top_right.isChecked():  # 右上
            mark_pos = 'top_right'
        elif self.Ui.radioButton_bottom_right.isChecked():  # 右下
            mark_pos = 'bottom_right'
        if self.Ui.radioButton_poster_official.isChecked():  # 官方
            uncensored_poster = 0
        elif self.Ui.radioButton_poster_cut.isChecked():  # 裁剪
            uncensored_poster = 1
        # ========================================================================下载文件，剧照
        if self.Ui.checkBox_download_nfo.isChecked():
            nfo_download = 1
        else:
            nfo_download = 0
        if self.Ui.checkBox_download_poster.isChecked():
            poster_download = 1
        else:
            poster_download = 0
        if self.Ui.checkBox_download_fanart.isChecked():
            fanart_download = 1
        else:
            fanart_download = 0
        if self.Ui.checkBox_download_thumb.isChecked():
            thumb_download = 1
        else:
            thumb_download = 0
        if self.Ui.radioButton_extrafanart_download_on.isChecked():  # 下载剧照
            extrafanart_download = 1
        else:  # 关闭封面
            extrafanart_download = 0
        
        # ========================================================================读取现有配置
        config_file = 'config.ini'
        config = ConfigParser()
        config.read(config_file, encoding='UTF-8')
        try:
            lang_priority = config['language']['priority']
        except:
            lang_priority = 'sc,tc,ja'  # 默认简体中文优先
        try:
            no_file_move = config['common']['no_file_move']
        except:
            no_file_move = '0'
        
        json_config = {
            'main_mode': main_mode,
            'soft_link': soft_link,
            'switch_debug': switch_debug,
            'show_poster': show_poster,
            'failed_file_move': failed_file_move,
            'update_check': update_check,
            'save_log': save_log,
            'website': website,
            'failed_output_folder': self.Ui.lineEdit_fail.text(),
            'success_output_folder': self.Ui.lineEdit_success.text(),
            'type': proxy_type,
            'proxy': self.Ui.lineEdit_proxy.text(),
            'timeout': self.Ui.horizontalSlider_timeout.value(),
            'retry': self.Ui.horizontalSlider_retry.value(),
            'folder_name': self.Ui.lineEdit_dir_name.text(),
            'naming_media': self.Ui.lineEdit_media_name.text(),
            'naming_file': self.Ui.lineEdit_local_name.text(),
            'literals': self.Ui.lineEdit_escape_char.text(),
            'folders': self.Ui.lineEdit_escape_dir.text(),
            'string': self.Ui.lineEdit_escape_string.text(),
            'emby_url': self.Ui.lineEdit_emby_url.text(),
            'api_key': self.Ui.lineEdit_api_key.text(),
            'media_path': self.Ui.lineEdit_movie_path.text(),
            'media_type': self.Ui.lineEdit_movie_type.text(),
            'sub_type': self.Ui.lineEdit_sub_type.text(),
            'poster_mark': poster_mark,
            'thumb_mark': thumb_mark,
            'mark_size': self.Ui.horizontalSlider_mark_size.value(),
            'mark_type': mark_type.strip(','),
            'mark_pos': mark_pos,
            'uncensored_poster': uncensored_poster,
            'uncensored_prefix': self.Ui.lineEdit_uncensored_prefix.text(),
            'nfo_download': nfo_download,
            'poster_download': poster_download,
            'fanart_download': fanart_download,
            'thumb_download': thumb_download,
            'extrafanart_download': extrafanart_download,
            'extrafanart_folder': self.Ui.lineEdit_extrafanart_dir.text(),
            'language_priority': lang_priority,
            'no_file_move': no_file_move,
        }
        save_config(json_config)

    # ========================================================================小工具-单视频刮削
    def pushButton_select_file_clicked(self):
        path = self.Ui.lineEdit_movie_path.text()
        filepath, filetype = QtWidgets.QFileDialog.getOpenFileName(self, "选取视频文件", path, "Movie Files(*.mp4 "
                                                                                         "*.avi *.rmvb *.wmv "
                                                                                         "*.mov *.mkv *.flv *.ts "
                                                                                         "*.webm *.MP4 *.AVI "
                                                                                         "*.RMVB *.WMV *.MOV "
                                                                                         "*.MKV *.FLV *.TS "
                                                                                         "*.WEBM);;All Files(*)")
        self.select_file_path = filepath

    def pushButton_start_single_file_clicked(self):
        if self.select_file_path != '':
            self.Ui.stackedWidget.setCurrentIndex(0)
            try:
                t = threading.Thread(target=self.select_file_thread)
                t.start()  # 启动线程,即让线程开始执行
            except Exception as error_info:
                self.add_text_main('[-]Error in pushButton_start_single_file_clicked: ' + str(error_info))

    def select_file_thread(self):
        file_name = self.select_file_path
        file_root = os.getcwd().replace("\\\\", "/").replace("\\", "/")
        file_path = file_name.replace(file_root, '.').replace("\\\\", "/").replace("\\", "/")
        # 获取去掉拓展名的文件名做为番号
        file_name = os.path.splitext(file_name.split('/')[-1])[0]
        mode = self.Ui.comboBox_website.currentIndex() + 1
        # 指定的网址
        appoint_url = self.Ui.lineEdit_appoint_url.text()
        appoint_number = self.Ui.lineEdit_movie_number.text()
        try:
            if appoint_number:
                file_name = appoint_number
            else:
                if '-CD' in file_name or '-cd' in file_name:
                    part = ''
                    if re.search(r'-CD\d+', file_name):
                        part = re.findall(r'-CD\d+', file_name)[0]
                    elif re.search(r'-cd\d+', file_name):
                        part = re.findall(r'-cd\d+', file_name)[0]
                    file_name = file_name.replace(part, '')
                if '-c.' in file_path or '-C.' in file_path:
                    file_name = file_name[0:-2]
            self.add_text_main("[!]Making Data for   [" + file_path + "], the number is [" + file_name + "]")
            self.Core_Main(file_path, file_name, mode, 0, appoint_url)
        except Exception as error_info:
            self.add_text_main('[-]Error in select_file_thread: ' + str(error_info))
        self.add_text_main("[*]======================================================")

    # ========================================================================小工具-裁剪封面图
    def pushButton_select_thumb_clicked(self):
        path = self.Ui.lineEdit_movie_path.text()
        filePath, fileType = QtWidgets.QFileDialog.getOpenFileName(self, "选取缩略图", path,
                                                                   "Picture Files(*.jpg);;All Files(*)")
        if filePath != '':
            self.Ui.stackedWidget.setCurrentIndex(0)
            try:
                t = threading.Thread(target=self.select_thumb_thread, args=(filePath,))
                t.start()  # 启动线程,即让线程开始执行
            except Exception as error_info:
                self.add_text_main('[-]Error in pushButton_select_thumb_clicked: ' + str(error_info))

    def select_thumb_thread(self, file_path):
        file_name = file_path.split('/')[-1]
        file_path = file_path.replace('/' + file_name, '')
        self.image_cut(file_path, file_name, 2)
        self.add_text_main("[*]======================================================")

    def image_cut(self, path, file_name, mode=1):
        png_name = file_name.replace('-thumb.jpg', '-poster.jpg')
        file_path = os.path.join(path, file_name)
        png_path = os.path.join(path, png_name)
        try:
            if os.path.exists(png_path):
                os.remove(png_path)
        except Exception as error_info:
            self.add_text_main('[-]Error in image_cut: ' + str(error_info))
            return

        """ 你的 APPID AK SK """
        APP_ID = '17013175'
        API_KEY = 'IQs1mkG4FerdtmNh6qKDI4fW'
        SECRET_KEY = 'dLr9GTqqutqP9nWKKRaEinVDhxYlPbnD'

        client = AipBodyAnalysis(APP_ID, API_KEY, SECRET_KEY)

        """ 获取图片分辨率 """
        im = Image.open(file_path)  # 返回一个Image对象
        width, height = im.size

        """ 读取图片 """
        with open(file_path, 'rb') as fp:
            image = fp.read()
        ex, ey, ew, eh = 0, 0, 0, 0
        """ 获取裁剪区域 """
        if height / width <= 1.5:  # 长宽比大于1.5，太宽
            """ 调用人体检测与属性识别 """
            result = client.bodyAnalysis(image)
            ewidth = int(height / 1.5)
            ex = int(result["person_info"][0]['body_parts']['nose']['x'])
            if width - ex < ewidth / 2:
                ex = width - ewidth
            else:
                ex -= int(ewidth / 2)
            if ex < 0:
                ex = 0
            ey = 0
            eh = height
            if ewidth > width:
                ew = width
            else:
                ew = ewidth
        elif height / width > 1.5:  # 长宽比小于1.5，太窄
            ex = 0
            ey = 0
            ew = int(width)
            eh = ew * 1.5
        fp = open(file_path, 'rb')
        img = Image.open(fp)
        img_new_png = img.crop((ex, ey, ew + ex, eh + ey))
        fp.close()
        img_new_png.save(png_path)
        self.add_text_main('[+]Poster Cut         ' + png_name + ' from ' + file_name + '!')
        if mode == 2:
            pix = QPixmap(file_path)
            self.Ui.label_thumb.setScaledContents(True)
            self.Ui.label_thumb.setPixmap(pix)  # 添加图标
            pix = QPixmap(png_path)
            self.Ui.label_poster.setScaledContents(True)
            self.Ui.label_poster.setPixmap(pix)  # 添加图标

    # ========================================================================小工具-视频移动
    def move_file(self):
        self.Ui.stackedWidget.setCurrentIndex(4)
        try:
            t = threading.Thread(target=self.move_file_thread)
            t.start()  # 启动线程,即让线程开始执行
        except Exception as error_info:
            self.add_text_main('[-]Error in move_file: ' + str(error_info))

    def move_file_thread(self):
        escape_dir = self.Ui.lineEdit_escape_dir_move.text()
        sub_type = self.Ui.lineEdit_sub_type.text().split('|')
        movie_path = self.Ui.lineEdit_movie_path.text()
        movie_type = self.Ui.lineEdit_movie_type.text()
        movie_list = movie_lists(escape_dir, movie_type, movie_path)
        des_path = movie_path + '/Movie_moved'
        if not os.path.exists(des_path):
            self.add_text_main('[+]Created folder Movie_moved!')
            os.makedirs(des_path)
        self.add_text_main('[+]Move Movies Start!')
        for movie in movie_list:
            if des_path in movie:
                continue
            sour = movie
            des = des_path + '/' + sour.split('/')[-1]
            try:
                shutil.move(sour, des)
                self.add_text_main('   [+]Move ' + sour.split('/')[-1] + ' to Movie_moved Success!')
                path_old = sour.replace(sour.split('/')[-1], '')
                filename = sour.split('/')[-1].split('.')[0]
                for sub in sub_type:
                    if os.path.exists(path_old + '/' + filename + sub):  # 字幕移动
                        shutil.move(path_old + '/' + filename + sub, des_path + '/' + filename + sub)
                        self.add_text_main('   [+]Sub moved! ' + filename + sub)
            except Exception as error_info:
                self.add_text_main('[-]Error in move_file_thread: ' + str(error_info))
        self.add_text_main("[+]Move Movies All Finished!!!")
        self.add_text_main("[*]======================================================")

    # ========================================================================小工具-emby女优头像
    def pushButton_add_actor_pic_clicked(self):  # 添加头像按钮响应
        self.Ui.stackedWidget.setCurrentIndex(4)
        emby_url = self.Ui.lineEdit_emby_url.text()
        api_key = self.Ui.lineEdit_api_key.text()
        if emby_url == '':
            self.add_text_main('[-]The emby_url is empty!')
            self.add_text_main("[*]======================================================")
            return
        elif api_key == '':
            self.add_text_main('[-]The api_key is empty!')
            self.add_text_main("[*]======================================================")
            return
        try:
            t = threading.Thread(target=self.found_profile_picture, args=(1,))
            t.start()  # 启动线程,即让线程开始执行
        except Exception as error_info:
            self.add_text_main('[-]Error in pushButton_add_actor_pic_clicked: ' + str(error_info))

    def pushButton_show_pic_actor_clicked(self):  # 查看按钮响应
        self.Ui.stackedWidget.setCurrentIndex(4)
        emby_url = self.Ui.lineEdit_emby_url.text()
        api_key = self.Ui.lineEdit_api_key.text()
        if emby_url == '':
            self.add_text_main('[-]The emby_url is empty!')
            self.add_text_main("[*]======================================================")
            return
        elif api_key == '':
            self.add_text_main('[-]The api_key is empty!')
            self.add_text_main("[*]======================================================")
            return
        if self.Ui.comboBox_pic_actor.currentIndex() == 0:  # 可添加头像的女优
            try:
                t = threading.Thread(target=self.found_profile_picture, args=(2,))
                t.start()  # 启动线程,即让线程开始执行
            except Exception as error_info:
                self.add_text_main('[-]Error in pushButton_show_pic_actor_clicked: ' + str(error_info))
        else:
            try:
                t = threading.Thread(target=self.show_actor, args=(self.Ui.comboBox_pic_actor.currentIndex(),))
                t.start()  # 启动线程,即让线程开始执行
            except Exception as error_info:
                self.add_text_main('[-]Error in pushButton_show_pic_actor_clicked: ' + str(error_info))

    def show_actor(self, mode):  # 按模式显示相应列表
        if mode == 1:  # 没有头像的女优
            self.add_text_main('[+]没有头像的女优!')
        elif mode == 2:  # 有头像的女优
            self.add_text_main('[+]有头像的女优!')
        elif mode == 3:  # 所有女优
            self.add_text_main('[+]所有女优!')
        actor_list = self.get_emby_actor_list()
        if actor_list['TotalRecordCount'] == 0:
            self.add_text_main("[*]======================================================")
            return
        count = 1
        actor_list_temp = ''
        for actor in actor_list['Items']:
            if mode == 3:  # 所有女优
                actor_list_temp += str(count) + '.' + actor['Name'] + ','
                count += 1
            elif mode == 2 and actor['ImageTags'] != {}:  # 有头像的女优
                actor_list_temp += str(count) + '.' + actor['Name'] + ','
                count += 1
            elif mode == 1 and actor['ImageTags'] == {}:  # 没有头像的女优
                actor_list_temp += str(count) + '.' + actor['Name'] + ','
                count += 1
            if (count - 1) % 5 == 0 and actor_list_temp != '':
                self.add_text_main('[+]' + actor_list_temp)
                actor_list_temp = ''
        self.add_text_main("[*]======================================================")

    def get_emby_actor_list(self):  # 获取emby的演员列表
        emby_url = self.Ui.lineEdit_emby_url.text()
        api_key = self.Ui.lineEdit_api_key.text()
        emby_url = emby_url.replace('：', ':')
        url = 'http://' + emby_url + '/emby/Persons?api_key=' + api_key
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/60.0.3100.0 Safari/537.36'}
        actor_list = {}
        try:
            getweb = requests.get(str(url), headers=headers, timeout=10)
            getweb.encoding = 'utf-8'
            actor_list = json.loads(getweb.text)
        except:
            self.add_text_main('[-]Error! Check your emby_url or api_key!')
            actor_list['TotalRecordCount'] = 0
        return actor_list

    def found_profile_picture(self, mode):  # mode=1，上传头像，mode=2，显示可添加头像的女优
        if mode == 1:
            self.add_text_main('[+]Start upload profile pictures!')
        elif mode == 2:
            self.add_text_main('[+]可添加头像的女优!')
        path = 'Actor'
        if not os.path.exists(path):
            self.add_text_main('[+]Actor folder not exist!')
            self.add_text_main("[*]======================================================")
            return
        path_success = 'Actor/Success'
        if not os.path.exists(path_success):
            os.makedirs(path_success)
        profile_pictures = os.listdir(path)
        actor_list = self.get_emby_actor_list()
        if actor_list['TotalRecordCount'] == 0:
            self.add_text_main("[*]======================================================")
            return
        count = 1
        for actor in actor_list['Items']:
            flag = 0
            pic_name = ''
            if actor['Name'] + '.jpg' in profile_pictures:
                flag = 1
                pic_name = actor['Name'] + '.jpg'
            elif actor['Name'] + '.png' in profile_pictures:
                flag = 1
                pic_name = actor['Name'] + '.png'
            if flag == 0:
                byname_list = re.split('[,，()（）]', actor['Name'])
                for byname in byname_list:
                    if byname + '.jpg' in profile_pictures:
                        pic_name = byname + '.jpg'
                        flag = 1
                        break
                    elif byname + '.png' in profile_pictures:
                        pic_name = byname + '.png'
                        flag = 1
                        break
            if flag == 1 and (actor['ImageTags'] == {} or not os.path.exists(path_success + '/' + pic_name)):
                if mode == 1:
                    try:
                        self.upload_profile_picture(count, actor, path + '/' + pic_name)
                        shutil.copy(path + '/' + pic_name, path_success + '/' + pic_name)
                    except Exception as error_info:
                        self.add_text_main('[-]Error in found_profile_picture! ' + str(error_info))
                else:
                    self.add_text_main('[+]' + "%4s" % str(count) + '.Actor name: ' + actor['Name'] + '  Pic name: '
                                       + pic_name)
                count += 1
        if count == 1:
            self.add_text_main('[-]NO profile picture can be uploaded!')
        self.add_text_main("[*]======================================================")

    def upload_profile_picture(self, count, actor, pic_path):  # 上传头像
        emby_url = self.Ui.lineEdit_emby_url.text()
        api_key = self.Ui.lineEdit_api_key.text()
        emby_url = emby_url.replace('：', ':')
        try:
            f = open(pic_path, 'rb')  # 二进制方式打开图文件
            b6_pic = base64.b64encode(f.read())  # 读取文件内容，转换为base64编码
            f.close()
            url = 'http://' + emby_url + '/emby/Items/' + actor['Id'] + '/Images/Primary?api_key=' + api_key
            if pic_path.endswith('jpg'):
                header = {"Content-Type": 'image/png', }
            else:
                header = {"Content-Type": 'image/jpeg', }
            requests.post(url=url, data=b6_pic, headers=header)
            self.add_text_main(
                '[+]' + "%4s" % str(count) + '.Success upload profile picture for ' + actor['Name'] + '!')
        except Exception as error_info:
            self.add_text_main('[-]Error in upload_profile_picture! ' + str(error_info))

    # ========================================================================自定义文件名
    def get_naming_rule(self, json_data):
        title, studio, publisher, year, outline, runtime, director, actor_photo, actor, release, tag, number, cover, website, series = get_info(
            json_data)
        if len(actor.split(',')) >= 10:  # 演员过多取前五个
            actor = actor.split(',')[0] + ',' + actor.split(',')[1] + ',' + actor.split(',')[2] + '等演员'
        
        # 使用翻译后的标题（如果可用且配置允许）
        title_for_naming = json_data.get('title_display', title)
        
        name_file = json_data['naming_file'].replace('title', title_for_naming).replace('studio', studio).replace('year',
                                                                                                       year).replace(
            'runtime',
            runtime).replace(
            'director', director).replace('actor', actor).replace('release', release).replace('number', number).replace(
            'series', series).replace('publisher', publisher)
        name_file = name_file.replace('//', '/').replace('--', '-').strip('-')
        if len(name_file) > 100:  # 文件名过长 取标题前70个字符
            self.add_text_main('[-]Error in Length of Path! Cut title!')
            name_file = name_file.replace(title_for_naming, title_for_naming[0:70])
        return name_file

    # ========================================================================语句添加到日志框（槽函数，在主线程执行）
    def _add_text_main_slot(self, text):
        try:
            if self.Ui.radioButton_log_on.isChecked() and hasattr(self, 'log_txt'):
                self.log_txt.write((str(text) + '\n').encode('utf8'))
            self.Ui.textBrowser_log_main.append(text)
            self.Ui.textBrowser_log_main.moveCursor(QTextCursor.End)
        except Exception as error_info:
            try:
                self.Ui.textBrowser_log_main.append('[-]Error in add_text_main: ' + str(error_info))
            except:
                pass

    # ========================================================================语句添加到日志框（线程安全）
    def add_text_main(self, text):
        # 使用信号机制确保在主线程更新 GUI
        self.textSignal.emit(str(text))

    # ========================================================================移动到失败文件夹
    def moveFailedFolder(self, filepath, failed_folder):
        if self.Ui.radioButton_fail_move_on.isChecked():
            if self.Ui.radioButton_soft_off.isChecked():
                try:
                    shutil.move(filepath, failed_folder + '/')
                    self.add_text_main('[-]Move ' + os.path.split(filepath)[1] + ' to Failed output folder Success!')
                except Exception as error_info:
                    self.add_text_main('[-]Error in moveFailedFolder! ' + str(error_info))

    # ========================================================================下载文件
    def DownloadFileWithFilename(self, url, filename, path, Config, filepath, failed_folder):
        proxy_type = ''
        retry_count = 0
        proxy = ''
        timeout = 0
        try:
            proxy_type, proxy, timeout, retry_count, _ = get_config()
        except Exception as error_info:
            print('[-]Error in DownloadFileWithFilename! ' + str(error_info))
            self.add_text_main('[-]Error in DownloadFileWithFilename! Proxy config error! Please check the config.')
        
        # 关键修复：当 type=no 时，proxies 设为 None 以使用系统环境变量代理
        if proxy_type == 'no':
            proxies = None  # 使用系统代理（HTTP_PROXY/HTTPS_PROXY 环境变量）
        else:
            proxies = get_proxies(proxy_type, proxy)
        
        i = 0
        while i < retry_count:
            try:
                if not os.path.exists(path):
                    os.makedirs(path)
                # 添加 Referer 头，某些网站需要它来下载图片
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                                  'Chrome/120.0.0.0 Safari/537.36',
                    'Referer': 'https://www.javbus.com/',
                    'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8'
                }
                result = requests.get(str(url), headers=headers, timeout=timeout, proxies=proxies)
                
                # 检查HTTP状态码
                if result.status_code != 200:
                    raise Exception(f"HTTP {result.status_code}")
                
                file_path = str(path) + "/" + filename
                with open(file_path, "wb") as code:
                    code.write(result.content)
                code.close()
                # 检查下载的文件是否为空
                if os.path.getsize(file_path) == 0:
                    os.remove(file_path)
                    raise Exception("Downloaded file is empty")
                return
            except Exception as error_info:
                i += 1
                # 删除可能存在的空文件
                file_path = str(path) + "/" + filename
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except:
                        pass
                error_str = str(error_info)
                print(f'[-]Error in DownloadFileWithFilename! {error_str}')
                print(f'[-]Image Download :   Connect retry {i}/{retry_count}')
        self.add_text_main('[-]Connect Failed! Please check your Proxy or Network!')
        # 在仅刮削模式下不移动失败文件
        try:
            config_file = 'config.ini'
            config = ConfigParser()
            config.read(config_file, encoding='UTF-8')
            no_file_move = int(config['common']['no_file_move'])
        except:
            no_file_move = 0
        if no_file_move == 0:
            self.moveFailedFolder(filepath, failed_folder)

    # ========================================================================下载缩略图
    def thumbDownload(self, json_data, path, naming_rule, Config, filepath, failed_folder):
        thumb_name = naming_rule + '-thumb.jpg'
        thumb_path = path + '/' + thumb_name
        
        # 检查 thumb 是否存在且有效（非空且大小大于 1KB）
        if os.path.exists(thumb_path):
            file_size = os.path.getsize(thumb_path)
            if file_size > 1024:  # 大于1KB认为是有效图片
                self.add_text_main('[+]Thumb Existed!     ' + thumb_name + f' ({file_size/1024:.1f} KB)')
                return
            else:
                self.add_text_main('[!]Thumb exists but is empty/corrupted, re-downloading...')
                try:
                    os.remove(thumb_path)
                except:
                    pass
        
        # 检查封面URL是否有效
        cover_url = json_data.get('cover', '')
        if not cover_url or 'http' not in cover_url:
            self.add_text_main('[-]Cover URL is invalid, skip thumb download')
            return
            
        i = 1
        max_retry = int(Config['proxy']['retry']) if Config['proxy']['retry'] else 3
        download_success = False
        
        while i <= max_retry:
            try:
                self.DownloadFileWithFilename(cover_url, thumb_name, path, Config, filepath, failed_folder)
                if check_pic(thumb_path):
                    file_size = os.path.getsize(thumb_path)
                    self.add_text_main('[+]Thumb Downloaded!  ' + thumb_name + f' ({file_size/1024:.1f} KB)')
                    download_success = True
                    break
                else:
                    self.add_text_main('[!]Thumb image check failed, retrying... ' + str(i) + '/' + str(max_retry))
                    # 删除损坏的文件
                    if os.path.exists(thumb_path):
                        try:
                            os.remove(thumb_path)
                        except:
                            pass
            except Exception as e:
                self.add_text_main('[-]Thumb download error: ' + str(e) + ' retry: ' + str(i) + '/' + str(max_retry))
            i += 1
        
        if not download_success:
            self.add_text_main('[-]Thumb download failed after ' + str(max_retry) + ' retries')
            # 不创建空文件，让后续处理知道文件缺失

    def deletethumb(self, path, naming_rule):
        try:
            thumb_path = path + '/' + naming_rule + '-thumb.jpg'
            if (not self.Ui.checkBox_download_thumb.isChecked()) and os.path.exists(thumb_path):
                os.remove(thumb_path)
                self.add_text_main('[+]Thumb Delete!      ' + naming_rule + '-thumb.jpg')
        except Exception as error_info:
            self.add_text_main('[-]Error in deletethumb: ' + str(error_info))

    # ========================================================================无码片下载封面图
    def smallCoverDownload(self, path, naming_rule, json_data, Config, filepath, failed_folder):
        if json_data['imagecut'] == 3:
            if json_data['cover_small'] == '':
                return 'small_cover_error'
            is_pic_open = 0
            poster_name = naming_rule + '-poster.jpg'
            if os.path.exists(path + '/' + poster_name):
                self.add_text_main('[+]Poster Existed!    ' + poster_name)
                return
            self.DownloadFileWithFilename(json_data['cover_small'], 'cover_small.jpg', path, Config, filepath,
                                          failed_folder)
            try:
                if not check_pic(path + '/cover_small.jpg'):
                    raise Exception("The Size of smallcover is Error! Deleted cover_small.jpg!")
                fp = open(path + '/cover_small.jpg', 'rb')
                is_pic_open = 1
                img = Image.open(fp)
                w = img.width
                h = img.height
                if not (1.4 <= h / w <= 1.6):
                    self.add_text_main('[-]The size of cover_small.jpg is unfit, Try to cut thumb!')
                    fp.close()
                    os.remove(path + '/cover_small.jpg')
                    return 'small_cover_error'
                img.save(path + '/' + poster_name)
                self.add_text_main('[+]Poster Downloaded! ' + poster_name)
                fp.close()
                os.remove(path + '/cover_small.jpg')
            except Exception as error_info:
                self.add_text_main('[-]Error in smallCoverDownload: ' + str(error_info))
                if is_pic_open:
                    fp.close()
                os.remove(path + '/cover_small.jpg')
                self.add_text_main('[+]Try to cut cover!')
                return 'small_cover_error'

    # ========================================================================下载剧照
    def extrafanartDownload(self, json_data, path, Config, filepath, failed_folder):
        if len(json_data['extrafanart']) == 0:
            json_data['extrafanart'] = ''
        if self.Ui.radioButton_extrafanart_download_on.isChecked() and str(json_data['extrafanart']) != '':
            self.add_text_main('[+]ExtraFanart Downloading!')
            extrafanart_folder = self.Ui.lineEdit_extrafanart_dir.text()
            if extrafanart_folder == '':
                extrafanart_folder = 'extrafanart'
            extrafanart_path = path + '/' + extrafanart_folder
            extrafanart_list = json_data['extrafanart']
            if not os.path.exists(extrafanart_path):
                os.makedirs(extrafanart_path)
            extrafanart_count = 0
            for extrafanart_url in extrafanart_list:
                extrafanart_count += 1
                if not os.path.exists(extrafanart_path + '/fanart' + str(extrafanart_count) + '.jpg'):
                    i = 1
                    while i <= int(Config['proxy']['retry']):
                        self.DownloadFileWithFilename(extrafanart_url, 'fanart' + str(extrafanart_count) + '.jpg',
                                                      extrafanart_path, Config, filepath, failed_folder)
                        if not check_pic(extrafanart_path + '/fanart' + str(extrafanart_count) + '.jpg'):
                            print('[!]Image Download Failed! Trying again. ' + str(i) + '/' + Config['proxy']['retry'])
                            i = i + 1
                        else:
                            break

    # ========================================================================打印NFO
    def escape_xml(self, text):
        """XML字符转义：将< > &等转为实体引用"""
        if not text:
            return ''
        text = str(text)
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        text = text.replace('"', '&quot;')
        text = text.replace("'", '&apos;')
        return text
    
    def convert_actor_id_to_numeric(self, actor_id, actor_name=''):
        """
        将字母数字混合的演员ID转换为纯数字ID
        用于确保跨影片演员关联一致性
        
        转换规则：
        - 如果已经是纯数字，直接返回
        - 如果是字母+数字混合，使用哈希转换为数字
        """
        if not actor_id:
            return ''
        
        original_id = str(actor_id)
        
        # 提取ID部分（去掉 source: 前缀）
        if ':' in original_id:
            source, actor_id = original_id.split(':', 1)
        else:
            actor_id = original_id
        
        # 检查是否已经是纯数字
        if actor_id.isdigit():
            if actor_name:
                self.add_text_main(f'[*]演员ID [{actor_name}]: {actor_id} (纯数字)')
            return actor_id
        
        # 字母数字混合，需要转换
        # 方法：将每个字符转为ASCII码后拼接
        result = ''
        for char in actor_id.lower():
            if char.isdigit():
                result += char
            elif char.isalpha():
                # a=1, b=2, ..., z=26
                result += str(ord(char) - ord('a') + 1).zfill(2)
        
        # 如果结果太长，取前10位
        if len(result) > 10:
            result = result[:10]
        
        # 确保不以0开头
        result = result.lstrip('0')
        if not result:
            result = '0'
        
        # 输出转换日志
        if actor_name:
            self.add_text_main(f'[*]演员ID [{actor_name}]: {original_id} -> {result} (已转换)')
        
        return result
    
    def clean_plot_text(self, text):
        """清洗剧情文本：移除Python列表残留字符"""
        if not text:
            return ''
        text = str(text)
        # 如果是列表字符串形式，尝试清洗
        if text.startswith('[') and text.endswith(']'):
            # 移除列表符号和引号
            text = text.strip('[]')
            text = text.replace("'", "")
            text = text.replace('"', "")
            text = text.replace(',', '')
        # 移除转义符
        text = text.replace('\\n', ' ')
        text = text.replace('\\t', ' ')
        text = text.replace('\\', '')
        # 清理多余空格
        text = ' '.join(text.split())
        return text.strip()
    
    def PrintFiles(self, path, name_file, cn_sub, leak, json_data, filepath, failed_folder):
        title, studio, publisher, year, outline, runtime, director, actor_photo, actor, release, tag, number, cover, website, series = get_info(
            json_data)
        name_media = json_data['naming_media'].replace('title', title).replace('studio', studio).replace('year',
                                                                                                         year).replace(
            'runtime',
            runtime).replace(
            'director', director).replace('actor', actor).replace('release', release).replace('number', number).replace(
            'series', series).replace('publisher', publisher)
        try:
            if not os.path.exists(path):
                os.makedirs(path)
            
            # 检查是否覆盖已存在的 nfo 文件
            config_file = 'config.ini'
            config = ConfigParser()
            config.read(config_file, encoding='UTF-8')
            overwrite_nfo = config.getboolean('file_download', 'overwrite_nfo', fallback=False)
            
            nfo_path = path + "/" + name_file + ".nfo"
            if os.path.exists(nfo_path) and not overwrite_nfo:
                self.add_text_main('[+]Nfo Existed!       ' + name_file + ".nfo")
                return
            elif os.path.exists(nfo_path) and overwrite_nfo:
                self.add_text_main('[!]Nfo Overwrite!     ' + name_file + ".nfo")
            
            with open(nfo_path, "wt", encoding='UTF-8') as code:
                print('<?xml version="1.0" encoding="UTF-8" ?>', file=code)
                print("<movie>", file=code)
                
                # 生成NFO标题：使用 number-actor-title-release 格式
                # 使用翻译后的标题
                title_for_nfo = json_data.get('title_display', title)
                # 构建完整标题：number-actor-title-release
                # 限制演员数量，最多2个
                actor_str = actor if actor != 'unknown' else ''
                if actor_str:
                    actor_list_nfo = [a.strip() for a in actor_str.split(',') if a.strip()]
                    if len(actor_list_nfo) > 2:
                        actor_str = ', '.join(actor_list_nfo[:2])
                nfo_title = f"{number}"
                if actor_str:
                    nfo_title += f"-{actor_str}"
                if title_for_nfo and title_for_nfo != 'unknown':
                    nfo_title += f"-{title_for_nfo}"
                if release and release != 'unknown':
                    nfo_title += f"-{release}"
                # 清理多余的连字符
                nfo_title = nfo_title.replace('--', '-').strip('-')
                print("  <title>" + self.escape_xml(nfo_title) + "</title>", file=code)
                
                # 添加原文标题（作为 sorttitle）
                title_original = json_data.get('title_original', '')
                if title_original and title_original != title_for_nfo:
                    print("  <originaltitle>" + self.escape_xml(title_original) + "</originaltitle>", file=code)
                
                # 添加uniqueid字段（番号）
                print(f'  <uniqueid type="jp.javbus" default="true">{number}</uniqueid>', file=code)
                
                print("  <set>", file=code)
                print("  </set>", file=code)
                try:
                    if str(json_data['score']) != 'unknown' and str(json_data['score']) != '' and float(
                            json_data['score']) != 0.0:
                        print("  <rating>" + str(json_data['score']) + "</rating>", file=code)
                except Exception as err:
                    print("Error in json_data score!" + str(err))
                if studio != 'unknown':
                    print("  <studio>" + self.escape_xml(studio) + "</studio>", file=code)
                if str(year) != 'unknown':
                    print("  <year>" + year + "</year>", file=code)
                
                # 简介：优先使用翻译后的简介，并进行清洗和转义
                outline_display = json_data.get('outline_translated', outline)
                outline_original = json_data.get('outline_original', '')
                # 清洗文本
                outline_display = self.clean_plot_text(outline_display)
                outline_original = self.clean_plot_text(outline_original)
                if outline_display and outline_display != 'unknown':
                    print("  <outline>" + self.escape_xml(outline_display) + "</outline>", file=code)
                    print("  <plot>" + self.escape_xml(outline_display) + "</plot>", file=code)
                # 如果原文与译文不同，添加原文作为注释
                if outline_original and outline_original != outline_display and outline_original != 'unknown':
                    print("  <!-- original_plot>" + self.escape_xml(outline_original) + "</original_plot -->", file=code)
                
                if str(runtime) != 'unknown':
                    print("  <runtime>" + str(runtime).replace(" ", "") + "</runtime>", file=code)
                if director != 'unknown':
                    print("  <director>" + self.escape_xml(director) + "</director>", file=code)
                print("  <poster>" + name_file + "-poster.jpg</poster>", file=code)
                print("  <thumb>" + name_file + "-thumb.jpg</thumb>", file=code)
                print("  <fanart>" + name_file + "-fanart.jpg</fanart>", file=code)
                
                # 演员信息（标准tmdb格式）- NFO中显示所有演员
                try:
                    actor_id_map = json_data.get('actor_id', {})
                    actor_local_photo = json_data.get('actor_local_photo', {})
                    actor_list = list(actor_photo.keys()) if actor_photo else []
                    
                    # NFO中显示所有演员（不限制数量）
                    for idx, key in enumerate(actor_list):
                        if str(key) != 'unknown' and str(key) != '':
                            print('  <actor>', file=code)
                            print("    <name>" + self.escape_xml(key) + "</name>", file=code)
                            print("    <role>演员</role>", file=code)
                            print("    <order>" + str(idx) + "</order>", file=code)
                            
                            # 计算数字ID（用于头像路径）
                            actor_raw_id = actor_id_map.get(key, '')
                            numeric_id = self.convert_actor_id_to_numeric(actor_raw_id, key) if actor_raw_id else ''
                            
                            # 头像路径：优先本地，其次远程
                            if key in actor_local_photo and actor_local_photo[key]:
                                # 本地路径统一使用数字ID格式: ./.actors/数字ID.jpg
                                if numeric_id:
                                    thumb_path = f'./.actors/{numeric_id}.jpg'
                                else:
                                    # 回退到原始路径
                                    thumb_path = actor_local_photo[key]
                                print('    <thumb>' + thumb_path + '</thumb>', file=code)
                            elif key in actor_photo and actor_photo[key]:
                                # 远程URL
                                print('    <thumb>' + actor_photo[key] + '</thumb>', file=code)
                            
                            # 演员ID和profile链接（纯数字tmdbid格式，用于跨影片关联）
                            if actor_raw_id:
                                # tmdbid格式: 纯数字ID
                                print('    <tmdbid>' + numeric_id + '</tmdbid>', file=code)
                                # profile链接（使用原始ID）
                                if ':' in str(actor_raw_id):
                                    source, original_id = str(actor_raw_id).split(':', 1)
                                    if source == 'javbus':
                                        profile_url = f'https://www.javbus.com/star/{original_id}'
                                        print('    <profile>' + profile_url + '</profile>', file=code)
                            
                            print("  </actor>", file=code)
                except Exception as error_info:
                    self.add_text_main('[-]Error in actor_photo: ' + str(error_info))
                if studio != 'unknown':
                    print("  <maker>" + self.escape_xml(studio) + "</maker>", file=code)
                if publisher != 'unknown':
                    print("  <maker>" + self.escape_xml(publisher) + "</maker>", file=code)
                print("  <label>", file=code)
                print("  </label>", file=code)
                try:
                    for i in tag:
                        if i != 'unknown':
                            print("  <tag>" + self.escape_xml(i) + "</tag>", file=code)
                except Exception as error_info:
                    self.add_text_main('[-]Error in tag: ' + str(error_info))
                if json_data['imagecut'] == 3:
                    print("  <tag>無碼</tag>", file=code)
                if leak == 1:
                    print("  <tag>流出</tag>", file=code)
                if cn_sub == 1:
                    print("  <tag>中文字幕</tag>", file=code)
                if series != 'unknown':
                    print("  <tag>" + '系列:' + self.escape_xml(series) + "</tag>", file=code)
                if studio != 'unknown':
                    print("  <tag>" + '製作:' + self.escape_xml(studio) + "</tag>", file=code)
                if publisher != 'unknown':
                    print("  <tag>" + '發行:' + self.escape_xml(publisher) + "</tag>", file=code)
                try:
                    for i in tag:
                        if i != 'unknown':
                            print("  <genre>" + self.escape_xml(i) + "</genre>", file=code)
                except Exception as error_info:
                    self.add_text_main('[-]Error in genre: ' + str(error_info))
                if json_data['imagecut'] == 3:
                    print("  <genre>無碼</genre>", file=code)
                if leak == 1:
                    print("  <genre>流出</genre>", file=code)
                if cn_sub == 1:
                    print("  <genre>中文字幕</genre>", file=code)
                if series != 'unknown':
                    print("  <genre>" + '系列:' + self.escape_xml(series) + "</genre>", file=code)
                if studio != 'unknown':
                    print("  <genre>" + '製作:' + self.escape_xml(studio) + "</genre>", file=code)
                if publisher != 'unknown':
                    print("  <genre>" + '發行:' + self.escape_xml(publisher) + "</genre>", file=code)
                print("  <num>" + number + "</num>", file=code)
                if release != 'unknown':
                    print("  <premiered>" + release + "</premiered>", file=code)
                    print("  <release>" + release + "</release>", file=code)
                # URL字符串strip处理
                cover_clean = cover.strip() if cover else ''
                website_clean = website.strip() if website else ''
                print("  <cover>" + cover_clean + "</cover>", file=code)
                print("  <website>" + website_clean + "</website>", file=code)
                print("</movie>", file=code)
                self.add_text_main("[+]Nfo Wrote!         " + name_file + ".nfo")
        except Exception as error_info:
            self.add_text_main("[-]Write Failed!")
            self.add_text_main('[-]Error in PrintFiles: ' + str(error_info))
            self.moveFailedFolder(filepath, failed_folder)

    # ========================================================================thumb复制为fanart
    def copyRenameJpgToFanart(self, path, naming_rule):
        try:
            thumb_path = path + '/' + naming_rule + '-thumb.jpg'
            fanart_path = path + '/' + naming_rule + '-fanart.jpg'
            
            # 检查 fanart 是否已存在且有效
            if os.path.exists(fanart_path) and os.path.getsize(fanart_path) > 0:
                self.add_text_main('[+]Fanart Existed!    ' + naming_rule + '-fanart.jpg')
                return
            
            # 检查 thumb 是否存在且有效
            if not os.path.exists(thumb_path) or os.path.getsize(thumb_path) == 0:
                self.add_text_main('[-]Thumb not found or empty, skip fanart copy')
                return
            
            shutil.copy(thumb_path, fanart_path)
            self.add_text_main('[+]Fanart Copied!     ' + naming_rule + '-fanart.jpg')
        except Exception as error_info:
            self.add_text_main('[-]Error in copyRenameJpgToFanart: ' + str(error_info))

    # ========================================================================移动视频、字幕
    def pasteFileToFolder(self, filepath, path, naming_rule, failed_folder):
        type = str(os.path.splitext(filepath)[1])
        try:
            if os.path.exists(path + '/' + naming_rule + type):
                raise FileExistsError
            if self.Ui.radioButton_soft_on.isChecked():  # 如果使用软链接
                os.symlink(filepath, path + '/' + naming_rule + type)
                self.add_text_main('[+]Movie Linked!     ' + naming_rule + type)
            else:
                shutil.move(filepath, path + '/' + naming_rule + type)
                self.add_text_main('[+]Movie Moved!       ' + naming_rule + type)
            path_old = filepath.replace(filepath.split('/')[-1], '')
            filename = filepath.split('/')[-1].split('.')[0]
            sub_type = self.Ui.lineEdit_sub_type.text().split('|')
            for sub in sub_type:
                if os.path.exists(path_old + '/' + filename + sub):  # 字幕移动
                    shutil.move(path_old + '/' + filename + sub, path + '/' + naming_rule + sub)
                    self.add_text_main('[+]Sub moved!         ' + naming_rule + sub)
                    return True
        except FileExistsError:
            self.add_text_main('[+]Movie Existed!     ' + naming_rule + type)
            if os.path.split(filepath)[0] != path:
                self.moveFailedFolder(filepath, failed_folder)
        except PermissionError:
            self.add_text_main('[-]PermissionError! Please run as Administrator!')
        except Exception as error_info:
            self.add_text_main('[-]Error in pasteFileToFolder: ' + str(error_info))
        return False

    # ========================================================================仅重命名文件（仅刮削模式使用）
    def renameFileOnly(self, filepath, naming_rule):
        """仅刮削模式下使用：在原目录重命名文件，不移动
        
        Returns:
            str: 新的文件路径，失败返回 None
        """
        try:
            file_ext = os.path.splitext(filepath)[1]
            file_dir = os.path.dirname(filepath)
            new_path = os.path.join(file_dir, naming_rule + file_ext)
            
            # 如果文件名已经是目标名称，则跳过重命名
            if filepath == new_path:
                self.add_text_main('[+]File already named correctly: ' + naming_rule + file_ext)
                return new_path
                
            # 如果目标文件已存在，添加序号避免冲突
            if os.path.exists(new_path):
                base_name = naming_rule
                counter = 1
                while os.path.exists(new_path):
                    new_path = os.path.join(file_dir, f"{base_name}_{counter}{file_ext}")
                    counter += 1
                naming_rule = f"{base_name}_{counter-1}"
            
            os.rename(filepath, new_path)
            self.add_text_main('[+]File Renamed!       ' + os.path.basename(new_path))
            
            # 同时重命名字幕文件
            old_filename = os.path.splitext(os.path.basename(filepath))[0]
            sub_type = self.Ui.lineEdit_sub_type.text().split('|')
            for sub in sub_type:
                old_sub = os.path.join(file_dir, old_filename + sub)
                if os.path.exists(old_sub):
                    new_sub = os.path.join(file_dir, naming_rule + sub)
                    os.rename(old_sub, new_sub)
                    self.add_text_main('[+]Sub Renamed!        ' + os.path.basename(new_sub))
            return new_path
        except Exception as error_info:
            self.add_text_main('[-]Error in renameFileOnly: ' + str(error_info))
            return None

    # ========================================================================仅重命名文件夹（仅刮削模式使用）
    def renameFolderOnly(self, old_folder_path, json_data):
        """仅刮削模式下使用：根据元数据重命名文件夹
        
        Returns:
            str: 新的文件夹路径，失败返回原路径
        """
        try:
            from Function.Function import get_info
            title, studio, publisher, year, outline, runtime, director, actor_photo, actor, release, tag, number, cover, website, series = get_info(
                json_data)
            
            if len(actor.split(',')) >= 10:
                actor = actor.split(',')[0] + ',' + actor.split(',')[1] + ',' + actor.split(',')[2] + '等演员'
            
            # 使用翻译后的标题（如果可用）
            title_for_folder = json_data.get('title_display', title)
            
            # 生成新文件夹名
            folder_name = json_data['folder_name']
            new_folder_name = folder_name.replace('title', title_for_folder).replace('studio', studio).replace('year', year).replace('runtime', runtime).replace(
                'director', director).replace('actor', actor).replace('release', release).replace('number', number).replace(
                'series', series).replace('publisher', publisher)
            new_folder_name = new_folder_name.replace('--', '-').strip('-')
            if len(new_folder_name) > 100:
                new_folder_name = new_folder_name.replace(title_for_folder, title_for_folder[0:70])
            
            # 清理非法字符
            new_folder_name = new_folder_name.replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
            
            # 获取父目录和当前文件夹名
            parent_dir = os.path.dirname(old_folder_path)
            new_folder_path = os.path.join(parent_dir, new_folder_name)
            
            # 如果名称相同，无需重命名
            if old_folder_path == new_folder_path:
                self.add_text_main('[+]Folder already named correctly: ' + new_folder_name)
                return old_folder_path
            
            # 如果目标文件夹已存在，添加序号
            if os.path.exists(new_folder_path):
                base_name = new_folder_name
                counter = 1
                while os.path.exists(new_folder_path):
                    new_folder_path = os.path.join(parent_dir, f"{base_name}_{counter}")
                    counter += 1
                new_folder_name = f"{base_name}_{counter-1}"
            
            # 执行重命名
            os.rename(old_folder_path, new_folder_path)
            self.add_text_main('[+]Folder Renamed!     ' + os.path.basename(old_folder_path) + ' -> ' + os.path.basename(new_folder_path))
            return new_folder_path
            
        except Exception as error_info:
            self.add_text_main('[-]Error in renameFolderOnly: ' + str(error_info))
            return old_folder_path

    # ========================================================================有码片裁剪封面
    def cutImage(self, imagecut, path, naming_rule):
        if imagecut != 3:
            thumb_name = naming_rule + '-thumb.jpg'
            poster_name = naming_rule + '-poster.jpg'
            thumb_path = path + '/' + thumb_name
            poster_path = path + '/' + poster_name
            
            # 检查 poster 是否已存在
            if os.path.exists(poster_path) and os.path.getsize(poster_path) > 0:
                self.add_text_main('[+]Poster Existed!    ' + poster_name)
                return
            
            # 检查 thumb 是否存在且有效
            if not os.path.exists(thumb_path) or os.path.getsize(thumb_path) == 0:
                self.add_text_main('[-]Thumb not found or empty, skip poster cut')
                return
            
            try:
                if imagecut == 0:
                    self.image_cut(path, thumb_name)
                else:
                    img = Image.open(thumb_path)
                    w = img.width
                    h = img.height
                    img2 = img.crop((w / 1.9, 0, w, h))
                    img2.save(poster_path)
                    self.add_text_main('[+]Poster Cut!        ' + poster_name)
            except Exception as e:
                self.add_text_main('[-]Thumb cut failed: ' + str(e))

    def fix_size(self, path, naming_rule):
        try:
            poster_path = path + '/' + naming_rule + '-poster.jpg'
            # 检查 poster 是否存在且有效
            if not os.path.exists(poster_path) or os.path.getsize(poster_path) == 0:
                return
            pic = Image.open(poster_path)
            (width, height) = pic.size
            if not 2 / 3 - 0.05 <= width / height <= 2 / 3 + 0.05:  # 仅处理会过度拉伸的图片
                fixed_pic = pic.resize((int(width), int(3 / 2 * width)))  # 拉伸图片
                fixed_pic = fixed_pic.filter(ImageFilter.GaussianBlur(radius=50))  # 高斯模糊
                fixed_pic.paste(pic, (0, int((3 / 2 * width - height) / 2)))  # 粘贴原图
                fixed_pic.save(poster_path)
        except Exception as error_info:
            self.add_text_main('[-]Error in fix_size: ' + str(error_info))

    # ========================================================================下载演员头像（全局共享）
    def downloadActorPhotos(self, json_data, path, Config):
        """下载演员头像到全局共享文件夹，并更新 json_data 中的本地路径"""
        try:
            # 检查是否启用演员头像下载
            try:
                download_enabled = Config.getboolean('actor', 'download_actor_photo', fallback=True)
            except:
                download_enabled = True
            
            if not download_enabled:
                return
            
            # 获取演员信息
            actor_photo = json_data.get('actor_photo', {})
            actor_id = json_data.get('actor_id', {})
            
            if not actor_photo:
                return
            
            # 在视频所在目录下创建.actors文件夹（业内通用做法）
            actor_folder = '.actors'
            actor_path = os.path.join(path, actor_folder)
            
            # 创建演员头像文件夹
            if not os.path.exists(actor_path):
                os.makedirs(actor_path)
                self.add_text_main('[+]Actor folder created: ' + actor_path)
            
            # 初始化本地头像路径字典
            if 'actor_local_photo' not in json_data:
                json_data['actor_local_photo'] = {}
            
            # 下载每个演员的头像
            downloaded_count = 0
            for actor_name, photo_url in actor_photo.items():
                if not photo_url or not photo_url.startswith('http'):
                    continue
                
                # 获取演员原始ID并转换为纯数字ID
                actor_raw_id = actor_id.get(actor_name, '')
                numeric_id = self.convert_actor_id_to_numeric(actor_raw_id, actor_name) if actor_raw_id else ''
                
                # 使用数字ID作为文件名（确保跨影片一致性）
                if numeric_id:
                    filename = f"{numeric_id}.jpg"
                else:
                    # 回退到演员名字（清理特殊字符）
                    safe_name = actor_name.replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
                    filename = f"{safe_name}.jpg"
                
                file_path = os.path.join(actor_path, filename)
                # NFO中使用相对路径: ./.actors/数字ID.jpg
                local_path = f"./{actor_folder}/{filename}"
                
                # 如果文件已存在且有效，直接使用本地路径
                if os.path.exists(file_path) and os.path.getsize(file_path) > 1024:
                    json_data['actor_local_photo'][actor_name] = local_path
                    continue
                
                # 下载头像
                try:
                    self.DownloadFileWithFilename(
                        photo_url, 
                        filename, 
                        actor_path, 
                        Config, 
                        '', 
                        ''
                    )
                    if os.path.exists(file_path) and os.path.getsize(file_path) > 1024:
                        downloaded_count += 1
                        # 更新 json_data 中的本地路径
                        json_data['actor_local_photo'][actor_name] = local_path
                        self.add_text_main(f'[+]Actor photo: {actor_name} -> {local_path}')
                except Exception as e:
                    self.add_text_main(f'[-]Failed to download photo for {actor_name}: {str(e)[:50]}')
            
            if downloaded_count > 0:
                self.add_text_main(f'[+]Downloaded {downloaded_count} actor photos')
            else:
                self.add_text_main(f'[+]Actor photos already exist in folder')
                
        except Exception as error_info:
            self.add_text_main('[-]Error in downloadActorPhotos: ' + str(error_info))

    # ========================================================================加水印
    def add_mark(self, poster_path, thumb_path, cn_sub, leak, uncensored, config):
        mark_type = ''
        if self.Ui.checkBox_sub.isChecked() and cn_sub:
            mark_type += ',字幕'
        if self.Ui.checkBox_leak.isChecked() and leak:
            mark_type += ',流出'
        if self.Ui.checkBox_uncensored.isChecked() and uncensored:
            mark_type += ',无码'
        if self.Ui.radioButton_thumb_mark_on.isChecked() and mark_type != '' and self.Ui.checkBox_download_thumb.isChecked() and os.path.exists(thumb_path):
            self.add_mark_thread(thumb_path, cn_sub, leak, uncensored)
            self.add_text_main('[+]Thumb Add Mark:    ' + mark_type.strip(','))
        if self.Ui.radioButton_poster_mark_on.isChecked() and mark_type != '' and self.Ui.checkBox_download_poster.isChecked() and os.path.exists(poster_path):
            self.add_mark_thread(poster_path, cn_sub, leak, uncensored)
            self.add_text_main('[+]Poster Add Mark:   ' + mark_type.strip(','))

    def add_mark_thread(self, pic_path, cn_sub, leak, uncensored):
        size = 14 - int(self.Ui.horizontalSlider_mark_size.value())  # 获取自定义大小的值
        img_pic = Image.open(pic_path)
        count = 0  # 获取自定义位置，取余配合pos达到顺时针添加的效果
        if self.Ui.radioButton_top_left.isChecked():
            count = 0
        elif self.Ui.radioButton_top_right.isChecked():
            count = 1
        elif self.Ui.radioButton_bottom_right.isChecked():
            count = 2
        elif self.Ui.radioButton_bottom_left.isChecked():
            count = 3
        if self.Ui.checkBox_sub.isChecked() and cn_sub == 1:
            self.add_to_pic(pic_path, img_pic, size, count, 1)  # 添加
            count = (count + 1) % 4
        if self.Ui.checkBox_leak.isChecked() and leak == 1:
            self.add_to_pic(pic_path, img_pic, size, count, 2)
            count = (count + 1) % 4
        if self.Ui.checkBox_uncensored.isChecked() and uncensored == 1:
            self.add_to_pic(pic_path, img_pic, size, count, 3)
        img_pic.close()

    def add_to_pic(self, pic_path, img_pic, size, count, mode):
        mark_pic_path = ''
        if mode == 1:
            mark_pic_path = 'Img/SUB.png'
        elif mode == 2:
            mark_pic_path = 'Img/LEAK.png'
        elif mode == 3:
            mark_pic_path = 'Img/UNCENSORED.png'
        img_subt = Image.open(mark_pic_path)
        scroll_high = int(img_pic.height / size)
        scroll_wide = int(scroll_high * img_subt.width / img_subt.height)
        img_subt = img_subt.resize((scroll_wide, scroll_high), Image.ANTIALIAS)
        r, g, b, a = img_subt.split()  # 获取颜色通道，保持png的透明性
        # 封面四个角的位置
        pos = [
            {'x': 0, 'y': 0},
            {'x': img_pic.width - scroll_wide, 'y': 0},
            {'x': img_pic.width - scroll_wide, 'y': img_pic.height - scroll_high},
            {'x': 0, 'y': img_pic.height - scroll_high},
        ]
        img_pic.paste(img_subt, (pos[count]['x'], pos[count]['y']), mask=a)
        img_pic.save(pic_path, quality=95)

    # ========================================================================获取分集序号
    def get_part(self, filepath, failed_folder):
        try:
            if re.search(r'-CD\d+', filepath):
                return re.findall(r'-CD\d+', filepath)[0]
            if re.search(r'-cd\d+', filepath):
                return re.findall(r'-cd\d+', filepath)[0]
        except Exception as error_info:
            self.add_text_main('[-]Error in get_part: ' + str(error_info))
            self.moveFailedFolder(filepath, failed_folder)

    # ========================================================================更新进度条
    def set_processbar(self, value):
        self.Ui.progressBar_avdc.setProperty("value", value)
        self.Ui.label_percent.setText(str(value) + '%')

    # ========================================================================输出调试信息
    def debug_mode(self, json_data):
        try:
            self.add_text_main('[+] ---Debug info---')
            for key, value in json_data.items():
                if value == '' or key == 'actor_photo' or key == 'extrafanart':
                    continue
                if key == 'tag' and len(value) == 0:
                    continue
                elif key == 'tag':
                    value = str(json_data['tag']).strip(" ['']").replace('\'', '')
                self.add_text_main('   [+]-' + "%-13s" % key + ': ' + str(value))
            self.add_text_main('[+] ---Debug info---')
        except Exception as error_info:
            self.add_text_main('[-]Error in debug_mode: ' + str(error_info))

    # ========================================================================创建输出文件夹
    def creatFolder(self, success_folder, json_data, config):
        title, studio, publisher, year, outline, runtime, director, actor_photo, actor, release, tag, number, cover, website, series = get_info(
            json_data)
        if len(actor.split(',')) >= 10:  # 演员过多取前五个
            actor = actor.split(',')[0] + ',' + actor.split(',')[1] + ',' + actor.split(',')[2] + '等演员'
        folder_name = json_data['folder_name']
        path = folder_name.replace('title', title).replace('studio', studio).replace('year', year).replace('runtime',
                                                                                                           runtime).replace(
            'director', director).replace('actor', actor).replace('release', release).replace('number', number).replace(
            'series', series).replace('publisher', publisher)  # 生成文件夹名
        path = path.replace('--', '-').strip('-')
        if len(path) > 100:  # 文件夹名过长 取标题前70个字符
            self.add_text_main('[-]Error in Length of Path! Cut title!')
            path = path.replace(title, title[0:70])
        path = success_folder + '/' + path
        path = path.replace('--', '-').strip('-')
        if not os.path.exists(path):
            path = escapePath(path, config)
            os.makedirs(path)
        return path

    # ========================================================================从指定网站获取json_data
    def get_json_data(self, mode, number, config, appoint_url):
        if mode == 5:  # javdb模式
            self.add_text_main('[!]Please Wait Three Seconds！')
            time.sleep(3)
        json_data = getDataFromJSON(number, config, mode, appoint_url)
        return json_data

    # ========================================================================json_data添加到主界面（槽函数，在主线程执行）
    def _update_label_info_slot(self, json_data):
        try:
            self.Ui.label_number.setText(json_data['number'])
            self.Ui.label_release.setText(json_data['release'])
            self.Ui.label_director.setText(json_data['director'])
            self.Ui.label_label.setText(json_data['series'])
            self.Ui.label_studio.setText(json_data['studio'])
            self.Ui.label_publish.setText(json_data['publisher'])
            self.Ui.label_title.setText(json_data['title'])
            self.Ui.label_actor.setText(json_data['actor'])
            self.Ui.label_outline.setText(json_data['outline'])
            self.Ui.label_tag.setText(str(json_data['tag']).strip(" [',']").replace('\'', ''))
            if self.Ui.checkBox_cover.isChecked():
                poster_path = json_data.get('poster_path', '')
                thumb_path = json_data.get('thumb_path', '')
                if os.path.exists(poster_path):
                    pix = QPixmap(poster_path)
                    self.Ui.label_poster.setScaledContents(True)
                    self.Ui.label_poster.setPixmap(pix)  # 添加封面图
                if os.path.exists(thumb_path):
                    pix = QPixmap(thumb_path)
                    self.Ui.label_thumb.setScaledContents(True)
                    self.Ui.label_thumb.setPixmap(pix)  # 添加缩略图
        except Exception as error_info:
            self.add_text_main('[-]Error in _update_label_info_slot: ' + str(error_info))

    # ========================================================================json_data添加到主界面（线程安全）
    def add_label_info(self, json_data):
        try:
            # 使用信号机制确保在主线程更新 GUI
            self.labelInfoSignal.emit(json_data)
        except Exception as error_info:
            self.add_text_main('[-]Error in add_label_info: ' + str(error_info))

    # ========================================================================检查更新
    def UpdateCheck(self):
        if self.Ui.radioButton_update_on.isChecked():
            self.add_text_main('[!]Update Checking!')
            html2 = get_html('https://raw.githubusercontent.com/moyy996/AVDC/master/update_check.json')
            if html2 == 'ProxyError':
                return 'ProxyError'
            html = json.loads(str(html2))
            if float(self.version) < float(html['version']):
                self.add_text_main('[*]                  * New update ' + html['version'] + ' *')
                self.add_text_main('[*]                     ↓ Download ↓')
                self.add_text_main('[*] ' + html['download'])
            else:
                self.add_text_main('[!]No Newer Version Available!')
            self.add_text_main("[*]======================================================")
        return 'True'

    # ========================================================================新建失败输出文件夹
    def CreatFailedFolder(self, failed_folder):
        if self.Ui.radioButton_fail_move_on.isChecked() and not os.path.exists(failed_folder):
            try:
                os.makedirs(failed_folder + '/')
                self.add_text_main('[+]Created folder named ' + failed_folder + '!')
            except Exception as error_info:
                self.add_text_main('[-]Error in CreatFailedFolder: ' + str(error_info))

    # ========================================================================删除空目录
    def CEF(self, path):
        if os.path.exists(path):
            for root, dirs, files in os.walk(path):
                for dir in dirs:
                    try:
                        os.removedirs(root.replace('\\', '/') + '/' + dir)  # 删除这个空文件夹
                        self.add_text_main('[+]Deleting empty folder ' + root.replace('\\', '/') + '/' + dir)
                    except:
                        delete_empty_folder_failed = ''

    # ========================================================================生成刮削总结报告
    def generate_scrape_report(self):
        """生成刮削总结报告"""
        if not self.scrape_results:
            return
        
        total = len(self.scrape_results)
        success = sum(1 for r in self.scrape_results if r['status'] == 'success')
        incomplete = sum(1 for r in self.scrape_results if r['status'] == 'incomplete')
        failed = sum(1 for r in self.scrape_results if r['status'] == 'failed')
        
        # 统计重命名信息
        renamed_files = sum(1 for r in self.scrape_results if 'renamed_to' in r)
        renamed_folders = sum(1 for r in self.scrape_results if r.get('folder_renamed', False))
        
        self.add_text_main("")
        self.add_text_main("[*]==================== 刮削总结报告 ====================")
        self.add_text_main(f"[*] 总计: {total} | 成功: {success} | 不完整: {incomplete} | 失败: {failed}")
        if renamed_files > 0 or renamed_folders > 0:
            self.add_text_main(f"[*] 重命名: {renamed_files} 个文件, {renamed_folders} 个文件夹")
        self.add_text_main("[*]=====================================================")
        
        # 列出成功的文件（显示重命名信息）
        if success > 0:
            renamed_items = [r for r in self.scrape_results if r['status'] == 'success' and 'renamed_to' in r]
            if renamed_items:
                self.add_text_main("")
                self.add_text_main("[+] 以下文件已成功刮削并重命名：")
                for r in renamed_items:
                    # 显示文件重命名
                    self.add_text_main(f"    [+] 文件: {r.get('renamed_from', 'Unknown')} -> {r['renamed_to']}")
                    # 显示文件夹重命名（如果有）
                    if r.get('folder_renamed'):
                        self.add_text_main(f"        文件夹: {r.get('old_folder')} -> {r.get('new_folder')}")
                    self.add_text_main(f"        位置: {r['path']}")
                self.add_text_main("[*]-----------------------------------------------------")
        
        # 列出不完整的文件
        if incomplete > 0:
            self.add_text_main("")
            self.add_text_main("[!] 以下文件刮削不完整（缺少部分元数据）：")
            for r in self.scrape_results:
                if r['status'] == 'incomplete':
                    filename = os.path.basename(r['filepath'])
                    self.add_text_main(f"    [-] {filename}")
                    self.add_text_main(f"        位置: {r['path']}")
                    self.add_text_main(f"        命名: {r.get('naming_rule', 'N/A')}")
                    self.add_text_main(f"        缺失: {', '.join(r['missing_files'])}")
            self.add_text_main("[*]-----------------------------------------------------")
        
        # 列出失败的文件
        if failed > 0:
            self.add_text_main("")
            self.add_text_main("[!] 以下文件刮削失败：")
            for r in self.scrape_results:
                if r['status'] == 'failed':
                    filename = os.path.basename(r['filepath'])
                    self.add_text_main(f"    [-] {filename}")
                    self.add_text_main(f"        番号: {r.get('number', 'N/A')}")
                    self.add_text_main(f"        错误: {r['error_msg'][:100]}")  # 限制错误信息长度
            self.add_text_main("[*]-----------------------------------------------------")
        
        self.add_text_main("")
        self.add_text_main("[+] 提示：不完整的文件可以使用「单文件刮削」功能重新处理")
        self.add_text_main("[*]=====================================================")
        
        # 清空结果列表，为下次刮削做准备
        self.scrape_results = []
    
    # ========================================================================修复不完整刮削
    def fix_incomplete_scrape(self, filepath, path, naming_rule, json_data):
        """修复不完整的刮削（补全缺失的文件）"""
        config_file = 'config.ini'
        Config = ConfigParser()
        Config.read(config_file, encoding='UTF-8')
        
        failed_folder = ''  # 不需要移动失败文件
        thumb_path = path + '/' + naming_rule + '-thumb.jpg'
        poster_path = path + '/' + naming_rule + '-poster.jpg'
        fanart_path = path + '/' + naming_rule + '-fanart.jpg'
        
        self.add_text_main('[!]尝试修复不完整文件: ' + os.path.basename(filepath))
        
        # 检查并补全缺失的文件
        fixed = []
        
        # 检查 thumb
        if not os.path.exists(thumb_path) or os.path.getsize(thumb_path) < 1024:
            self.add_text_main('[!]尝试重新下载 thumb...')
            try:
                self.thumbDownload(json_data, path, naming_rule, Config, filepath, failed_folder)
                if os.path.exists(thumb_path) and os.path.getsize(thumb_path) > 1024:
                    fixed.append('thumb')
            except Exception as e:
                self.add_text_main('[-]thumb 修复失败: ' + str(e))
        
        # 检查 poster
        if not os.path.exists(poster_path) or os.path.getsize(poster_path) < 1024:
            self.add_text_main('[!]尝试重新生成 poster...')
            try:
                self.cutImage(json_data.get('imagecut', 1), path, naming_rule)
                if os.path.exists(poster_path) and os.path.getsize(poster_path) > 1024:
                    fixed.append('poster')
            except Exception as e:
                self.add_text_main('[-]poster 修复失败: ' + str(e))
        
        # 检查 fanart
        if not os.path.exists(fanart_path) or os.path.getsize(fanart_path) < 1024:
            self.add_text_main('[!]尝试重新生成 fanart...')
            try:
                self.copyRenameJpgToFanart(path, naming_rule)
                if os.path.exists(fanart_path) and os.path.getsize(fanart_path) > 1024:
                    fixed.append('fanart')
            except Exception as e:
                self.add_text_main('[-]fanart 修复失败: ' + str(e))
        
        if fixed:
            self.add_text_main('[+]修复完成，补全文件: ' + ', '.join(fixed))
        else:
            self.add_text_main('[-]未能修复任何文件')
        
        return fixed

    def Core_Main(self, filepath, number, mode, count, appoint_url=''):
        # =======================================================================初始化所需变量
        leak = 0
        uncensored = 0
        cn_sub = 0
        c_word = ''
        multi_part = 0
        part = ''
        program_mode = 0
        config_file = 'config.ini'
        Config = ConfigParser()
        Config.read(config_file, encoding='UTF-8')
        
        # 读取是否启用仅刮削模式（不移动文件）
        try:
            no_file_move = int(Config['common']['no_file_move'])
        except:
            no_file_move = 0
        
        if self.Ui.radioButton_common.isChecked():
            program_mode = 1
        elif self.Ui.radioButton_sort.isChecked():
            program_mode = 2
        
        # 如果启用仅刮削模式，显示提示
        if no_file_move == 1:
            self.add_text_main('[!]仅刮削模式 - 文件将保持在原目录，不移动任何文件')
        movie_path = self.Ui.lineEdit_movie_path.text()
        if movie_path == '':
            movie_path = os.getcwd().replace('\\', '/')
        failed_folder = movie_path + '/' + self.Ui.lineEdit_fail.text()  # 失败输出目录
        success_folder = movie_path + '/' + self.Ui.lineEdit_success.text()  # 成功输出目录
        # =======================================================================获取json_data
        json_data = self.get_json_data(mode, number, Config, appoint_url)
        
        # =======================================================================翻译功能（默认启用）
        try:
            translate_enabled = Config.getboolean('translate', 'enabled', fallback=True)
        except:
            translate_enabled = True
        
        if translate_enabled:
            try:
                from Function.translate import translate_movie_data
                self.add_text_main('[*]正在翻译影片数据为简体中文...')
                json_data = translate_movie_data(json_data)
                if json_data.get('title_translated') != json_data.get('title_original'):
                    title_trans = json_data.get('title_translated', '')
                self.add_text_main(f'[+]翻译完成')
            except Exception as e:
                self.add_text_main(f'[-]翻译失败: {str(e)[:100]}')
        
        # =======================================================================调试模式
        if self.Ui.radioButton_debug_on.isChecked():
            self.debug_mode(json_data)
        # =======================================================================是否找到影片信息
        if json_data['website'] == 'timeout':
            self.add_text_main('[-]Connect Failed! Please check your Proxy or Network!')
            return 'error'
        elif json_data['title'] == '':
            self.add_text_main('[-]Movie Data not found!')
            node = QTreeWidgetItem(self.item_fail)
            node.setText(0,
                         str(self.count_claw) + '-' + str(count) + '.' + os.path.splitext(filepath.split('/')[-1])[0])
            self.item_fail.addChild(node)
            # 仅在未启用仅刮削模式时移动失败文件
            if no_file_move == 0:
                self.moveFailedFolder(filepath, failed_folder)
            else:
                self.add_text_main('[!]仅刮削模式 - 刮削失败，文件保持不动')
            return 'not found'
        elif 'http' not in json_data['cover']:
            raise Exception('Cover Url is None!')
        elif json_data['imagecut'] == 3 and 'http' not in json_data['cover_small']:
            raise Exception('Cover_small Url is None!')
        # =======================================================================判断-C,-CD后缀,无码,流出
        if '-CD' in filepath or '-cd' in filepath:
            multi_part = 1
            part = self.get_part(filepath, failed_folder)
        if '-c.' in filepath or '-C.' in filepath or '中文' in filepath or '字幕' in filepath:
            cn_sub = 1
            c_word = '-C'  # 中文字幕影片后缀
        if json_data['imagecut'] == 3:  # imagecut=3为无码
            uncensored = 1
        if '流出' in os.path.split(filepath)[1]:
            leak = 1
        # =======================================================================创建输出文件夹
        if no_file_move == 1:
            # 仅刮削模式：元数据直接保存到视频所在目录（不创建子文件夹）
            path = os.path.dirname(filepath).replace('\\', '/')
            self.add_text_main('[+]Folder (仅刮削模式): ' + path)
        else:
            path = self.creatFolder(success_folder, json_data, Config)
            self.add_text_main('[+]Folder : ' + path)
        self.add_text_main('[+]From   : ' + json_data['website'])
        # =======================================================================文件命名规则
        number = json_data['number']
        naming_rule = str(self.get_naming_rule(json_data)).replace('--', '-').strip('-')
        if leak == 1:
            naming_rule += '-流出'
        if multi_part == 1:
            naming_rule += part
        if cn_sub == 1:
            naming_rule += c_word
        # =======================================================================封面路径
        thumb_path = path + '/' + naming_rule + '-thumb.jpg'
        poster_path = path + '/' + naming_rule + '-poster.jpg'
        fanart_path = path + '/' + naming_rule + '-fanart.jpg'
        nfo_path = path + '/' + naming_rule + '.nfo'
        # 初始化刮削结果记录
        scrape_result = {
            'filepath': filepath,
            'number': number,
            'naming_rule': naming_rule,
            'path': path,
            'status': 'processing',
            'missing_files': [],
            'error_msg': ''
        }
        # =======================================================================无码封面获取方式
        if json_data['imagecut'] == 3 and self.Ui.radioButton_poster_cut.isChecked():
            json_data['imagecut'] = 0
        # =======================================================================刮削模式
        if program_mode == 1:
            # imagecut 0 判断人脸位置裁剪缩略图为封面，1 裁剪右半面，3 下载小封面
            self.thumbDownload(json_data, path, naming_rule, Config, filepath, failed_folder)
            if self.Ui.checkBox_download_poster.isChecked():
                if self.smallCoverDownload(path, naming_rule, json_data, Config, filepath,
                                           failed_folder) == 'small_cover_error':  # 下载小封面
                    json_data['imagecut'] = 0
                self.cutImage(json_data['imagecut'], path, naming_rule)  # 裁剪图
                self.fix_size(path, naming_rule)
            if self.Ui.checkBox_download_fanart.isChecked():
                self.copyRenameJpgToFanart(path, naming_rule)
            self.deletethumb(path, naming_rule)
            
            # 下载演员头像
            self.downloadActorPhotos(json_data, path, Config)
            
            # 仅在未启用仅刮削模式时移动文件
            renamed_file = None
            renamed_folder = None
            if no_file_move == 0:
                if self.pasteFileToFolder(filepath, path, naming_rule, failed_folder):  # 移动文件,True 为有外挂字幕
                    cn_sub = 1
            else:
                # 仅刮削模式：先重命名文件，再重命名文件夹
                self.add_text_main('[*]仅刮削模式 - 开始重命名流程...')
                
                # 1. 先重命名文件
                renamed_file = self.renameFileOnly(filepath, naming_rule)
                if renamed_file:
                    scrape_result['renamed_from'] = os.path.basename(filepath)
                    scrape_result['renamed_to'] = os.path.basename(renamed_file)
                    filepath = renamed_file  # 更新文件路径
                    self.add_text_main(f'[*]文件已重命名为: {os.path.basename(renamed_file)}')
                else:
                    self.add_text_main('[!]文件重命名失败或无需重命名')
                
                # 2. 重命名文件夹（在文件重命名之后）
                old_folder = os.path.dirname(filepath)
                self.add_text_main(f'[*]准备重命名文件夹: {os.path.basename(old_folder)}')
                renamed_folder = self.renameFolderOnly(old_folder, json_data)
                if renamed_folder and renamed_folder != old_folder:
                    # 更新所有路径引用
                    path = renamed_folder.replace('\\', '/')
                    scrape_result['path'] = path
                    # 更新封面路径（因为文件夹变了）
                    thumb_path = path + '/' + naming_rule + '-thumb.jpg'
                    poster_path = path + '/' + naming_rule + '-poster.jpg'
                    fanart_path = path + '/' + naming_rule + '-fanart.jpg'
                    nfo_path = path + '/' + naming_rule + '.nfo'
                    scrape_result['folder_renamed'] = True
                    scrape_result['old_folder'] = os.path.basename(old_folder)
                    scrape_result['new_folder'] = os.path.basename(renamed_folder)
                    self.add_text_main(f'[*]文件夹已重命名为: {os.path.basename(renamed_folder)}')
                    self.add_text_main(f'[*]新完整路径: {path}')
                else:
                    self.add_text_main('[!]文件夹重命名失败或无需重命名')
                
            if self.Ui.checkBox_download_nfo.isChecked():
                self.PrintFiles(path, naming_rule, cn_sub, leak, json_data, filepath, failed_folder)  # 打印文件
            if self.Ui.radioButton_extrafanart_download_on.isChecked():
                self.extrafanartDownload(json_data, path, Config, filepath, failed_folder)
            self.add_mark(poster_path, thumb_path, cn_sub, leak, uncensored, Config)
        # =======================================================================整理模式
        elif program_mode == 2:
            # 仅在未启用仅刮削模式时移动文件
            if no_file_move == 0:
                self.pasteFileToFolder(filepath, path, naming_rule, failed_folder)  # 移动文件
        # =======================================================================检查文件完整性
        missing_files = []
        if not os.path.exists(thumb_path) or os.path.getsize(thumb_path) == 0:
            missing_files.append('thumb')
        if self.Ui.checkBox_download_poster.isChecked() and (not os.path.exists(poster_path) or os.path.getsize(poster_path) == 0):
            missing_files.append('poster')
        if self.Ui.checkBox_download_fanart.isChecked() and (not os.path.exists(fanart_path) or os.path.getsize(fanart_path) == 0):
            missing_files.append('fanart')
        if self.Ui.checkBox_download_nfo.isChecked() and (not os.path.exists(nfo_path) or os.path.getsize(nfo_path) == 0):
            missing_files.append('nfo')
        
        # 记录刮削结果
        scrape_result['missing_files'] = missing_files
        if missing_files:
            scrape_result['status'] = 'incomplete'
            scrape_result['error_msg'] = 'Missing: ' + ', '.join(missing_files)
            self.add_text_main('[!]Warning: Missing files - ' + ', '.join(missing_files))
        else:
            scrape_result['status'] = 'success'
        self.scrape_results.append(scrape_result)
        
        # =======================================================================json添加封面项
        json_data['thumb_path'] = thumb_path
        json_data['poster_path'] = poster_path
        json_data['number'] = number
        self.add_label_info(json_data)
        self.json_array[str(self.count_claw) + '-' + str(count)] = json_data
        return part + c_word

    def AVDC_Main(self):
        # =======================================================================初始化所需变量
        os.chdir(os.getcwd())
        config_file = 'config.ini'
        config = ConfigParser()
        config.read(config_file, encoding='UTF-8')
        
        # 读取是否启用仅刮削模式
        try:
            no_file_move = int(config['common']['no_file_move'])
        except:
            no_file_move = 0
        
        movie_path = self.Ui.lineEdit_movie_path.text()
        if movie_path == '':
            movie_path = os.getcwd().replace('\\', '/')
        failed_folder = movie_path + '/' + self.Ui.lineEdit_fail.text()  # 失败输出目录
        escape_folder = self.Ui.lineEdit_escape_dir.text()  # 多级目录刮削需要排除的目录
        mode = self.Ui.comboBox_website_all.currentIndex() + 1
        movie_type = self.Ui.lineEdit_movie_type.text()
        escape_string = self.Ui.lineEdit_escape_string.text()
        # =======================================================================检测更新,判断网络情况,新建failed目录,获取影片列表
        if self.UpdateCheck() == 'ProxyError':
            self.add_text_main('[-]Connect Failed! Please check your Proxy or Network!')
            self.Ui.pushButton_start_cap.setEnabled(True)
            self.add_text_main("[*]======================================================")
            return
        
        # 仅在未启用仅刮削模式时创建失败文件夹
        if self.Ui.radioButton_fail_move_on.isChecked() and no_file_move == 0:
            self.CreatFailedFolder(failed_folder)  # 新建failed文件夹
        elif no_file_move == 1:
            self.add_text_main('[!]仅刮削模式已启用 - 文件将保持在原目录')
        movie_list = movie_lists(escape_folder, movie_type, movie_path)  # 获取所有需要刮削的影片列表
        count = 0
        count_all = str(len(movie_list))
        self.add_text_main('[+]Find ' + count_all + ' movies')
        if count_all == 0:
            self.progressBarValue.emit(int(100))
        if config['common']['soft_link'] == '1':
            self.add_text_main('[!] --- Soft link mode is ENABLE! ----')
        # =======================================================================遍历电影列表 交给core处理
        for movie in movie_list:  # 遍历电影列表 交给core处理
            count += 1
            self.Ui.label_progress.setText('当前: ' + str(count) + '/' + str(count_all))
            percentage = str(count / int(count_all) * 100)[:4] + '%'
            value = int(count / int(count_all) * 100)
            self.add_text_main(
                '[!] - ' + str(self.count_claw) + ' - ' + percentage + ' - [' + str(count) + '/' + count_all + '] -')
            try:
                movie_number = getNumber(movie, escape_string)
                self.add_text_main("[!]Making Data for   [" + movie + "], the number is [" + movie_number + "]")
                result = self.Core_Main(movie, movie_number, mode, count)
                if result != 'not found' and movie_number != '' and result != 'error':
                    node = QTreeWidgetItem(self.item_succ)
                    node.setText(0, str(self.count_claw) + '-' + str(count) + '.' + movie_number + result)
                    self.item_succ.addChild(node)
                elif result == 'error':
                    break
                self.add_text_main("[*]======================================================")
            except Exception as error_info:
                node = QTreeWidgetItem(self.item_fail)
                node.setText(0,
                             str(self.count_claw) + '-' + str(count) + '.' + os.path.splitext(movie.split('/')[-1])[0])
                self.item_fail.addChild(node)
                error_msg = str(error_info)
                self.add_text_main('[-]Error in AVDC_Main: ' + error_msg)
                # 记录失败结果
                self.scrape_results.append({
                    'filepath': movie,
                    'number': movie_number if 'movie_number' in locals() else '',
                    'naming_rule': '',
                    'path': '',
                    'status': 'failed',
                    'missing_files': [],
                    'error_msg': error_msg
                })
                # 仅在未启用仅刮削模式且启用失败移动时移动文件
                if no_file_move == 0 and self.Ui.radioButton_fail_move_on.isChecked() and not os.path.exists(
                        failed_folder + '/' + os.path.split(movie)[1]):
                    if config['common']['soft_link'] == '0':
                        try:
                            shutil.move(movie, failed_folder + '/')
                            self.add_text_main('[-]Move ' + movie + ' to failed folder')
                        except shutil.Error as error_info:
                            self.add_text_main('[-]Error in AVDC_Main: ' + str(error_info))
                elif no_file_move == 1:
                    self.add_text_main('[!]仅刮削模式 - 错误发生时文件保持不动')
                self.add_text_main("[*]======================================================")
            self.progressBarValue.emit(int(value))
        self.Ui.pushButton_start_cap.setEnabled(True)
        self.CEF(movie_path)
        # 输出刮削总结报告
        self.generate_scrape_report()
        self.add_text_main("[+]All finished!!!")
        self.add_text_main("[*]======================================================")

    # ========================================================================清理影片目录
    def cleanup_movie_directory(self, movie_dir, movie_name):
        """清理单个影片目录下的旧文件和文件夹"""
        import shutil
        
        cleaned = []
        
        # 删除 NFO 文件（所有 nfo 文件）
        for file in os.listdir(movie_dir):
            if file.lower().endswith('.nfo'):
                try:
                    os.remove(os.path.join(movie_dir, file))
                    cleaned.append(f'NFO:{file}')
                except:
                    pass
        
        # 删除旧的演员头像文件夹
        for folder in ['.actor', '.actors', 'actors', 'actor']:
            actor_path = os.path.join(movie_dir, folder)
            if os.path.exists(actor_path) and os.path.isdir(actor_path):
                try:
                    shutil.rmtree(actor_path)
                    cleaned.append(f'文件夹:{folder}')
                except:
                    pass
        
        # 删除 metadata 文件夹
        metadata_path = os.path.join(movie_dir, 'metadata')
        if os.path.exists(metadata_path) and os.path.isdir(metadata_path):
            try:
                shutil.rmtree(metadata_path)
                cleaned.append('文件夹:metadata')
            except:
                pass
        
        return cleaned

    # ========================================================================二次刮削功能（强制重新刮削所有）
    def rescrape_missing(self):
        """二次刮削：强制重新刮削所有影片（删除旧文件后重新生成）"""
        self.add_text_main("[*]==================== 强制重新刮削 ====================")
        self.add_text_main("[*] 此操作将删除所有旧NFO文件并重新生成")
        
        movie_path = self.Ui.lineEdit_movie_path.text()
        if movie_path == '':
            movie_path = os.getcwd().replace('\\', '/')
        
        movie_type = self.Ui.lineEdit_movie_type.text()
        escape_folder = self.Ui.lineEdit_escape_dir.text()
        
        # 获取所有影片
        movie_list = movie_lists(escape_folder, movie_type, movie_path)
        total = len(movie_list)
        
        if total == 0:
            self.add_text_main("[!] 未找到影片文件")
            return
        
        self.add_text_main(f"[*] 发现 {total} 个影片，准备重新刮削...")
        self.add_text_main("[*]======================================================")
        
        # 强制覆盖nfo文件
        config_file = 'config.ini'
        config = ConfigParser()
        config.read(config_file, encoding='UTF-8')
        original_overwrite = config.getboolean('file_download', 'overwrite_nfo', fallback=False)
        
        # 临时启用覆盖
        config.set('file_download', 'overwrite_nfo', '1')
        with open(config_file, 'w', encoding='UTF-8') as f:
            config.write(f)
        
        # 重新刮削所有影片
        count = 0
        for movie in movie_list:
            count += 1
            movie_dir = os.path.dirname(movie).replace('\\', '/')
            movie_name = os.path.splitext(os.path.basename(movie))[0]
            
            self.add_text_main(f"[*] [{count}/{total}] 处理: {movie_name}")
            
            # 清理该影片目录下的旧文件
            cleaned = self.cleanup_movie_directory(movie_dir, movie_name)
            if cleaned:
                self.add_text_main(f"    [清理] {', '.join(cleaned)}")
            
            try:
                # 执行刮削
                self.Core_Main(movie, str(os.path.splitext(os.path.basename(movie))[0]), 1, count)
                self.add_text_main(f"    [完成]")
            except Exception as e:
                self.add_text_main(f"    [失败] {str(e)}")
            
            self.add_text_main("[*]------------------------------------------------------")
        
        # 恢复原始覆盖设置
        config.set('file_download', 'overwrite_nfo', str(int(original_overwrite)))
        with open(config_file, 'w', encoding='UTF-8') as f:
            config.write(f)
        
        self.add_text_main("[+] 强制重新刮削完成!")
        self.add_text_main("[*]======================================================")


if __name__ == '__main__':
    '''
    主函数
    '''
    app = QApplication(sys.argv)
    ui = MyMAinWindow()
    ui.show()
    sys.exit(app.exec_())
