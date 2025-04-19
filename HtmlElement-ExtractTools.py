import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget,
                              QPushButton, QTextEdit, QLabel, QFileDialog,
                              QMessageBox, QComboBox, QLineEdit, QCheckBox,
                              QRadioButton, QButtonGroup, QHBoxLayout,
                              QGroupBox, QSpacerItem, QSizePolicy)
from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtGui import QFont
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import pyperclip
import os

class SeleniumWorker(QThread):
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, chrome_path, driver_path, url, element_type, element_name):
        super().__init__()
        self.chrome_path = chrome_path
        self.driver_path = driver_path
        self.url = url
        self.element_type = element_type
        self.element_name = element_name

    def run(self):
        try:
            chrome_options = Options()
            chrome_options.binary_location = self.chrome_path
            chrome_options.add_argument("--headless")

            service = Service(self.driver_path)
            driver = webdriver.Chrome(service=service, options=chrome_options)

            driver.get(self.url)
            if self.element_type == "class_name":
                form = driver.find_element(By.CLASS_NAME, self.element_name)
            elif self.element_type == "id":
                form = driver.find_element(By.ID, self.element_name)

            form_html = form.get_attribute('outerHTML')
            driver.quit()
            self.finished.emit(form_html)

        except Exception as e:
            self.error.emit(str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HTML元素提取工具")
        self.setGeometry(100, 100, 900, 700)

        # 设置主窗口样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QGroupBox {
                border: 1px solid #ccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                text-align: center;
                text-decoration: none;
                font-size: 14px;
                margin: 4px 2px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
            QTextEdit, QLineEdit, QComboBox {
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 5px;
            }
        """)

        # 主部件和布局
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # 创建分组框
        path_group = QGroupBox("浏览器路径设置")
        url_group = QGroupBox("目标设置")
        save_group = QGroupBox("保存选项")
        result_group = QGroupBox("结果")
        info_group = QGroupBox("关于")

        # 路径设置组
        path_layout = QVBoxLayout()

        # Chrome路径
        chrome_layout = QHBoxLayout()
        self.chrome_label = QLabel("Chrome.exe文件路径:")
        self.chrome_input = QTextEdit()
        self.chrome_input.setMaximumHeight(30)
        self.chrome_input.setText(r"D:\chrome-win64\chrome.exe")
        self.browse_chrome_btn = QPushButton("浏览")
        chrome_layout.addWidget(self.chrome_label)
        chrome_layout.addWidget(self.chrome_input)
        chrome_layout.addWidget(self.browse_chrome_btn)

        # Driver路径
        driver_layout = QHBoxLayout()
        self.driver_label = QLabel("ChromeDriver路径:")
        self.driver_input = QTextEdit()
        self.driver_input.setMaximumHeight(30)
        self.driver_input.setText(r"D:\chrome-win64\chromedriver.exe")
        self.browse_driver_btn = QPushButton("浏览")
        driver_layout.addWidget(self.driver_label)
        driver_layout.addWidget(self.driver_input)
        driver_layout.addWidget(self.browse_driver_btn)

        path_layout.addLayout(chrome_layout)
        path_layout.addLayout(driver_layout)
        path_group.setLayout(path_layout)

        # 目标设置组
        url_layout = QVBoxLayout()

        # URL
        url_row = QHBoxLayout()
        self.url_label = QLabel("目标URL:")
        self.url_input = QTextEdit()
        self.url_input.setMaximumHeight(30)
        self.url_input.setText("https://xn--5nqs58m.xn--5brr03o.top/login.html")
        url_row.addWidget(self.url_label)
        url_row.addWidget(self.url_input)

        # 元素设置
        element_row = QHBoxLayout()
        self.element_type_label = QLabel("元素类型:")
        self.element_type_combo = QComboBox()
        self.element_type_combo.addItems(["class_name", "id"])
        self.element_type_combo.setCurrentText("class_name")

        self.element_name_label = QLabel("元素名称:")
        self.element_name_input = QLineEdit()
        self.element_name_input.setText("login-form")

        element_row.addWidget(self.element_type_label)
        element_row.addWidget(self.element_type_combo)
        element_row.addWidget(self.element_name_label)
        element_row.addWidget(self.element_name_input)

        url_layout.addLayout(url_row)
        url_layout.addLayout(element_row)
        url_group.setLayout(url_layout)

        # 保存选项组
        save_layout = QVBoxLayout()

        self.save_checkbox = QCheckBox("保存为txt文件")
        self.save_checkbox.setChecked(True)
        self.save_checkbox.stateChanged.connect(self.toggle_save_options)

        self.default_path_radio = QRadioButton("默认路径 (D:\\Download)")
        self.default_path_radio.setChecked(True)

        self.custom_path_radio = QRadioButton("自定义路径")
        self.custom_path_input = QLineEdit()
        self.custom_path_input.setEnabled(False)

        self.browse_custom_path_btn = QPushButton("浏览路径")
        self.browse_custom_path_btn.setEnabled(False)
        self.browse_custom_path_btn.clicked.connect(self.browse_custom_path)

        self.button_group = QButtonGroup()
        self.button_group.addButton(self.default_path_radio)
        self.button_group.addButton(self.custom_path_radio)
        self.button_group.buttonClicked.connect(self.on_radio_button_clicked)

        save_layout.addWidget(self.save_checkbox)
        save_layout.addWidget(self.default_path_radio)
        save_layout.addWidget(self.custom_path_radio)

        custom_path_layout = QHBoxLayout()
        custom_path_layout.addWidget(self.custom_path_input)
        custom_path_layout.addWidget(self.browse_custom_path_btn)
        save_layout.addLayout(custom_path_layout)
        save_group.setLayout(save_layout)

        # 结果组
        result_layout = QVBoxLayout()
        self.result_label = QLabel("表单HTML结果:")
        self.result_output = QTextEdit()
        self.result_output.setReadOnly(True)

        button_layout = QHBoxLayout()
        self.run_btn = QPushButton("提取表单HTML")
        self.run_btn.clicked.connect(self.run_selenium)

        self.copy_btn = QPushButton("复制到剪贴板")
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        self.copy_btn.setEnabled(False)

        self.save_btn = QPushButton("保存到文件")
        self.save_btn.clicked.connect(self.save_to_file)
        self.save_btn.setEnabled(False)

        button_layout.addWidget(self.run_btn)
        button_layout.addWidget(self.copy_btn)
        button_layout.addWidget(self.save_btn)

        result_layout.addWidget(self.result_label)
        result_layout.addWidget(self.result_output)
        result_layout.addLayout(button_layout)
        result_group.setLayout(result_layout)

        # 关于组
        info_layout = QVBoxLayout()
        info_label = QLabel("""
            <p style='font-size:12px; color:#666;'>
            <b>HTML元素提取工具 v1.0</b><br>
            开源地址: <a href='https://github.com/LACSTUDIO/HtmlElement-ExtractTools'>GitHub</a><br>
            </p>
        """)
        info_label.setOpenExternalLinks(True)
        info_label.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(info_label)
        info_group.setLayout(info_layout)

        # 添加到主布局
        main_layout.addWidget(path_group)
        main_layout.addWidget(url_group)
        main_layout.addWidget(save_group)
        main_layout.addWidget(result_group)
        main_layout.addWidget(info_group)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # 连接按钮信号
        self.browse_chrome_btn.clicked.connect(self.browse_chrome)
        self.browse_driver_btn.clicked.connect(self.browse_driver)

        # 存储结果
        self.current_html = ""

    def browse_chrome(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择Chrome可执行文件", "", "Executable Files (*.exe)")
        if path:
            self.chrome_input.setText(path)

    def browse_driver(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择ChromeDriver", "", "Executable Files (*.exe)")
        if path:
            self.driver_input.setText(path)

    def run_selenium(self):
        chrome_path = self.chrome_input.toPlainText()
        driver_path = self.driver_input.toPlainText()
        url = self.url_input.toPlainText()
        element_type = self.element_type_combo.currentText()
        element_name = self.element_name_input.text()

        if not chrome_path or not driver_path or not url or not element_name:
            QMessageBox.warning(self, "警告", "请填写所有字段")
            return

        self.run_btn.setEnabled(False)
        self.run_btn.setText("正在提取...")

        self.worker = SeleniumWorker(chrome_path, driver_path, url, element_type, element_name)
        self.worker.finished.connect(self.on_success)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def on_success(self, html):
        self.current_html = html
        self.result_output.setPlainText(html)
        self.run_btn.setEnabled(True)
        self.run_btn.setText("提取表单HTML")
        self.copy_btn.setEnabled(True)
        self.save_btn.setEnabled(True)
        QMessageBox.information(self, "成功", "表单HTML提取成功!")

    def on_error(self, error_msg):
        self.run_btn.setEnabled(True)
        self.run_btn.setText("提取表单HTML")
        QMessageBox.critical(self, "错误", f"发生错误:\n{error_msg}")

    def copy_to_clipboard(self):
        if self.current_html:
            pyperclip.copy(self.current_html)
            QMessageBox.information(self, "成功", "HTML内容已复制到剪贴板")

    def save_to_file(self):
        if not self.current_html:
            return

        if self.save_checkbox.isChecked():
            if self.default_path_radio.isChecked():
                path = os.path.join("D:\\", "Download", "form.txt")
            elif self.custom_path_radio.isChecked():
                path = os.path.join(self.custom_path_input.text(), "form.html")
            else:
                path, _ = QFileDialog.getSaveFileName(self, "保存HTML文件", "", "Text Files (*.txt)")
            if path:
                try:
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(self.current_html)
                    QMessageBox.information(self, "成功", f"文件已保存到:\n{path}")
                except Exception as e:
                    QMessageBox.critical(self, "错误", f"保存文件时出错:\n{str(e)}")

    def toggle_save_options(self):
        if self.save_checkbox.isChecked():
            self.default_path_radio.setEnabled(True)
            self.custom_path_radio.setEnabled(True)
            self.browse_custom_path_btn.setEnabled(True)
        else:
            self.default_path_radio.setEnabled(False)
            self.custom_path_radio.setEnabled(False)
            self.custom_path_input.setEnabled(False)
            self.browse_custom_path_btn.setEnabled(False)

    def on_radio_button_clicked(self, button):
        if button == self.custom_path_radio:
            self.custom_path_input.setEnabled(True)
        else:
            self.custom_path_input.setEnabled(False)

    def browse_custom_path(self):
        path = QFileDialog.getExistingDirectory(self, "选择保存路径", "")
        if path:
            self.custom_path_input.setText(path)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
