import sys
import requests
import json
import threading
import os
from PyQt5 import QtWidgets, QtCore, QtGui


class ChatApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.conversation_history = []
        self.is_waiting_for_response = False
        self.gradient_start_color = "#282C34"
        self.gradient_end_color = "#222830"

        self.theme_settings_file = "theme_settings.json"

        self.load_theme_settings()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("聊天 AI")
        self.setGeometry(100, 100, 800, 600)

        self.setStyleSheet(self.get_stylesheet())

        self.main_layout = QtWidgets.QHBoxLayout()

        self.sidebar = QtWidgets.QWidget(self)
        self.sidebar_layout = QtWidgets.QVBoxLayout(self.sidebar)
        self.chat_list = QtWidgets.QListWidget(self)
        self.chat_list.setStyleSheet("""
            background-color: #1E1E1E;
            color: white;
            border-radius: 10px;
            font-size: 14px;
            padding: 10px;
        """)
        self.chat_list.itemDoubleClicked.connect(self.load_selected_chat_history)
        self.chat_list.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.chat_list.customContextMenuRequested.connect(self.show_context_menu)
        self.sidebar_layout.addWidget(self.chat_list)

        self.chat_area = QtWidgets.QWidget(self)
        self.chat_area_layout = QtWidgets.QVBoxLayout(self.chat_area)

        self.new_chat_button = QtWidgets.QPushButton("新建聊天", self.chat_area)
        self.new_chat_button.setStyleSheet("""
            background-color: #6C757D;
            color: white;
            border-radius: 20px;
            padding: 12px;
            font-size: 14px;
            margin: 10px;
        """)
        self.new_chat_button.clicked.connect(self.new_chat)
        self.chat_area_layout.addWidget(self.new_chat_button)

        self.text_edit = QtWidgets.QTextEdit(self.chat_area)
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet("""
            background-color: #1E1E1E;
            color: white;
            border-radius: 10px;
            font-size: 16px;
            padding: 15px;
            line-height: 1.5;
        """)

        # 禁用滚动条
        self.text_edit.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.text_edit.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self.chat_area_layout.addWidget(self.text_edit)

        self.input_layout = QtWidgets.QHBoxLayout()
        self.input_edit = QtWidgets.QLineEdit(self.chat_area)
        self.input_edit.setStyleSheet("""
            background-color: #33373D;
            color: lime;
            border-radius: 20px;
            padding: 12px;
            font-size: 14px;
            margin: 10px;
        """)
        self.input_edit.returnPressed.connect(self.send_message)
        self.input_layout.addWidget(self.input_edit)

        self.send_button = QtWidgets.QPushButton("发送", self.chat_area)
        self.send_button.setStyleSheet("""
            background-color: #007ACC;
            color: white;
            border-radius: 20px;
            padding: 12px;
            font-size: 14px;
            margin: 10px;
        """)
        self.send_button.clicked.connect(self.send_message)
        self.input_layout.addWidget(self.send_button)

        self.chat_area_layout.addLayout(self.input_layout)

        self.button_layout = QtWidgets.QHBoxLayout()
        self.save_button = QtWidgets.QPushButton("保存聊天记录", self.chat_area)
        self.save_button.setStyleSheet("""
            background-color: #28a745;
            color: white;
            border-radius: 20px;
            padding: 12px;
            font-size: 14px;
            margin: 10px;
        """)
        self.save_button.clicked.connect(self.save_chat_history)
        self.button_layout.addWidget(self.save_button)

        self.theme_button = QtWidgets.QPushButton("设置主题", self.chat_area)
        self.theme_button.setStyleSheet("""
           background-color: #6C757D;
            color: white;
            border-radius: 20px;
            padding: 12px;
            font-size: 14px;
            margin: 10px;
        """)
        self.theme_button.clicked.connect(self.open_theme_dialog)
        self.button_layout.addWidget(self.theme_button)
        self.theme_button.setFixedWidth(self.send_button.width())

        self.chat_area_layout.addLayout(self.button_layout)

        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.splitter.addWidget(self.sidebar)
        self.splitter.addWidget(self.chat_area)
        self.splitter.setStretchFactor(1, 1)

        self.main_layout.addWidget(self.splitter)

        self.setLayout(self.main_layout)

        self.chat_record_directory = "chat_records"
        self.load_chat_records_from_directory()

    def load_theme_settings(self):
        if os.path.exists(self.theme_settings_file):
            with open(self.theme_settings_file, 'r', encoding='utf-8') as f:
                theme_data = json.load(f)
                self.gradient_start_color = theme_data.get("start_color", self.gradient_start_color)
                self.gradient_end_color = theme_data.get("end_color", self.gradient_end_color)

    def save_theme_settings(self):
        theme_data = {
            "start_color": self.gradient_start_color,
            "end_color": self.gradient_end_color
        }
        with open(self.theme_settings_file, 'w', encoding='utf-8') as f:
            json.dump(theme_data, f, ensure_ascii=False, indent=4)

    def open_theme_dialog(self):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("主题设置")
        dialog.setGeometry(200, 200, 400, 300)
        dialog.setStyleSheet("""
            background-color: #1E1E1E;
            color: white;
        """)

        layout = QtWidgets.QVBoxLayout(dialog)

        self.start_color_button = QtWidgets.QPushButton("选择渐变起始色", dialog)
        self.start_color_button.setStyleSheet("""
            background-color: #33373D;
            color: lime;
            border-radius: 20px;
            padding: 12px;
            font-size: 14px;
            margin: 10px;
        """)
        self.start_color_button.clicked.connect(self.select_start_color)
        layout.addWidget(self.start_color_button)

        self.end_color_button = QtWidgets.QPushButton("选择渐变终止色", dialog)
        self.end_color_button.setStyleSheet("""
            background-color: #33373D;
            color: lime;
            border-radius: 20px;
            padding: 12px;
            font-size: 14px;
            margin: 10px;
        """)
        self.end_color_button.clicked.connect(self.select_end_color)
        layout.addWidget(self.end_color_button)

        apply_button = QtWidgets.QPushButton("应用", dialog)
        apply_button.setStyleSheet("""
            background-color: #28a745;
            color: white;
            border-radius: 20px;
            padding: 12px;
            font-size: 14px;
            margin: 10px;
        """)
        apply_button.clicked.connect(self.apply_theme)
        layout.addWidget(apply_button)

        dialog.exec_()

    def select_start_color(self):
        color = QtWidgets.QColorDialog.getColor(QtGui.QColor(self.gradient_start_color), self)
        if color.isValid():
            self.gradient_start_color = color.name()

    def select_end_color(self):
        color = QtWidgets.QColorDialog.getColor(QtGui.QColor(self.gradient_end_color), self)
        if color.isValid():
            self.gradient_end_color = color.name()

    def apply_theme(self):
        self.setStyleSheet(self.get_stylesheet())
        self.save_theme_settings()

    def get_stylesheet(self):
        return f"""
            background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 {self.gradient_start_color}, stop:1 {self.gradient_end_color});
            font-family: 'Segoe UI', Tahoma, sans-serif;
            color: white;
            border-radius: 10px;
        """

    def new_chat(self):
        self.conversation_history = []
        self.text_edit.clear()
        self.input_edit.clear()
        self.load_chat_records_from_directory()

        self.save_button.setEnabled(True)
        self.send_button.setEnabled(True)

    def load_chat_records_from_directory(self):
        self.chat_list.clear()
        if not os.path.exists(self.chat_record_directory):
            os.makedirs(self.chat_record_directory)

        files = [f for f in os.listdir(self.chat_record_directory) if f.endswith('.json')]

        for file in files:
            self.chat_list.addItem(file)

    def send_message(self):
        user_input = self.input_edit.text()

        if user_input.lower() in ['exit','退出']:
            QtCore.QCoreApplication.instance().quit()
            return

        self.send_button.setEnabled(False)
        self.text_edit.append(f"<font color='lime'>你：{user_input}</font>")
        self.input_edit.clear()

        self.is_waiting_for_response = True
        self.input_edit.setEnabled(False)
        self.save_button.setEnabled(False)

        threading.Thread(target=self.get_ai_response, args=(user_input,), daemon=True).start()

    def get_ai_response(self, user_input):
        response = self.interact_with_model(user_input)
        QtCore.QMetaObject.invokeMethod(self, "display_ai_response", QtCore.Q_ARG(str, response))

    @QtCore.pyqtSlot(str)
    def display_ai_response(self, response):
        self.text_edit.append(f"<font color='red'>AI：{response}</font>")
        self.is_waiting_for_response = False
        self.input_edit.setEnabled(True)
        self.save_button.setEnabled(True)
        self.send_button.setEnabled(True)

        cursor = self.text_edit.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        self.text_edit.setTextCursor(cursor)

    def interact_with_model(self, prompt):
        url = 'http://127.0.0.1:11434/v1/chat/completions'
        headers = {'Content-Type': 'application/json'}

        self.conversation_history.append({'role': 'user', 'content': prompt})

        data = {
            'model': 'llama3.1',
            'messages': self.conversation_history
        }

        response = requests.post(url, headers=headers, json=data)
        response_data = response.json()

        model_reply = response_data['choices'][0]['message']['content']
        self.conversation_history.append({'role': 'assistant', 'content': model_reply})

        return model_reply

    def save_chat_history(self):
        options = QtWidgets.QFileDialog.Options()
        file_name, _ = QtWidgets.QFileDialog.getSaveFileName(self, "保存聊天记录", "", "JSON文件 (*.json);;所有文件 (*)", options=options)
        if file_name:
            with open(file_name, 'w', encoding='utf-8') as f:
                json.dump(self.conversation_history, f, ensure_ascii=False, indent=4)
            self.load_chat_records_from_directory()

    def load_selected_chat_history(self, item):
        file_name = item.text()
        if file_name:
            with open(os.path.join(self.chat_record_directory, file_name), 'r', encoding='utf-8') as f:
                self.conversation_history = json.load(f)
                self.text_edit.clear()

                for entry in self.conversation_history:
                    role = "你" if entry['role'] == 'user' else "AI"
                    self.text_edit.append(f"<font color='{'lime' if entry['role'] == 'user' else 'red'}'>{role}：{entry['content']}</font>")

    def show_context_menu(self, pos):
        context_menu = QtWidgets.QMenu(self)
        rename_action = context_menu.addAction("重命名")
        delete_action = context_menu.addAction("删除")

        action = context_menu.exec_(self.chat_list.mapToGlobal(pos))

        if action == rename_action:
            self.rename_chat_history()
        elif action == delete_action:
            self.delete_chat_history()

    def rename_chat_history(self):
        item = self.chat_list.selectedItems()
        if item:
            old_name = item[0].text()
            new_name, ok = QtWidgets.QInputDialog.getText(self, "重命名", "请输入新的文件名", text=old_name)
            if ok and new_name:
                if not new_name.endswith('.json'):
                    new_name += '.json'
                os.rename(
                    os.path.join(self.chat_record_directory, old_name),
                    os.path.join(self.chat_record_directory, new_name)
                )
                self.load_chat_records_from_directory()

    def delete_chat_history(self):
        item = self.chat_list.selectedItems()
        if item:
            file_name = item[0].text()
            file_path = os.path.join(self.chat_record_directory, file_name)
            if os.path.exists(file_path):
                os.remove(file_path)
                self.load_chat_records_from_directory()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv) 
    chat_app = ChatApp()
    chat_app.show()
    sys.exit(app.exec_())
