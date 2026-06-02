window.WriterStudioDrafts = (() => {
    const BASE_STORAGE_KEY = 'ws_current_draft_v1';
    const SAVE_DELAY_MS = 500;
    const DEFAULT_CONTENT = `# Welcome to Writer Studio

Here is your new web-based editor.

## Features
- **Markdown** Support
- Instant **HTML Preview**
- WeChat Publishing

> "Simplicity is the ultimate sophistication."

Click "Generate" to see the magic.`;

    let timer = null;
    let dirty = false;
    let storageKey = BASE_STORAGE_KEY;

    function configure(sessionId) {
        storageKey = sessionId ? `${BASE_STORAGE_KEY}_${sessionId}` : BASE_STORAGE_KEY;
    }

    function nowLabel() {
        return new Date().toLocaleTimeString('zh-CN', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    }

    function read() {
        try {
            return JSON.parse(localStorage.getItem(storageKey) || '{}');
        } catch (e) {
            console.warn('Unable to read draft', e);
            return {};
        }
    }

    function snapshot(dom) {
        return {
            content: dom.editor.value,
            filename: dom.filenameInput.value,
            theme: dom.themeSelect.value,
            updated_at: new Date().toISOString()
        };
    }

    function write(data) {
        localStorage.setItem(storageKey, JSON.stringify(data));
    }

    function setDraftStatus(dom, text) {
        if (dom.draftStatus) dom.draftStatus.textContent = text;
    }

    function setGenerationStatus(dom, text) {
        if (dom.generationStatus) dom.generationStatus.textContent = text;
    }

    function hasSavedDraft() {
        const draft = read();
        return Boolean(draft.content || draft.filename || draft.updated_at);
    }

    function isDefaultContent(content) {
        return String(content || '').trim() === DEFAULT_CONTENT.trim();
    }

    function restore(dom) {
        const draft = read();
        if (draft.content || draft.filename || draft.theme) {
            dom.editor.value = draft.content || '';
            dom.filenameInput.value = draft.filename || 'untitled';
            if (draft.theme) dom.themeSelect.value = draft.theme;
            setDraftStatus(dom, '已恢复本地草稿');
            return;
        }

        dom.editor.value = DEFAULT_CONTENT;
        setDraftStatus(dom, '示例草稿已载入');
    }

    function saveNow(dom) {
        write(snapshot(dom));
        dirty = false;
        setDraftStatus(dom, `已自动保存 ${nowLabel()}`);
    }

    function scheduleSave(dom) {
        dirty = true;
        setDraftStatus(dom, '正在编辑...');
        clearTimeout(timer);
        timer = setTimeout(() => saveNow(dom), SAVE_DELAY_MS);
    }

    function markGenerated(dom) {
        setGenerationStatus(dom, `已生成预览 ${nowLabel()}`);
    }

    function markGenerationDirty(dom) {
        setGenerationStatus(dom, '预览可能不是最新');
    }

    function bind(dom) {
        ['input', 'change'].forEach(eventName => {
            dom.editor.addEventListener(eventName, () => {
                scheduleSave(dom);
                markGenerationDirty(dom);
            });
            dom.filenameInput.addEventListener(eventName, () => {
                scheduleSave(dom);
                markGenerationDirty(dom);
            });
        });

        window.addEventListener('beforeunload', event => {
            if (!dirty) return;
            event.preventDefault();
            event.returnValue = '';
        });
    }

    return {
        bind,
        configure,
        hasSavedDraft,
        isDefaultContent,
        markGenerated,
        markGenerationDirty,
        restore,
        saveNow
    };
})();
