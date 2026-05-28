window.WriterStudioObsidian = (() => {
    const modal = document.getElementById('obsidian-modal');
    const fileSearch = document.getElementById('file-search');
    const fileListContainer = document.getElementById('file-list-container');
    let files = [];
    let context = null;

    function configure(nextContext) {
        context = nextContext;
    }

    function setFileListMessage(message, isError = false) {
        const div = document.createElement('div');
        div.className = 'loading';
        div.textContent = message;
        if (isError) div.style.color = '#ff4d4f';
        fileListContainer.replaceChildren(div);
    }

    function formatFileSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    }

    function renderFileList(nextFiles) {
        if (nextFiles.length === 0) {
            setFileListMessage('没有找到文件');
            return;
        }

        fileListContainer.replaceChildren(...nextFiles.map(file => {
            const item = document.createElement('div');
            item.className = 'file-item';
            item.addEventListener('click', () => loadFile(file.name));

            const name = document.createElement('div');
            name.className = 'file-name';
            name.textContent = `📄 ${file.name}`;

            const meta = document.createElement('div');
            meta.className = 'file-meta';
            meta.textContent = `${file.modified_str} · ${formatFileSize(file.size)}`;

            item.append(name, meta);
            return item;
        }));
    }

    async function open() {
        modal.style.display = 'flex';
        await refresh();
    }

    function close() {
        modal.style.display = 'none';
    }

    async function refresh() {
        setFileListMessage('加载中...');

        try {
            const data = await context.api.listObsidianFiles();

            if (data.status === 'success') {
                files = data.files;
                renderFileList(files);
            } else {
                setFileListMessage(data.message, true);
            }
        } catch (e) {
            console.error(e);
            setFileListMessage('加载失败', true);
        }
    }

    function filter() {
        const searchTerm = fileSearch.value.toLowerCase();
        const filtered = files.filter(file =>
            file.name.toLowerCase().includes(searchTerm)
        );
        renderFileList(filtered);
    }

    async function loadFile(filename) {
        context.notify('加载中...', 'success');

        try {
            const data = await context.api.loadObsidianFile({
                filename,
                session_id: context.sessionId
            });

            if (data.status === 'success') {
                context.onLoaded(data);
                close();
                context.notify('✅ 文章已加载！');
            } else {
                context.notify(data.message || '加载失败', 'error');
            }
        } catch (e) {
            console.error(e);
            context.notify('加载失败', 'error');
        }
    }

    return {
        configure,
        open,
        close,
        refresh,
        filter
    };
})();
