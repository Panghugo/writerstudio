const api = window.WriterStudioApi;
const dom = window.WriterStudioDom;
const editor = window.WriterStudioEditor;
const notifications = window.WriterStudioNotifications;
const settings = window.WriterStudioSettings;
const publishing = window.WriterStudioPublishing;
const obsidian = window.WriterStudioObsidian;
const uploads = window.WriterStudioUploads;

const DEFAULT_CONTENT = `# Welcome to Writer Studio

Here is your new web-based editor.

## Features
- **Markdown** Support
- Instant **HTML Preview**
- WeChat Publishing

> "Simplicity is the ultimate sophistication."

Click "Generate" to see the magic.`;

const sessionId = getOrCreateSessionId();
dom.editor.value = DEFAULT_CONTENT;
initializeTheme();
configureModules();
bindEvents();

function getOrCreateSessionId() {
    const existingSession = localStorage.getItem('ws_session_id');
    if (existingSession) return existingSession;

    const nextSession = uuidv4();
    localStorage.setItem('ws_session_id', nextSession);
    return nextSession;
}

function uuidv4() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

function initializeTheme() {
    dom.themeSelect.value = localStorage.getItem('ws_theme') || 'black_gold';
}

function configureModules() {
    obsidian.configure({
        api,
        sessionId,
        notify: showNotify,
        onLoaded(data) {
            dom.editor.value = data.content;
            dom.filenameInput.value = data.filename;
        }
    });

    uploads.configure({
        api,
        sessionId,
        notify: showNotify,
        insertFormat: insertEditorFormat
    });
}

function bindEvents() {
    dom.themeSelect.addEventListener('change', () => {
        localStorage.setItem('ws_theme', dom.themeSelect.value);
        saveAndGenerate();
    });

    document.addEventListener('keydown', event => {
        if ((event.ctrlKey || event.metaKey) && event.key === 's') {
            event.preventDefault();
            saveAndGenerate();
        }
    });

    dom.settingsOpenBtn.addEventListener('click', settings.open);
    dom.settingsCloseBtn.addEventListener('click', settings.close);
    dom.settingsSaveBtn.addEventListener('click', () => {
        settings.save();
        showNotify('Settings saved to browser!');
    });

    dom.blogPublishBtn.addEventListener('click', () => {
        publishing.publishBlog({
            api,
            settings,
            content: dom.editor.value,
            filename: dom.filenameInput.value,
            notify: showNotify
        });
    });

    dom.wechatPublishBtn.addEventListener('click', () => {
        publishing.publishWechat({
            api,
            settings,
            filename: dom.filenameInput.value,
            sessionId,
            theme: dom.themeSelect.value,
            notify: showNotify
        });
    });

    dom.generateBtn.addEventListener('click', saveAndGenerate);
    dom.obsidianOpenBtn.addEventListener('click', obsidian.open);
    dom.obsidianCloseBtn.addEventListener('click', obsidian.close);
    dom.obsidianRefreshBtn.addEventListener('click', obsidian.refresh);
    dom.fileSearch.addEventListener('keyup', obsidian.filter);

    dom.formatButtons.forEach(button => {
        button.addEventListener('click', () => {
            insertEditorFormat(button.dataset.prefix || '', button.dataset.suffix || '');
        });
    });

    dom.imageUploadBtn.addEventListener('click', () => {
        dom.imageUploadInput.click();
    });
    dom.featureUploadBtn.addEventListener('click', () => {
        dom.featureUploadInput.click();
    });
    dom.imageUploadInput.addEventListener('change', event => {
        uploads.uploadImage(event.currentTarget);
    });
    dom.featureUploadInput.addEventListener('change', event => {
        uploads.uploadFeatureImage(event.currentTarget);
    });
}

function showNotify(msg, type = 'success') {
    notifications.show(dom.notification, msg, type);
}

function insertEditorFormat(prefix, suffix = '') {
    editor.insertFormat(dom.editor, prefix, suffix);
}

async function saveAndGenerate() {
    showNotify('Generating...', 'success');

    try {
        const data = await api.saveAndGenerate({
            content: dom.editor.value,
            filename: dom.filenameInput.value,
            session_id: sessionId,
            theme: dom.themeSelect.value,
            author_name: settings.getAuthorName('作者')
        });

        if (data.status === 'success') {
            showNotify('Generated Successfully!');
            dom.emptyPreview.style.display = 'none';
            dom.previewFrame.style.display = 'block';
            dom.previewFrame.src = data.preview_url + '?t=' + Date.now();
        } else {
            showNotify(data.message || 'Generation failed', 'error');
        }
    } catch (e) {
        console.error(e);
        showNotify('Network error', 'error');
    }
}
