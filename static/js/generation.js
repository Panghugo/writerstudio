window.WriterStudioGeneration = (() => {
    async function saveAndGenerate({ api, dom, settings, sessionId, notify, drafts, onSuccess }) {
        dom.setButtonBusy(dom.generateBtn, true, '生成中...');
        notify('正在生成预览...', 'success');
        const config = settings.getConfig();

        try {
            const data = await api.saveAndGenerate({
                content: dom.editor.value,
                filename: dom.filenameInput.value,
                session_id: sessionId,
                theme: dom.themeSelect.value,
                author_name: config.author_name || '作者'
            });

            if (data.status === 'success') {
                notify('预览已生成');
                const previewUrl = getArtifactUrl(data, 'html') || data.preview_url;
                if (onSuccess) {
                    onSuccess(data, { previewUrl });
                } else {
                    renderWechatPreview(dom.previewFrame, previewUrl, Date.now());
                    if (drafts) drafts.markGenerated(dom);
                }
                return data;
            } else {
                notify(data.message || '生成失败', 'error');
            }
        } catch (e) {
            console.error(e);
            notify('网络错误', 'error');
        } finally {
            dom.setButtonBusy(dom.generateBtn, false);
        }
    }

    async function generateSocialImage({ api, dom, settings, sessionId, notify, layoutOverrides, blockControls, socialPreset, onSuccess }) {
        dom.setButtonBusy(dom.socialImageBtn, true, '生成中...');
        notify('正在生成文字图...', 'success');
        const config = settings.getConfig();

        try {
            const data = await api.generateSocialImage({
                content: dom.editor.value,
                filename: dom.filenameInput.value,
                session_id: sessionId,
                theme: dom.themeSelect.value,
                author_name: config.author_name || '作者',
                social_brand_name: config.social_brand_name,
                social_brand_en: config.social_brand_en,
                social_brand_accent_text: config.social_brand_accent_text,
                social_preset: socialPreset || 'balanced',
                social_layout_overrides: layoutOverrides || {},
                social_block_controls: blockControls || {}
            });

            if (data.status === 'success') {
                notify(data.message || '文字图已生成');
                const imageUrls = getArtifactUrls(data, 'image');
                if (!imageUrls.length) {
                    imageUrls.push(...(data.image_urls || [data.image_url]));
                }
                if (onSuccess) {
                    onSuccess(data, {
                        imageUrls: imageUrls.filter(Boolean),
                        zipUrl: getArtifactUrl(data, 'zip') || data.zip_url || '',
                        qualityChecks: Array.isArray(data.quality_checks) ? data.quality_checks : [],
                        pageLayout: Array.isArray(data.page_layout) ? data.page_layout : [],
                        socialPreset: data.social_preset || socialPreset || 'balanced'
                    });
                } else {
                    renderSocialPreview(dom.previewFrame, imageUrls.filter(Boolean), Date.now());
                }
                return data;
            } else {
                notify(data.message || '文字图生成失败', 'error');
            }
        } catch (e) {
            console.error(e);
            notify('网络错误', 'error');
        } finally {
            dom.setButtonBusy(dom.socialImageBtn, false);
        }
        return null;
    }

    function renderWechatPreview(frame, previewUrl, cacheToken) {
        frame.removeAttribute('srcdoc');
        frame.src = withCache(previewUrl, cacheToken);
    }

    function renderSocialPreview(frame, imageUrls, cacheToken) {
        const urls = Array.isArray(imageUrls) ? imageUrls : [imageUrls];
        const imagesHtml = urls.map((imageUrl, index) => {
            const displayUrl = withCache(imageUrl, cacheToken);
            const safeDisplayUrl = escapeAttribute(displayUrl);
            const safeOpenUrl = escapeAttribute(imageUrl);
            const pageLabel = String(index + 1).padStart(2, '0');
            const totalLabel = String(urls.length).padStart(2, '0');
            return `
                <figure>
                    <a href="${safeOpenUrl}" target="_blank" rel="noopener noreferrer">
                        <img src="${safeDisplayUrl}" alt="文字图预览 ${index + 1}">
                    </a>
                    <figcaption>${pageLabel} / ${totalLabel}</figcaption>
                </figure>
            `;
        }).join('');

        frame.removeAttribute('src');
        frame.srcdoc = `
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {
                        margin: 0;
                        background: #f3f1eb;
                        color: #262823;
                        padding: 24px;
                        font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Noto Sans SC", sans-serif;
                    }
                    .summary {
                        max-width: 980px;
                        margin: 0 auto 18px;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        color: #73766f;
                        font-size: 13px;
                    }
                    .pages {
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                        gap: 22px;
                        max-width: 980px;
                        margin: 0 auto;
                        justify-items: center;
                    }
                    figure {
                        margin: 0;
                        width: min(100%, 320px);
                    }
                    a {
                        display: block;
                    }
                    img {
                        display: block;
                        width: 100%;
                        height: auto;
                        border-radius: 3px;
                        box-shadow: 0 18px 42px rgba(52, 48, 40, 0.18);
                    }
                    figcaption {
                        color: #73766f;
                        font-size: 12px;
                        line-height: 1.4;
                        margin-top: 9px;
                        text-align: center;
                    }
                </style>
            </head>
            <body>
                <div class="summary">
                    <strong>已生成 ${urls.length} 张</strong>
                    <span>PNG</span>
                </div>
                <div class="pages">${imagesHtml}</div>
            </body>
            </html>
        `;
    }

    function getArtifactUrl(data, type) {
        return getArtifactUrls(data, type)[0] || '';
    }

    function getArtifactUrls(data, type) {
        if (!Array.isArray(data.artifacts)) return [];
        return data.artifacts
            .filter(artifact => artifact.type === type && artifact.url)
            .map(artifact => artifact.url);
    }

    function withCache(url, cacheToken) {
        if (!url || !cacheToken) return url;
        return `${url}${url.includes('?') ? '&' : '?'}t=${cacheToken}`;
    }

    function escapeAttribute(value) {
        return String(value)
            .replace(/&/g, '&amp;')
            .replace(/"/g, '&quot;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
    }

    return {
        saveAndGenerate,
        generateSocialImage,
        renderWechatPreview,
        renderSocialPreview
    };
})();
