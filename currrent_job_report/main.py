#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


import traceback


# Для отлова всех исключений, которые в слотах Qt могут "затеряться" и привести к тихому падению
def log_uncaught_exceptions(ex_cls, ex, tb):
    text = '{}: {}:\n'.format(ex_cls.__name__, ex)
    text += ''.join(traceback.format_tb(tb))

    print('Error: ', text)
    QMessageBox.critical(None, 'Error', text)
    quit()


import sys
sys.excepthook = log_uncaught_exceptions


import os.path
TRAY_ICON = os.path.join(os.path.dirname(__file__), 'favicon.ico')


import datetime

from get_user_and_deviation_hours import (
    get_user_and_deviation_hours, get_quarter_user_and_deviation_hours, get_quarter_num,
    NotFoundReport
)


from qtpy.QtWidgets import *
from qtpy.QtGui import *
from qtpy.QtCore import *


import time


class CheckJobReportThread(QThread):
    about_new_text = Signal(str)
    about_ok = Signal(bool)

    about_log = Signal(str)

    def __init__(self):
        super().__init__()

        self.last_text = None
        self.ok = None

    def run(self):
        def _get_title(deviation_hours):
            ok = deviation_hours[0] != '-'
            return 'Переработка' if ok else 'Недоработка'

        while True:
            try:
                today = datetime.datetime.today().strftime('%d/%m/%Y %H:%M:%S')
                self.about_log.emit('Check for {}'.format(today))

                text = ""
                deviation_hours = None
                quarter_deviation_hours = None

                try:
                    name, deviation_hours = get_user_and_deviation_hours()
                    ok = deviation_hours[0] != '-'
                    text += name + '\n\n' + _get_title(deviation_hours) + ' ' + deviation_hours

                except NotFoundReport:
                    text = "Отчет на сегодня еще не готов."
                    ok = True

                try:
                    _, quarter_deviation_hours = get_quarter_user_and_deviation_hours()
                    if quarter_deviation_hours.count(':') == 1:
                        quarter_deviation_hours += ":00"

                    text += "\n" + _get_title(quarter_deviation_hours) + ' за квартал ' + get_quarter_num() \
                            + " " + quarter_deviation_hours

                except NotFoundReport:
                    pass

                # Если часы за месяц не готовы, но часы за квартал есть
                if not deviation_hours and quarter_deviation_hours:
                    ok = True

                if self.last_text != text:
                    self.last_text = text

                    text = f"Обновлено {today}\n{self.last_text}"
                    self.about_new_text.emit(text)
                    self.about_log.emit("    " + self.last_text + "\n")
                else:
                    self.about_log.emit("    Ничего не изменилось\n")

                if self.ok != ok:
                    self.ok = ok
                    self.about_ok.emit(self.ok)

                time.sleep(3600)

            except Exception as e:
                self.about_log.emit("Error: " + str(e))
                self.about_log.emit("Wait 60 secs")
                time.sleep(60)


class JobReportWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.info = QLabel()
        self.ok = None

        self.quit_button = QToolButton()
        self.quit_button.setText('Quit')
        self.quit_button.setAutoRaise(True)
        self.quit_button.clicked.connect(QApplication.instance().quit)

        self.hide_button = QToolButton()
        self.hide_button.setText('Hide')
        self.hide_button.setAutoRaise(True)
        self.hide_button.clicked.connect(lambda x=None: self.parent().hide())

        self.log = QPlainTextEdit()
        self.log.setWindowTitle("Log")
        self.log.setMaximumBlockCount(500)
        self.log.hide()

        visible_log_button = QToolButton()
        visible_log_button.setToolTip("Show log")
        visible_log_button.setAutoRaise(True)
        visible_log_button.setText("+")
        visible_log_button.clicked.connect(self.log.show)

        layout = QVBoxLayout()
        layout.setSpacing(0)

        hlayout = QHBoxLayout()
        hlayout.addWidget(self.info)
        hlayout.addWidget(visible_log_button, alignment=Qt.AlignTop)
        layout.addLayout(hlayout)

        layout.addStretch()

        layout_buttons = QHBoxLayout()
        layout_buttons.addWidget(self.quit_button)
        layout_buttons.addStretch()
        layout_buttons.addWidget(self.hide_button)

        layout.addLayout(layout_buttons)

        self.setLayout(layout)

        self.thread = CheckJobReportThread()
        self.thread.about_new_text.connect(self.info.setText)
        self.thread.about_ok.connect(self._set_ok)
        self.thread.about_log.connect(self._add_log)
        self.thread.start()

    def _set_ok(self, val):
        self.ok = val
        self.update()

    def _add_log(self, val):
        print(val)
        self.log.appendPlainText(val)

    def paintEvent(self, event):
        super().paintEvent(event)

        color = QColor('#29AB87') if self.ok else QColor(255, 0, 0, 128)

        painter = QPainter(self)
        painter.setBrush(color)
        painter.setPen(color)
        painter.drawRect(self.rect())


# TODO: Нарисовать график
if __name__ == '__main__':
    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)

    tray = QSystemTrayIcon(QIcon(TRAY_ICON))

    job_report_widget = JobReportWidget()
    job_report_widget.setFixedSize(230, 130)
    job_report_widget_action = QWidgetAction(job_report_widget)
    job_report_widget_action.setDefaultWidget(job_report_widget)

    menu = QMenu()
    menu.addAction(job_report_widget_action)

    tray.setContextMenu(menu)
    tray.activated.connect(lambda x: menu.exec(tray.geometry().center()))

    tray.setToolTip('Compass Plus. Рапорт учета рабочего времени')
    tray.show()

    app.exec()
