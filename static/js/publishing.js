window.WriterStudioPublishing = (() => {
    async function publishWechat({ api, settings, filename, sessionId, theme, notify }) {
        if (!confirm('Confirm publish to WeChat Drafts?')) return;

        const { app_id, app_secret, author_name } = settings.getConfig();
        if (!app_id || !app_secret) {
            notify('请先在 Settings 里填写 AppID 和 AppSecret', 'error');
            return;
        }

        console.log("Publishing draft...");
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
        }
    }

    async function publishBlog({ api, settings, content, filename, notify }) {
        if (!confirm('Sync this article to your personal blog (local)?')) return;

        const author_name = settings.getAuthorName('Hugo');
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
        }
    }

    return {
        publishWechat,
        publishBlog
    };
})();
