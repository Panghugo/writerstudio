window.WriterStudioDom = (() => {
    function qs(selector) {
        return document.querySelector(selector);
    }

    function qsa(selector) {
        return Array.from(document.querySelectorAll(selector));
    }

    return {
        editor: qs('#markdown-editor'),
        previewFrame: qs('#preview-frame'),
        emptyPreview: qs('#empty-preview'),
        filenameInput: qs('#filename-input'),
        notification: qs('#notification'),
        themeSelect: qs('#theme-select'),
        settingsOpenBtn: qs('#settings-open-btn'),
        settingsCloseBtn: qs('#settings-close-btn'),
        settingsSaveBtn: qs('#settings-save-btn'),
        blogPublishBtn: qs('#blog-publish-btn'),
        wechatPublishBtn: qs('#wechat-publish-btn'),
        generateBtn: qs('#generate-btn'),
        obsidianOpenBtn: qs('#obsidian-open-btn'),
        obsidianCloseBtn: qs('#obsidian-close-btn'),
        obsidianRefreshBtn: qs('#obsidian-refresh-btn'),
        fileSearch: qs('#file-search'),
        imageUploadBtn: qs('#image-upload-btn'),
        featureUploadBtn: qs('#feature-upload-btn'),
        imageUploadInput: qs('#img-upload'),
        featureUploadInput: qs('#feature-upload'),
        formatButtons: qsa('.format-btn')
    };
})();
