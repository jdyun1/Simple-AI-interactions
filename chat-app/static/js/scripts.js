document.addEventListener('DOMContentLoaded', function () {
    let conversationHistory = [];
    const inputField = document.getElementById('input');
    const sendBtn = document.getElementById('send-btn');
    const messagesDiv = document.getElementById('messages');
    const saveBtn = document.getElementById('save-btn');
    const modelSwitchBtn = document.getElementById('model-switch-btn');
    const chatList = document.getElementById('chat-list');
    const newChatBtn = document.getElementById('new-chat-btn');

    let currentModel = 'llama3.1'; // Default model

    // Event listeners
    sendBtn.addEventListener('click', sendMessage);
    saveBtn.addEventListener('click', saveChatHistory);
    modelSwitchBtn.addEventListener('click', switchModel);
    newChatBtn.addEventListener('click', newChat);

    // Handle Enter key press for sending message
    inputField.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') {
            e.preventDefault();  // Prevent the default action (new line)
            sendMessage();
        }
    });

    // Event listeners for delete and rename buttons
    chatList.addEventListener('click', function (e) {
        const filename = e.target.getAttribute('data-filename');
        if (e.target.classList.contains('delete-btn')) {
            deleteChatRecord(filename);
        } else if (e.target.classList.contains('rename-btn')) {
            renameChatRecord(filename);
        }
    });

    // Function to handle new chat
    function newChat() {
        conversationHistory = [];
        messagesDiv.innerHTML = '';
        inputField.value = '';
    }

    // Function to send message
    function sendMessage() {
        const userInput = inputField.value.trim();
        if (!userInput) return;

        displayMessage('你', userInput, 'lime');
        inputField.value = '';

        fetch('/get_ai_response', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ user_input: userInput, conversation_history: conversationHistory, model: currentModel })
        })
        .then(response => response.json())
        .then(data => {
            conversationHistory = data.conversation_history;
            displayMessage('AI', data.response, 'red');
        });
    }

    // Function to display message
    function displayMessage(sender, message, color) {
        const msgElem = document.createElement('div');

        // Check if the message contains a code block (indicated by triple backticks "```")
        if (message.startsWith("```") && message.endsWith("```")) {
            message = message.slice(3, -3);  // Remove the "```" markers
            msgElem.innerHTML = `<div style="color:${color}">${sender}：<pre><code>${message}</code></pre></div>`;
        } else {
            msgElem.innerHTML = `<span style="color:${color}">${sender}：${message}</span>`;
        }

        messagesDiv.appendChild(msgElem);
        messagesDiv.scrollTop = messagesDiv.scrollHeight; // Scroll to bottom
    }

    // Function to save chat history
    function saveChatHistory() {
        const filename = prompt("请输入聊天记录文件名（不含扩展名）：") + '.json';
        fetch('/save_chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ filename, conversation_history: conversationHistory })
        })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
            location.reload(); // Reload the page to update the chat list
        });
    }

    // Function to delete chat record
    function deleteChatRecord(filename) {
        const confirmDelete = confirm("确认删除该聊天记录?");
        if (confirmDelete) {
            fetch(`/delete_chat/${filename}`, {
                method: 'DELETE'
            })
            .then(response => response.json())
            .then(data => {
                alert(data.message);
                location.reload(); // Reload the page to update the chat list
            });
        }
    }

    // Function to rename chat record
    function renameChatRecord(filename) {
        const newFilename = prompt("请输入新的文件名（不含扩展名）：", filename.replace('.json', '')) + '.json';
        if (newFilename) {
            fetch(`/rename_chat/${filename}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ new_filename: newFilename })
            })
            .then(response => response.json())
            .then(data => {
                alert(data.message);
                location.reload(); // Reload the page to update the chat list
            });
        }
    }

    // Load selected chat history
    chatList.addEventListener('click', function (e) {
        const filename = e.target.getAttribute('data-filename');
        if (filename) {
            fetch(`/load_chat/${filename}`)
                .then(response => response.json())
                .then(data => {
                    conversationHistory = data.conversation_history;
                    messagesDiv.innerHTML = '';
                    conversationHistory.forEach(entry => {
                        const sender = entry.role === 'user' ? '你' : 'AI';
                        const color = entry.role === 'user' ? 'lime' : 'red';
                        displayMessage(sender, entry.content, color);
                    });
                });
        }
    });

    // Function to switch model
    function switchModel() {
        const newModel = prompt("请输入要切换的模型（llama3.1/llama3.2/qwen2.5/qwen2.5-coder:14b）：");
        if (newModel === 'llama3.1' || newModel === 'qwen2.5' || newModel === 'llama3.2' || newModel === 'qwen2.5-coder:14b') {
            currentModel = newModel;
            alert(`当前模型已切换为 ${currentModel}`);
        } else {
            alert("无效的模型选择，请选择 llama3.1 或 qwen2.5");
        }
    }
});
