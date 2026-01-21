/**
 * Cultural AI - Frontend Application
 * macOS/iOS themed chat interface
 */

// ============================================
// Configuration
// ============================================

const API_BASE_URL = 'http://localhost:8000';

// ============================================
// State Management
// ============================================

const state = {
    currentView: 'chat',
    isConnected: false,
    isLoading: false,
    selectedFile: null,
    messages: []
};

// ============================================
// DOM Elements
// ============================================

const elements = {
    // Navigation
    navItems: document.querySelectorAll('.nav-item'),
    views: document.querySelectorAll('.view'),

    // Status
    statusDot: document.querySelector('.status-dot'),
    statusText: document.querySelector('.status-text'),

    // Chat
    messagesContainer: document.getElementById('messages'),
    chatInput: document.getElementById('chat-input'),
    sendBtn: document.getElementById('send-btn'),
    clearChatBtn: document.querySelector('.clear-chat-btn'),
    quickActions: document.querySelectorAll('.quick-action'),

    // Knowledge Base
    kbStats: document.getElementById('kb-stats'),
    textTitle: document.getElementById('text-title'),
    textContent: document.getElementById('text-content'),
    textSourceType: document.getElementById('text-source-type'),
    textCategory: document.getElementById('text-category'),
    addTextBtn: document.getElementById('add-text-btn'),
    urlInput: document.getElementById('url-input'),
    urlSourceType: document.getElementById('url-source-type'),
    urlCategory: document.getElementById('url-category'),
    addUrlBtn: document.getElementById('add-url-btn'),
    fileUploadArea: document.getElementById('file-upload-area'),
    fileInput: document.getElementById('file-input'),
    fileSourceType: document.getElementById('file-source-type'),
    fileCategory: document.getElementById('file-category'),
    uploadFileBtn: document.getElementById('upload-file-btn'),

    // Analyze
    analyzeTopic: document.getElementById('analyze-topic'),
    analyzeBtn: document.getElementById('analyze-btn'),
    analyzeResult: document.getElementById('analyze-result'),
    analyzeContent: document.getElementById('analyze-content'),
    analyzeSources: document.getElementById('analyze-sources'),

    // Toast
    toastContainer: document.getElementById('toast-container')
};

// ============================================
// Utility Functions
// ============================================

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<span>${message}</span>`;
    elements.toastContainer.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'toastSlide 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function formatMarkdown(text) {
    // Basic markdown formatting
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`(.*?)`/g, '<code>$1</code>')
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>');
}

function autoResizeTextarea(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 150) + 'px';
}

// ============================================
// API Functions
// ============================================

async function checkConnection() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/health`);
        if (response.ok) {
            state.isConnected = true;
            elements.statusDot.classList.add('connected');
            elements.statusText.textContent = 'Connected';
            return true;
        }
    } catch (error) {
        state.isConnected = false;
        elements.statusDot.classList.remove('connected');
        elements.statusText.textContent = 'Disconnected';
    }
    return false;
}

async function fetchStats() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/stats`);
        if (response.ok) {
            const data = await response.json();
            elements.kbStats.innerHTML = `<span class="stat-badge">${data.count} documents</span>`;
        }
    } catch (error) {
        console.error('Failed to fetch stats:', error);
    }
}

async function sendChatMessage(question) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question, k: 4, temperature: 0.7 })
        });

        if (!response.ok) throw new Error('API request failed');
        return await response.json();
    } catch (error) {
        throw error;
    }
}

async function ingestText(text, title, category, source_type) {
    const response = await fetch(`${API_BASE_URL}/api/ingest/text`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, title, category, source_type })
    });

    if (!response.ok) throw new Error('Failed to ingest text');
    return await response.json();
}

async function ingestUrl(url, category, source_type) {
    const response = await fetch(`${API_BASE_URL}/api/ingest/url`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, category, source_type })
    });

    if (!response.ok) throw new Error('Failed to ingest URL');
    return await response.json();
}

async function uploadFile(file, category, source_type) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('category', category);
    formData.append('source_type', source_type);

    const response = await fetch(`${API_BASE_URL}/api/ingest/file`, {
        method: 'POST',
        body: formData
    });

    if (!response.ok) throw new Error('Failed to upload file');
    return await response.json();
}

async function analyzeTopicAPI(topic, analysisType) {
    const response = await fetch(`${API_BASE_URL}/api/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic, analysis_type: analysisType })
    });

    if (!response.ok) throw new Error('Analysis failed');
    return await response.json();
}

// ============================================
// UI Functions
// ============================================

function switchView(viewName) {
    state.currentView = viewName;

    elements.navItems.forEach(item => {
        item.classList.toggle('active', item.dataset.view === viewName);
    });

    elements.views.forEach(view => {
        view.classList.toggle('active', view.id === `${viewName}-view`);
    });

    if (viewName === 'knowledge') {
        fetchStats();
    }
}

function addMessage(content, type, sources = []) {
    // Hide welcome message
    const welcome = elements.messagesContainer.querySelector('.welcome-message');
    if (welcome) welcome.style.display = 'none';

    const messageDiv = document.createElement('div');
    messageDiv.className = `message message-${type}`;

    if (type === 'user') {
        messageDiv.innerHTML = `
            <div class="message-content">
                <p>${content}</p>
            </div>
        `;
    } else {
        let sourcesHtml = '';
        if (sources.length > 0) {
            const sourceTags = sources.map(s =>
                `<span class="source-tag">${s.filename || s.url || 'Unknown'}</span>`
            ).join('');
            sourcesHtml = `
                <div class="message-sources">
                    <strong>Sources:</strong> ${sourceTags}
                </div>
            `;
        }

        messageDiv.innerHTML = `
            <div class="message-avatar">🎓</div>
            <div class="message-content">
                <p>${formatMarkdown(content)}</p>
                ${sourcesHtml}
            </div>
        `;
    }

    elements.messagesContainer.appendChild(messageDiv);
    elements.messagesContainer.scrollTop = elements.messagesContainer.scrollHeight;
}

function addTypingIndicator() {
    const indicator = document.createElement('div');
    indicator.className = 'message message-assistant typing';
    indicator.innerHTML = `
        <div class="message-avatar">🎓</div>
        <div class="message-content">
            <div class="typing-indicator">
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
            </div>
        </div>
    `;
    elements.messagesContainer.appendChild(indicator);
    elements.messagesContainer.scrollTop = elements.messagesContainer.scrollHeight;
    return indicator;
}

function removeTypingIndicator(indicator) {
    if (indicator && indicator.parentNode) {
        indicator.remove();
    }
}

function clearChat() {
    elements.messagesContainer.innerHTML = `
        <div class="welcome-message">
            <div class="welcome-icon">🎓</div>
            <h2>Selamat datang di Cultural AI</h2>
            <p>Asisten AI untuk Cultural Studies, Sastra, Linguistik, dan Ilmu Bahasa</p>
            <div class="quick-actions">
                <button class="quick-action" data-question="Apa itu semiotika dalam kajian budaya?">
                    Semiotika
                </button>
                <button class="quick-action" data-question="Jelaskan konsep hegemoni menurut Gramsci">
                    Hegemoni Gramsci
                </button>
                <button class="quick-action" data-question="Apa perbedaan antara langue dan parole?">
                    Langue vs Parole
                </button>
            </div>
        </div>
    `;

    // Re-attach quick action listeners
    document.querySelectorAll('.quick-action').forEach(btn => {
        btn.addEventListener('click', () => {
            elements.chatInput.value = btn.dataset.question;
            elements.sendBtn.disabled = false;
            handleSendMessage();
        });
    });

    state.messages = [];
}

// ============================================
// Event Handlers
// ============================================

async function handleSendMessage() {
    const question = elements.chatInput.value.trim();
    if (!question || state.isLoading) return;

    state.isLoading = true;
    elements.sendBtn.disabled = true;
    elements.chatInput.value = '';
    autoResizeTextarea(elements.chatInput);

    // Add user message
    addMessage(question, 'user');

    // Add typing indicator
    const typingIndicator = addTypingIndicator();

    try {
        const response = await sendChatMessage(question);
        removeTypingIndicator(typingIndicator);
        addMessage(response.answer, 'assistant', response.sources);
    } catch (error) {
        removeTypingIndicator(typingIndicator);
        addMessage('Maaf, terjadi kesalahan. Pastikan server backend berjalan di localhost:8000', 'assistant');
        showToast('Failed to get response', 'error');
    } finally {
        state.isLoading = false;
    }
}

async function handleAddText() {
    const text = elements.textContent.value.trim();
    const title = elements.textTitle.value.trim() || 'Untitled';
    const category = elements.textCategory.value;
    const source_type = elements.textSourceType.value;

    if (!text || text.length < 10) {
        showToast('Please enter at least 10 characters', 'warning');
        return;
    }

    try {
        elements.addTextBtn.disabled = true;
        elements.addTextBtn.textContent = 'Adding...';

        const result = await ingestText(text, title, category, source_type);

        showToast(`✅ Added "${title}" to ${source_type} knowledge base`, 'success');
        elements.textContent.value = '';
        elements.textTitle.value = '';
        fetchStats();
    } catch (error) {
        showToast('Failed to add text', 'error');
    } finally {
        elements.addTextBtn.disabled = false;
        elements.addTextBtn.textContent = 'Add to Knowledge Base';
    }
}

async function handleAddUrl() {
    const url = elements.urlInput.value.trim();
    const category = elements.urlCategory.value;
    const source_type = elements.urlSourceType.value;

    if (!url) {
        showToast('Please enter a URL', 'warning');
        return;
    }

    try {
        elements.addUrlBtn.disabled = true;
        elements.addUrlBtn.textContent = 'Fetching...';

        const result = await ingestUrl(url, category, source_type);

        showToast(`✅ URL content added as ${source_type}`, 'success');
        elements.urlInput.value = '';
        fetchStats();
    } catch (error) {
        showToast('Failed to fetch URL', 'error');
    } finally {
        elements.addUrlBtn.disabled = false;
        elements.addUrlBtn.textContent = 'Fetch & Add';
    }
}

async function handleFileUpload() {
    if (!state.selectedFile) {
        showToast('Please select a file', 'warning');
        return;
    }

    const category = elements.fileCategory.value;
    const source_type = elements.fileSourceType.value;

    try {
        elements.uploadFileBtn.disabled = true;
        elements.uploadFileBtn.textContent = 'Uploading...';

        const result = await uploadFile(state.selectedFile, category, source_type);

        showToast(`✅ Uploaded "${state.selectedFile.name}" as ${source_type}`, 'success');
        state.selectedFile = null;
        elements.fileUploadArea.querySelector('p').textContent = 'Drag & drop files here or click to browse';
        fetchStats();
    } catch (error) {
        showToast('Failed to upload file', 'error');
    } finally {
        elements.uploadFileBtn.disabled = true;
        elements.uploadFileBtn.textContent = 'Upload File';
    }
}

async function handleAnalyze() {
    const topic = elements.analyzeTopic.value.trim();
    const analysisType = document.querySelector('input[name="analysis-type"]:checked').value;

    if (!topic) {
        showToast('Please enter a topic', 'warning');
        return;
    }

    try {
        elements.analyzeBtn.disabled = true;
        elements.analyzeBtn.textContent = 'Analyzing...';

        const result = await analyzeTopicAPI(topic, analysisType);

        elements.analyzeContent.innerHTML = `<p>${formatMarkdown(result.analysis)}</p>`;

        if (result.sources && result.sources.length > 0) {
            const sourceTags = result.sources.map(s =>
                `<span class="source-tag">${s.filename || s.url || 'Unknown'}</span>`
            ).join('');
            elements.analyzeSources.innerHTML = `<strong>Sources:</strong> ${sourceTags}`;
        } else {
            elements.analyzeSources.innerHTML = '';
        }

        elements.analyzeResult.style.display = 'block';
    } catch (error) {
        showToast('Analysis failed', 'error');
    } finally {
        elements.analyzeBtn.disabled = false;
        elements.analyzeBtn.textContent = 'Start Analysis';
    }
}

// ============================================
// Event Listeners
// ============================================

function initEventListeners() {
    // Navigation
    elements.navItems.forEach(item => {
        item.addEventListener('click', () => switchView(item.dataset.view));
    });

    // Chat input
    elements.chatInput.addEventListener('input', () => {
        autoResizeTextarea(elements.chatInput);
        elements.sendBtn.disabled = !elements.chatInput.value.trim();
    });

    elements.chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    });

    elements.sendBtn.addEventListener('click', handleSendMessage);
    elements.clearChatBtn.addEventListener('click', clearChat);

    // Quick actions
    elements.quickActions.forEach(btn => {
        btn.addEventListener('click', () => {
            elements.chatInput.value = btn.dataset.question;
            elements.sendBtn.disabled = false;
            handleSendMessage();
        });
    });

    // Knowledge Base
    elements.addTextBtn.addEventListener('click', handleAddText);
    elements.addUrlBtn.addEventListener('click', handleAddUrl);
    elements.uploadFileBtn.addEventListener('click', handleFileUpload);

    // File upload
    elements.fileUploadArea.addEventListener('click', () => elements.fileInput.click());
    elements.fileUploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        elements.fileUploadArea.classList.add('dragover');
    });
    elements.fileUploadArea.addEventListener('dragleave', () => {
        elements.fileUploadArea.classList.remove('dragover');
    });
    elements.fileUploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        elements.fileUploadArea.classList.remove('dragover');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileSelect(files[0]);
        }
    });
    elements.fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelect(e.target.files[0]);
        }
    });

    // Analyze
    elements.analyzeBtn.addEventListener('click', handleAnalyze);
    elements.analyzeTopic.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            handleAnalyze();
        }
    });
}

function handleFileSelect(file) {
    const allowedTypes = ['.pdf', '.md', '.markdown', '.txt'];
    const ext = '.' + file.name.split('.').pop().toLowerCase();

    if (!allowedTypes.includes(ext)) {
        showToast('Please select a PDF, Markdown, or Text file', 'warning');
        return;
    }

    state.selectedFile = file;
    elements.fileUploadArea.querySelector('p').textContent = file.name;
    elements.uploadFileBtn.disabled = false;
}

// ============================================
// Initialization
// ============================================

async function init() {
    initEventListeners();

    // Check connection
    const connected = await checkConnection();
    if (connected) {
        showToast('Connected to Cultural AI', 'success');
        fetchStats();
    } else {
        showToast('Cannot connect to server. Start the backend first.', 'warning');
    }

    // Periodic connection check
    setInterval(checkConnection, 30000);
}

// Start the app
document.addEventListener('DOMContentLoaded', init);
