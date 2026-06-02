window.WriterStudioPublishing = (() => {
    async function publishWechat({ api, dom, settings, filename, sessionId, theme, notify, state }) {
        const approved = await confirmPublishCheck({ dom, settings, filename, state });
        if (!approved) return;

        const { app_id, app_secret, author_name } = settings.getConfig();
        if (!app_id || !app_secret) {
            notify('请先在 Settings 里填写 AppID 和 AppSecret', 'error');
            return;
        }

        console.log("Publishing draft...");
        setButtonBusy(dom.wechatPublishBtn, true, '发布中...');
        notify('Publishing...', 'success');

        try {
            const data = await api.publishWechat({
                filename,
                session_id: sessionId,
                app_id,
                app_secret,
                author_name,
                theme
            });

            if (data.status === 'success') {
                notify('Published to WeChat!');
            } else {
                notify(data.message, 'error');
            }
        } catch (e) {
            console.error(e);
            notify('Publish error', 'error');
        } finally {
            setButtonBusy(dom.wechatPublishBtn, false);
        }
    }

    async function publishBlog({ api, dom, settings, content, filename, notify }) {
        if (!confirm('Sync this article to your personal blog (local)?')) return;

        const author_name = settings.getAuthorName('Hugo');
        setButtonBusy(dom.blogPublishBtn, true, '同步中...');
        notify('Syncing to blog...', 'success');

        try {
            const data = await api.publishBlog({ content, filename, author_name });
            if (data.status === 'success') {
                notify('Synced to Blog Check posts folder!');
                console.log("Saved to:", data.path);
            } else {
                notify('Sync failed: ' + data.message, 'error');
            }
        } catch (e) {
            console.error(e);
            notify('Network error during sync', 'error');
        } finally {
            setButtonBusy(dom.blogPublishBtn, false);
        }
    }

    function confirmPublishCheck({ dom, settings, filename, state }) {
        const config = settings.getConfig();
        const checks = [
            {
                ok: Boolean(filename && filename.trim()),
                label: `文件名：${filename || '未填写'}`
            },
            {
                ok: Boolean(state && state.previewGenerated),
                label: state && state.previewGenerated ? '预览已生成' : '还没有生成当前预览'
            },
            {
                ok: Boolean(config.app_id && config.app_secret),
                label: config.app_id && config.app_secret ? '公众号配置已填写' : 'AppID / AppSecret 未填写'
            },
            {
                ok: true,
                label: state && state.featureImageName
                    ? `头图：${state.featureImageName}`
                    : '头图：未在本次会话上传，按文章内容继续'
            }
        ];
        const blocking = checks.some(check => !check.ok);

        dom.publishCheckList.replaceChildren(...checks.map(renderCheck));
        dom.publishCheckConfirmBtn.disabled = blocking;
        dom.publishCheckConfirmBtn.classList.toggle('is-disabled', blocking);
        dom.publishCheckModal.style.display = 'flex';

        return new Promise(resolve => {
            function close(result) {
                dom.publishCheckModal.style.display = 'none';
                dom.publishCheckCancelBtn.removeEventListener('click', onCancel);
                dom.publishCheckConfirmBtn.removeEventListener('click', onConfirm);
                resolve(result);
            }

            function onCancel() {
                close(false);
            }

            function onConfirm() {
                if (blocking) return;
                close(true);
            }

            dom.publishCheckCancelBtn.addEventListener('click', onCancel);
            dom.publishCheckConfirmBtn.addEventListener('click', onConfirm);
        });
    }

    function renderCheck(check) {
        const row = document.createElement('div');
        row.className = check.ok ? 'check-row check-row-ok' : 'check-row check-row-error';

        const icon = document.createElement('span');
        icon.className = 'check-icon';
        icon.textContent = check.ok ? '✓' : '!';

        const label = document.createElement('span');
        label.textContent = check.label;

        row.append(icon, label);
        return row;
    }

    function setButtonBusy(button, isBusy, busyText) {
        if (!button) return;
        if (isBusy) {
            button.dataset.defaultText = button.textContent;
            button.textContent = busyText;
            button.disabled = true;
            button.classList.add('is-busy');
            return;
        }

        button.textContent = button.dataset.defaultText || button.textContent;
        button.disabled = false;
        button.classList.remove('is-busy');
    }

    return {
        publishWechat,
        publishBlog
    };
})();
