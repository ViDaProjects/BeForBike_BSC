# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'form.ui'
##
## Created by: Qt User Interface Compiler version 6.9.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel,
    QMainWindow, QPushButton, QSizePolicy, QStatusBar,
    QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1024, 600)
        MainWindow.setMinimumSize(QSize(1024, 600))
        MainWindow.setMaximumSize(QSize(1024, 600))
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout_2 = QVBoxLayout(self.centralwidget)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.frame = QFrame(self.centralwidget)
        self.frame.setObjectName(u"frame")
        self.frame.setMouseTracking(False)
        self.frame.setFrameShape(QFrame.Shape.NoFrame)
        self.frame.setFrameShadow(QFrame.Shadow.Raised)
        self.frame.setLineWidth(0)
        self.horizontalLayout_2 = QHBoxLayout(self.frame)
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.frame_5 = QFrame(self.frame)
        self.frame_5.setObjectName(u"frame_5")
        self.frame_5.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_5.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_11 = QHBoxLayout(self.frame_5)
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.label_20 = QLabel(self.frame_5)
        self.label_20.setObjectName(u"label_20")
        self.label_20.setMaximumSize(QSize(60, 16777215))
        self.label_20.setPixmap(QPixmap(u"icons/map-pin.svg"))
        self.label_20.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_11.addWidget(self.label_20, 0, Qt.AlignmentFlag.AlignLeft)

        self.label_26 = QLabel(self.frame_5)
        self.label_26.setObjectName(u"label_26")
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        self.label_26.setFont(font)

        self.horizontalLayout_11.addWidget(self.label_26)

        self.label_19 = QLabel(self.frame_5)
        self.label_19.setObjectName(u"label_19")
        self.label_19.setMaximumSize(QSize(40, 16777215))
        font1 = QFont()
        font1.setPointSize(12)
        self.label_19.setFont(font1)
        self.label_19.setPixmap(QPixmap(u"icons/satellite-dish.png"))

        self.horizontalLayout_11.addWidget(self.label_19, 0, Qt.AlignmentFlag.AlignLeft)

        self.satellities_label = QLabel(self.frame_5)
        self.satellities_label.setObjectName(u"satellities_label")
        self.satellities_label.setMinimumSize(QSize(20, 0))
        self.satellities_label.setMaximumSize(QSize(20, 16777215))
        self.satellities_label.setFont(font1)

        self.horizontalLayout_11.addWidget(self.satellities_label)

        self.label_23 = QLabel(self.frame_5)
        self.label_23.setObjectName(u"label_23")
        self.label_23.setPixmap(QPixmap(u"icons/mobile.png"))

        self.horizontalLayout_11.addWidget(self.label_23)

        self.label_25 = QLabel(self.frame_5)
        self.label_25.setObjectName(u"label_25")
        self.label_25.setFont(font1)

        self.horizontalLayout_11.addWidget(self.label_25)

        self.fix_quality_label = QLabel(self.frame_5)
        self.fix_quality_label.setObjectName(u"fix_quality_label")
        self.fix_quality_label.setMinimumSize(QSize(20, 0))
        self.fix_quality_label.setFont(font1)

        self.horizontalLayout_11.addWidget(self.fix_quality_label)


        self.horizontalLayout_2.addWidget(self.frame_5, 0, Qt.AlignmentFlag.AlignLeft)

        self.frame_14 = QFrame(self.frame)
        self.frame_14.setObjectName(u"frame_14")
        self.frame_14.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_14.setFrameShadow(QFrame.Shadow.Plain)
        self.horizontalLayout_5 = QHBoxLayout(self.frame_14)
        self.horizontalLayout_5.setSpacing(0)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalLayout_5.setContentsMargins(-1, 0, 0, 0)
        self.date_label = QLabel(self.frame_14)
        self.date_label.setObjectName(u"date_label")
        font2 = QFont()
        font2.setPointSize(14)
        self.date_label.setFont(font2)
        self.date_label.setLineWidth(0)
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignHCenter|Qt.AlignmentFlag.AlignTop)
        self.date_label.setMargin(7)

        self.horizontalLayout_5.addWidget(self.date_label, 0, Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)

        self.time_label = QLabel(self.frame_14)
        self.time_label.setObjectName(u"time_label")
        self.time_label.setFont(font2)
        self.time_label.setMargin(7)

        self.horizontalLayout_5.addWidget(self.time_label, 0, Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)


        self.horizontalLayout_2.addWidget(self.frame_14)

        self.frame_13 = QFrame(self.frame)
        self.frame_13.setObjectName(u"frame_13")
        self.frame_13.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_13.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_4 = QHBoxLayout(self.frame_13)
        self.horizontalLayout_4.setSpacing(0)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.label_28 = QLabel(self.frame_13)
        self.label_28.setObjectName(u"label_28")
        self.label_28.setFont(font1)

        self.horizontalLayout_4.addWidget(self.label_28, 0, Qt.AlignmentFlag.AlignRight)

        self.app_bt_label = QLabel(self.frame_13)
        self.app_bt_label.setObjectName(u"app_bt_label")
        self.app_bt_label.setMinimumSize(QSize(50, 0))
        self.app_bt_label.setMaximumSize(QSize(60, 16777215))
        self.app_bt_label.setPixmap(QPixmap(u"icons/application.png"))
        self.app_bt_label.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.horizontalLayout_4.addWidget(self.app_bt_label, 0, Qt.AlignmentFlag.AlignRight)

        self.crank_bt_label = QLabel(self.frame_13)
        self.crank_bt_label.setObjectName(u"crank_bt_label")
        self.crank_bt_label.setMaximumSize(QSize(70, 16777215))
        self.crank_bt_label.setPixmap(QPixmap(u"icons/bicycle_big.png"))

        self.horizontalLayout_4.addWidget(self.crank_bt_label, 0, Qt.AlignmentFlag.AlignRight)


        self.horizontalLayout_2.addWidget(self.frame_13, 0, Qt.AlignmentFlag.AlignRight)


        self.verticalLayout_2.addWidget(self.frame)

        self.line = QFrame(self.centralwidget)
        self.line.setObjectName(u"line")
        self.line.setLineWidth(35)
        self.line.setFrameShape(QFrame.Shape.HLine)
        self.line.setFrameShadow(QFrame.Shadow.Sunken)

        self.verticalLayout_2.addWidget(self.line)

        self.frame_2 = QFrame(self.centralwidget)
        self.frame_2.setObjectName(u"frame_2")
        self.frame_2.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_2.setFrameShadow(QFrame.Shadow.Raised)
        self.frame_2.setLineWidth(0)
        self.horizontalLayout = QHBoxLayout(self.frame_2)
        self.horizontalLayout.setSpacing(0)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, -1)
        self.frame_3 = QFrame(self.frame_2)
        self.frame_3.setObjectName(u"frame_3")
        self.frame_3.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_3.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout = QVBoxLayout(self.frame_3)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 15, 0)
        self.frame_12 = QFrame(self.frame_3)
        self.frame_12.setObjectName(u"frame_12")
        self.frame_12.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_12.setFrameShadow(QFrame.Shadow.Raised)
        self.frame_12.setLineWidth(0)
        self.verticalLayout_3 = QVBoxLayout(self.frame_12)
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 20, 0, 10)
        self.label_18 = QLabel(self.frame_12)
        self.label_18.setObjectName(u"label_18")
        font3 = QFont()
        font3.setPointSize(40)
        font3.setBold(True)
        self.label_18.setFont(font3)
        self.label_18.setTextFormat(Qt.TextFormat.AutoText)
        self.label_18.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_18.setMargin(2)

        self.verticalLayout_3.addWidget(self.label_18)

        self.label_21 = QLabel(self.frame_12)
        self.label_21.setObjectName(u"label_21")
        self.label_21.setPixmap(QPixmap(u"icons/bike (2).png"))
        self.label_21.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_3.addWidget(self.label_21)


        self.verticalLayout.addWidget(self.frame_12)

        self.frame_6 = QFrame(self.frame_3)
        self.frame_6.setObjectName(u"frame_6")
        font4 = QFont()
        font4.setBold(True)
        font4.setUnderline(False)
        font4.setStrikeOut(False)
        font4.setKerning(True)
        self.frame_6.setFont(font4)
        self.frame_6.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_6.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_6 = QHBoxLayout(self.frame_6)
        self.horizontalLayout_6.setSpacing(0)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel(self.frame_6)
        self.label.setObjectName(u"label")
        font5 = QFont()
        font5.setPointSize(13)
        font5.setBold(True)
        font5.setUnderline(False)
        font5.setStrikeOut(False)
        font5.setKerning(True)
        self.label.setFont(font5)

        self.horizontalLayout_6.addWidget(self.label)

        self.speed_label = QLabel(self.frame_6)
        self.speed_label.setObjectName(u"speed_label")
        font6 = QFont()
        font6.setPointSize(20)
        font6.setBold(True)
        font6.setUnderline(False)
        font6.setStrikeOut(False)
        font6.setKerning(True)
        self.speed_label.setFont(font6)

        self.horizontalLayout_6.addWidget(self.speed_label)


        self.verticalLayout.addWidget(self.frame_6)

        self.frame_7 = QFrame(self.frame_3)
        self.frame_7.setObjectName(u"frame_7")
        self.frame_7.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_7.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_7 = QHBoxLayout(self.frame_7)
        self.horizontalLayout_7.setSpacing(0)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.horizontalLayout_7.setContentsMargins(0, 0, 0, 0)
        self.label_3 = QLabel(self.frame_7)
        self.label_3.setObjectName(u"label_3")
        font7 = QFont()
        font7.setPointSize(13)
        self.label_3.setFont(font7)

        self.horizontalLayout_7.addWidget(self.label_3)

        self.distance_label = QLabel(self.frame_7)
        self.distance_label.setObjectName(u"distance_label")
        font8 = QFont()
        font8.setPointSize(20)
        self.distance_label.setFont(font8)

        self.horizontalLayout_7.addWidget(self.distance_label)


        self.verticalLayout.addWidget(self.frame_7)

        self.frame_8 = QFrame(self.frame_3)
        self.frame_8.setObjectName(u"frame_8")
        font9 = QFont()
        font9.setBold(True)
        self.frame_8.setFont(font9)
        self.frame_8.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_8.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_8 = QHBoxLayout(self.frame_8)
        self.horizontalLayout_8.setSpacing(0)
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.horizontalLayout_8.setContentsMargins(0, 0, 0, 0)
        self.label_5 = QLabel(self.frame_8)
        self.label_5.setObjectName(u"label_5")
        font10 = QFont()
        font10.setPointSize(13)
        font10.setBold(True)
        self.label_5.setFont(font10)

        self.horizontalLayout_8.addWidget(self.label_5)

        self.calories_label = QLabel(self.frame_8)
        self.calories_label.setObjectName(u"calories_label")
        font11 = QFont()
        font11.setPointSize(20)
        font11.setBold(True)
        self.calories_label.setFont(font11)

        self.horizontalLayout_8.addWidget(self.calories_label)


        self.verticalLayout.addWidget(self.frame_8)

        self.frame_9 = QFrame(self.frame_3)
        self.frame_9.setObjectName(u"frame_9")
        self.frame_9.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_9.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_9 = QHBoxLayout(self.frame_9)
        self.horizontalLayout_9.setSpacing(0)
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.horizontalLayout_9.setContentsMargins(0, 0, 0, 0)
        self.label_7 = QLabel(self.frame_9)
        self.label_7.setObjectName(u"label_7")
        self.label_7.setFont(font7)

        self.horizontalLayout_9.addWidget(self.label_7)

        self.power_label = QLabel(self.frame_9)
        self.power_label.setObjectName(u"power_label")
        self.power_label.setFont(font8)

        self.horizontalLayout_9.addWidget(self.power_label)


        self.verticalLayout.addWidget(self.frame_9)

        self.frame_10 = QFrame(self.frame_3)
        self.frame_10.setObjectName(u"frame_10")
        self.frame_10.setFont(font9)
        self.frame_10.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_10.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_10 = QHBoxLayout(self.frame_10)
        self.horizontalLayout_10.setSpacing(0)
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.horizontalLayout_10.setContentsMargins(0, 0, 0, 0)
        self.label_9 = QLabel(self.frame_10)
        self.label_9.setObjectName(u"label_9")
        self.label_9.setFont(font10)

        self.horizontalLayout_10.addWidget(self.label_9)

        self.cadence_label = QLabel(self.frame_10)
        self.cadence_label.setObjectName(u"cadence_label")
        self.cadence_label.setFont(font11)

        self.horizontalLayout_10.addWidget(self.cadence_label)


        self.verticalLayout.addWidget(self.frame_10)

        self.frame_11 = QFrame(self.frame_3)
        self.frame_11.setObjectName(u"frame_11")
        self.frame_11.setFrameShape(QFrame.Shape.NoFrame)
        self.frame_11.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout_3 = QHBoxLayout(self.frame_11)
        self.horizontalLayout_3.setSpacing(0)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.label_11 = QLabel(self.frame_11)
        self.label_11.setObjectName(u"label_11")
        self.label_11.setFont(font7)

        self.horizontalLayout_3.addWidget(self.label_11)

        self.blinker_frame_left = QFrame(self.frame_11)
        self.blinker_frame_left.setObjectName(u"blinker_frame_left")
        self.blinker_frame_left.setFrameShape(QFrame.Shape.NoFrame)
        self.blinker_frame_left.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_5 = QVBoxLayout(self.blinker_frame_left)
        self.verticalLayout_5.setSpacing(0)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.verticalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.blinker_label_left = QLabel(self.blinker_frame_left)
        self.blinker_label_left.setObjectName(u"blinker_label_left")
        self.blinker_label_left.setPixmap(QPixmap(u"icons/arrow_left_off.svg"))
        self.blinker_label_left.setScaledContents(False)
        self.blinker_label_left.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.blinker_label_left.setWordWrap(False)

        self.verticalLayout_5.addWidget(self.blinker_label_left)


        self.horizontalLayout_3.addWidget(self.blinker_frame_left)

        self.blinker_frame_right = QFrame(self.frame_11)
        self.blinker_frame_right.setObjectName(u"blinker_frame_right")
        self.blinker_frame_right.setFrameShape(QFrame.Shape.NoFrame)
        self.blinker_frame_right.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_6 = QVBoxLayout(self.blinker_frame_right)
        self.verticalLayout_6.setSpacing(0)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.blinker_label_right = QLabel(self.blinker_frame_right)
        self.blinker_label_right.setObjectName(u"blinker_label_right")
        self.blinker_label_right.setLineWidth(4)
        self.blinker_label_right.setPixmap(QPixmap(u"icons/arrow_right_off.svg"))

        self.verticalLayout_6.addWidget(self.blinker_label_right)


        self.horizontalLayout_3.addWidget(self.blinker_frame_right)


        self.verticalLayout.addWidget(self.frame_11)


        self.horizontalLayout.addWidget(self.frame_3)

        self.line_2 = QFrame(self.frame_2)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setLineWidth(30)
        self.line_2.setFrameShape(QFrame.Shape.VLine)
        self.line_2.setFrameShadow(QFrame.Shadow.Sunken)

        self.horizontalLayout.addWidget(self.line_2)

        self.map_frame_original = QFrame(self.frame_2)
        self.map_frame_original.setObjectName(u"map_frame_original")
        self.map_frame_original.setMinimumSize(QSize(700, 500))
        self.map_frame_original.setFrameShape(QFrame.Shape.NoFrame)
        self.map_frame_original.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_4 = QVBoxLayout(self.map_frame_original)
        self.verticalLayout_4.setSpacing(0)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(25, 30, 25, 0)
        self.map_frame = QFrame(self.map_frame_original)
        self.map_frame.setObjectName(u"map_frame")
        self.map_frame.setMaximumSize(QSize(16777215, 350))
        self.map_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.map_frame.setFrameShadow(QFrame.Shadow.Raised)

        self.verticalLayout_4.addWidget(self.map_frame)

        self.start_button = QPushButton(self.map_frame_original)
        self.start_button.setObjectName(u"start_button")

        self.verticalLayout_4.addWidget(self.start_button)

        self.stop_button = QPushButton(self.map_frame_original)
        self.stop_button.setObjectName(u"stop_button")

        self.verticalLayout_4.addWidget(self.stop_button)


        self.horizontalLayout.addWidget(self.map_frame_original)


        self.verticalLayout_2.addWidget(self.frame_2)

        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.label_20.setText("")
        self.label_26.setText(QCoreApplication.translate("MainWindow", u"GPS", None))
        self.label_19.setText("")
        self.satellities_label.setText(QCoreApplication.translate("MainWindow", u"05", None))
        self.label_23.setText("")
        self.label_25.setText(QCoreApplication.translate("MainWindow", u"Fix quality:", None))
        self.fix_quality_label.setText(QCoreApplication.translate("MainWindow", u"1", None))
        self.date_label.setText(QCoreApplication.translate("MainWindow", u"16 out", None))
        self.time_label.setText(QCoreApplication.translate("MainWindow", u"13:05", None))
        self.label_28.setText(QCoreApplication.translate("MainWindow", u"Bluetooth conn", None))
        self.app_bt_label.setText("")
        self.crank_bt_label.setText("")
        self.label_18.setText(QCoreApplication.translate("MainWindow", u"Be For Bike", None))
        self.label_21.setText("")
        self.label.setText(QCoreApplication.translate("MainWindow", u"Speed:", None))
        self.speed_label.setText(QCoreApplication.translate("MainWindow", u"15 km/h", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"Distance:", None))
        self.distance_label.setText(QCoreApplication.translate("MainWindow", u"5000 m ", None))
        self.label_5.setText(QCoreApplication.translate("MainWindow", u"Calories:", None))
        self.calories_label.setText(QCoreApplication.translate("MainWindow", u"150 Kcal", None))
        self.label_7.setText(QCoreApplication.translate("MainWindow", u"Power:", None))
        self.power_label.setText(QCoreApplication.translate("MainWindow", u"130 W", None))
        self.label_9.setText(QCoreApplication.translate("MainWindow", u"Cadence: ", None))
        self.cadence_label.setText(QCoreApplication.translate("MainWindow", u"43 RPM", None))
        self.label_11.setText(QCoreApplication.translate("MainWindow", u"Blinker:", None))
        self.blinker_label_left.setText("")
        self.blinker_label_right.setText("")
        self.start_button.setText(QCoreApplication.translate("MainWindow", u"Start plotting", None))
        self.stop_button.setText(QCoreApplication.translate("MainWindow", u"Stop plotting", None))
    # retranslateUi

