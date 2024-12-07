import os
import json
from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

# Directory to store chat records
chat_record_directory = 'static/chat_records'
os.makedirs(chat_record_directory, exist_ok=True)

# Model interaction endpoint
def interact_with_model(prompt, conversation_history, model):
    url = 'http://127.0.0.1:11434/v1/chat/completions'
    headers = {'Content-Type': 'application/json'}

    # 更新会话记录，添加用户输入
    conversation_history.append({'role': 'user', 'content': prompt})

    data = {
        'model': model,  # 使用前端传递的模型名
        'messages': conversation_history
    }

    # 调用模型接口
    response = requests.post(url, headers=headers, json=data)
    response_data = response.json()

    # 获取模型的回应
    model_reply = response_data['choices'][0]['message']['content']

    # 如果模型的回答是代码，使用```符号包裹起来
    if "```" in model_reply:
        model_reply = "```\n" + model_reply + "\n```"

    # 更新会话记录，添加AI回应
    conversation_history.append({'role': 'assistant', 'content': model_reply})

    return model_reply



@app.route('/')
def index():
    # List saved chat records
    chat_files = [f for f in os.listdir(chat_record_directory) if f.endswith('.json')]
    return render_template('index.html', chat_files=chat_files)

@app.route('/get_ai_response', methods=['POST'])
def get_ai_response():
    user_input = request.json.get('user_input')
    conversation_history = request.json.get('conversation_history', [])
    model = request.json.get('model', 'llama3.1')  # 默认模型是 llama3.1

    # 调用模型交互函数
    response = interact_with_model(user_input, conversation_history, model)

    return jsonify({
        'response': response,
        'conversation_history': conversation_history
    })


@app.route('/save_chat', methods=['POST'])
def save_chat():
    chat_data = request.json
    chat_filename = chat_data['filename']
    conversation_history = chat_data['conversation_history']

    file_path = os.path.join(chat_record_directory, chat_filename)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(conversation_history, f, ensure_ascii=False, indent=4)

    return jsonify({'message': 'Chat saved successfully!'})

@app.route('/load_chat/<filename>')
def load_chat(filename):
    file_path = os.path.join(chat_record_directory, filename)
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            conversation_history = json.load(f)
        return jsonify({'conversation_history': conversation_history})
    return jsonify({'message': 'File not found!'}), 404

@app.route('/delete_chat/<filename>', methods=['DELETE'])
def delete_chat(filename):
    file_path = os.path.join(chat_record_directory, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        return jsonify({'message': f'聊天记录 {filename} 已删除！'})
    return jsonify({'message': '文件未找到！'}), 404

@app.route('/rename_chat/<filename>', methods=['POST'])
def rename_chat(filename):
    new_filename = request.json.get('new_filename')
    old_file_path = os.path.join(chat_record_directory, filename)
    new_file_path = os.path.join(chat_record_directory, new_filename)

    if os.path.exists(old_file_path):
        os.rename(old_file_path, new_file_path)
        return jsonify({'message': f'聊天记录 {filename} 已重命名为 {new_filename}！'})
    return jsonify({'message': '文件未找到！'}), 404

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)
