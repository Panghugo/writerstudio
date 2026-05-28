const api = window.WriterStudioApi;
const dom = window.WriterStudioDom;
const editor = window.WriterStudioEditor;
const generation = window.WriterStudioGeneration;
const notifications = window.WriterStudioNotifications;
const settings = window.WriterStudioSettings;
const publishing = window.WriterStudioPublishing;
const obsidian = window.WriterStudioObsidian;
const session = window.WriterStudioSession;
const theme = window.WriterStudioTheme;
const uploads = window.WriterStudioUploads;

const DEFAULT_CONTENT = `# Welcome to Writer Studio

Here is your new web-based editor.

## Features
- **Markdown** Support
- Instant **HTML Preview**
- WeChat Publishing

> "Simplicity is the ultimate sophistication."

Click "Generate" to see the magic.`;

const sessionId = session.getOrCreateSessionId();
dom.editor.value = DEFAULT_CONTENT;
theme.initialize(dom.themeSelect);
configureModules();
bindEvents();

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
        theme.saveSelectedTheme(dom.themeSelect.value);
        generatePreview();
    });

    document.addEventListener('keydown', event => {
        if ((event.ctrlKey || event.metaKey) && event.key === 's') {
            event.preventDefault();
            generatePreview();
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

    dom.generateBtn.addEventListener('click', generatePreview);
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

function generatePreview() {
    generation.saveAndGenerate({
        api,
        dom,
        settings,
        sessionId,
        notify: showNotify
    });
}
