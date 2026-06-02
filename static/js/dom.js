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
        emptyPreviewTitle: qs('#empty-preview-title'),
        emptyPreviewDetail: qs('#empty-preview-detail'),
        draftStatus: qs('#draft-status'),
        generationStatus: qs('#generation-status'),
        wechatOutputStatus: qs('#wechat-output-status'),
        socialOutputStatus: qs('#social-output-status'),
        socialPresetSelect: qs('#social-preset-select'),
        socialExportPanel: qs('#social-export-panel'),
        socialQualityPanel: qs('#social-quality-panel'),
        socialLayoutControls: qs('#social-layout-controls'),
        filenameInput: qs('#filename-input'),
        notification: qs('#notification'),
        themeSelect: qs('#theme-select'),
        outputTabs: qsa('.output-tab'),
        outputPanels: qsa('.output-panel'),
        settingsOpenBtn: qs('#settings-open-btn'),
        settingsCloseBtn: qs('#settings-close-btn'),
        settingsSaveBtn: qs('#settings-save-btn'),
        blogPublishBtn: qs('#blog-publish-btn'),
        wechatPublishBtn: qs('#wechat-publish-btn'),
        socialImageBtn: qs('#social-image-btn'),
        generateBtn: qs('#generate-btn'),
        publishCheckModal: qs('#publish-check-modal'),
        publishCheckList: qs('#publish-check-list'),
        publishCheckCancelBtn: qs('#publish-check-cancel-btn'),
        publishCheckConfirmBtn: qs('#publish-check-confirm-btn'),
        obsidianOpenBtn: qs('#obsidian-open-btn'),
        obsidianCloseBtn: qs('#obsidian-close-btn'),
        obsidianRefreshBtn: qs('#obsidian-refresh-btn'),
        fileSearch: qs('#file-search'),
        imageUploadBtn: qs('#image-upload-btn'),
        featureUploadBtn: qs('#feature-upload-btn'),
        featureRemoveBtn: qs('#feature-remove-btn'),
        featureImageStatus: qs('#feature-image-status'),
        imageUploadInput: qs('#img-upload'),
        featureUploadInput: qs('#feature-upload'),
        formatButtons: qsa('.format-btn')
    };
})();
