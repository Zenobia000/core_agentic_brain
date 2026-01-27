// web/static/app.js
document.addEventListener('DOMContentLoaded', () => {
    const statusLight = document.getElementById('status-light');
    const statusText = document.getElementById('status-text');
    const logsContainer = document.getElementById('logs');
    const taskInput = document.getElementById('task-input');
    const sendButton = document.getElementById('send-button');

    let socket;

    function connect() {
        // Use wss:// for secure connections (https)
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        socket = new WebSocket(wsUrl);

        socket.onopen = () => {
            updateStatus('connected', 'Connected');
            addLog('system', 'Connection established. Ready to receive tasks.');
            sendButton.disabled = false;
        };

        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            handleSocketMessage(data);
        };

        socket.onclose = () => {
            updateStatus('disconnected', 'Disconnected');
            addLog('system', 'Connection lost. Attempting to reconnect in 3 seconds...');
            sendButton.disabled = true;
            setTimeout(connect, 3000); // Attempt to reconnect
        };

        socket.onerror = (error) => {
            console.error('WebSocket Error:', error);
            addLog('error', 'A connection error occurred.');
        };
    }

    function handleSocketMessage(data) {
        switch (data.type) {
            case 'thought':
                addLog('thought', `> ${data.content}`);
                updateStatus('thinking', 'Thinking...');
                break;
            case 'final':
                addLog('final', `✓ Final Answer: ${data.content}`);
                updateStatus('connected', 'Connected');
                sendButton.disabled = false;
                taskInput.disabled = false;
                taskInput.focus();
                break;
            case 'error':
                addLog('error', `✗ Error: ${data.content}`);
                updateStatus('connected', 'Connected');
                sendButton.disabled = false;
                taskInput.disabled = false;
                taskInput.focus();
                break;
            default:
                addLog('system', data.content);
        }
    }

    function addLog(type, message) {
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry ${type}`;
        logEntry.textContent = message;
        logsContainer.appendChild(logEntry);
        // Scroll to the bottom
        logsContainer.scrollTop = logsContainer.scrollHeight;
    }

    function updateStatus(className, text) {
        statusLight.className = className;
        statusText.textContent = text;
    }

    function sendTask() {
        const task = taskInput.value.trim();
        if (task && socket && socket.readyState === WebSocket.OPEN) {
            addLog('user', `>>> Your Task: ${task}`);
            socket.send(task);
            taskInput.value = '';
            taskInput.disabled = true;
            sendButton.disabled = true;
            updateStatus('thinking', 'Thinking...');
        }
    }

    sendButton.addEventListener('click', sendTask);
    taskInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendTask();
        }
    });

    // Initial connection
    connect();
});
