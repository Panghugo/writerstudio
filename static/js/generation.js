window.WriterStudioGeneration = (() => {
    async function saveAndGenerate({ api, dom, settings, sessionId, notify }) {
        notify('Generating...', 'success');

        try {
            const data = await api.saveAndGenerate({
                content: dom.editor.value,
                filename: dom.filenameInput.value,
                session_id: sessionId,
                theme: dom.themeSelect.value,
                author_name: settings.getAuthorName('作者')
            });

            if (data.status === 'success') {
                notify('Generated Successfully!');
                dom.emptyPreview.style.display = 'none';
                dom.previewFrame.style.display = 'block';
                dom.previewFrame.src = data.preview_url + '?t=' + Date.now();
            } else {
                notify(data.message || 'Generation failed', 'error');
            }
        } catch (e) {
            console.error(e);
            notify('Network error', 'error');
        }
    }

    return {
        saveAndGenerate
    };
})();
