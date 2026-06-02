const api = window.WriterStudioApi;
const dom = window.WriterStudioDom;
const editor = window.WriterStudioEditor;
const drafts = window.WriterStudioDrafts;
const generation = window.WriterStudioGeneration;
const notifications = window.WriterStudioNotifications;
const settings = window.WriterStudioSettings;
const publishing = window.WriterStudioPublishing;
const obsidian = window.WriterStudioObsidian;
const session = window.WriterStudioSession;
const theme = window.WriterStudioTheme;
const uploads = window.WriterStudioUploads;

const OUTPUT_COPY = {
    wechat_article: {
        emptyTitle: '公众号正文预览',
        emptyDetail: '尚未生成',
        idle: '尚未生成预览',
        generated: '公众号预览已生成',
        dirty: '内容已修改，建议重新生成'
    },
    social_cards: {
        emptyTitle: '小红书文字图',
        emptyDetail: '尚未生成',
        idle: '尚未生成文字图',
        generated: count => `文字图已生成 ${count} 张`,
        dirty: '内容已修改，建议重新生成'
    }
};

const sessionId = session.getOrCreateSessionId();
const appState = {
    previewGenerated: false,
    featureImageName: '',
    outputMode: 'wechat_article',
    outputs: {
        wechat_article: {
            generated: false,
            dirty: false,
            url: '',
            cacheToken: 0
        },
        social_cards: {
            generated: false,
            dirty: false,
            imageUrls: [],
            zipUrl: '',
            qualityChecks: [],
            pageLayout: [],
            cacheToken: 0
        }
    },
    socialLayoutOverrides: {},
    socialBlockControls: {},
    socialBlockOrder: [],
    socialPreset: 'balanced'
};

theme.initialize(dom.themeSelect);
drafts.configure(sessionId);
drafts.restore(dom);
drafts.bind(dom);
configureModules();
bindEvents();
renderOutputMode();

function configureModules() {
    obsidian.configure({
        api,
        sessionId,
        notify: showNotify,
        shouldConfirmOverwrite() {
            const content = dom.editor.value.trim();
            return Boolean(content && !drafts.isDefaultContent(dom.editor.value));
        },
        onLoaded(data) {
            dom.editor.value = data.content;
            dom.filenameInput.value = data.filename;
            resetOutputs();
            drafts.saveNow(dom);
            drafts.markGenerationDirty(dom);
            renderOutputMode();
        }
    });

    uploads.configure({
        api,
        sessionId,
        notify: showNotify,
        insertFormat: insertEditorFormat,
        onFeatureUploaded(filename) {
            appState.featureImageName = filename;
            markOutputDirty('wechat_article');
            drafts.markGenerationDirty(dom);
            updateFeatureImageStatus();
            renderOutputMode();
        },
        onFeatureRemoved() {
            appState.featureImageName = '';
            markOutputDirty('wechat_article');
            drafts.markGenerationDirty(dom);
            updateFeatureImageStatus();
            renderOutputMode();
        }
    });
}

function bindEvents() {
    dom.themeSelect.addEventListener('change', () => {
        theme.saveSelectedTheme(dom.themeSelect.value);
        drafts.saveNow(dom);
        resetOutputs();
        drafts.markGenerationDirty(dom);
        generatePreview();
    });

    [dom.editor, dom.filenameInput].forEach(element => {
        element.addEventListener('input', () => {
            markAllOutputsDirty();
            renderOutputMode();
        });
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
        showNotify('设置已保存');
    });

    dom.blogPublishBtn.addEventListener('click', () => {
        publishing.publishBlog({
            api,
            dom,
            settings,
            content: dom.editor.value,
            filename: dom.filenameInput.value,
            notify: showNotify
        });
    });

    dom.wechatPublishBtn.addEventListener('click', () => {
        publishing.publishWechat({
            api,
            dom,
            settings,
            filename: dom.filenameInput.value,
            sessionId,
            theme: dom.themeSelect.value,
            notify: showNotify,
            state: appState
        });
    });

    if (dom.generateBtn) dom.generateBtn.addEventListener('click', generatePreview);
    if (dom.socialImageBtn) dom.socialImageBtn.addEventListener('click', generateSocialImage);
    if (dom.socialPresetSelect) {
        dom.socialPresetSelect.addEventListener('change', () => {
            appState.socialPreset = dom.socialPresetSelect.value || 'balanced';
            markOutputDirty('social_cards');
            renderOutputMode();
        });
    }
    if (dom.socialExportPanel) {
        dom.socialExportPanel.addEventListener('click', handleSocialExportAction);
    }
    if (dom.socialLayoutControls) {
        dom.socialLayoutControls.addEventListener('click', handleSocialBlockAction);
    }
    dom.outputTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            setOutputMode(tab.dataset.outputMode);
        });
    });
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
    if (dom.featureRemoveBtn) {
        dom.featureRemoveBtn.addEventListener('click', () => {
            uploads.removeFeatureImage();
        });
    }
    updateFeatureImageStatus();
}

function showNotify(msg, type = 'success') {
    notifications.show(dom.notification, msg, type);
}

function insertEditorFormat(prefix, suffix = '') {
    editor.insertFormat(dom.editor, prefix, suffix);
}

function generatePreview() {
    setOutputMode('wechat_article');
    generation.saveAndGenerate({
        api,
        dom,
        settings,
        sessionId,
        notify: showNotify,
        drafts,
        onSuccess(data, meta) {
            appState.previewGenerated = true;
            appState.outputs.wechat_article = {
                generated: true,
                dirty: false,
                url: meta.previewUrl,
                cacheToken: Date.now()
            };
            drafts.saveNow(dom);
            drafts.markGenerated(dom);
            renderOutputMode();
        }
    });
}

function updateFeatureImageStatus() {
    if (!dom.featureImageStatus || !dom.featureRemoveBtn) return;
    const hasFeature = Boolean(appState.featureImageName);
    dom.featureImageStatus.textContent = hasFeature
        ? `头图：${appState.featureImageName}`
        : '未设置头图';
    dom.featureImageStatus.classList.toggle('has-feature', hasFeature);
    dom.featureRemoveBtn.classList.toggle('is-hidden', !hasFeature);
}

function generateSocialImage() {
    setOutputMode('social_cards');
    generation.generateSocialImage({
        api,
        dom,
        settings,
        sessionId,
        notify: showNotify,
        layoutOverrides: appState.socialLayoutOverrides,
        blockControls: buildSocialBlockPayload(),
        socialPreset: appState.socialPreset,
        onSuccess(data, meta) {
            appState.outputs.social_cards = {
                generated: true,
                dirty: false,
                imageUrls: meta.imageUrls,
                zipUrl: meta.zipUrl || '',
                qualityChecks: meta.qualityChecks || [],
                pageLayout: meta.pageLayout || [],
                preset: meta.socialPreset || appState.socialPreset,
                cacheToken: Date.now()
            };
            renderOutputMode();
        }
    });
}

function setOutputMode(mode) {
    if (!mode) return;
    appState.outputMode = mode;
    renderOutputMode();
}

function renderOutputMode() {
    const mode = appState.outputMode;
    if (!dom.outputTabs.length || !dom.outputPanels.length || !dom.emptyPreview || !dom.previewFrame) {
        return;
    }
    updateModeChrome(mode);
    updateOutputStatuses();
    renderSocialQualityPanel();
    renderSocialExportPanel();
    renderSocialLayoutControls();

    const output = appState.outputs[mode];
    if (!output || !output.generated) {
        showEmptyState(mode);
        return;
    }

    dom.emptyPreview.classList.add('is-hidden');
    dom.previewFrame.classList.remove('is-hidden');
    if (mode === 'wechat_article') {
        generation.renderWechatPreview(dom.previewFrame, output.url, output.cacheToken);
    } else {
        generation.renderSocialPreview(dom.previewFrame, output.imageUrls, output.cacheToken);
    }
}

function updateModeChrome(mode) {
    dom.outputTabs.forEach(tab => {
        const isActive = tab.dataset.outputMode === mode;
        tab.classList.toggle('is-active', isActive);
        tab.setAttribute('aria-selected', String(isActive));
    });

    dom.outputPanels.forEach(panel => {
        panel.classList.toggle('is-active', panel.dataset.outputPanel === mode);
    });
}

function renderSocialLayoutControls() {
    if (!dom.socialLayoutControls) return;
    const blocks = applySocialBlockOrder(extractSocialBlocks(dom.editor.value));
    const images = blocks.filter(block => block.kind === 'image');
    if (appState.outputMode !== 'social_cards' || !blocks.length) {
        dom.socialLayoutControls.classList.add('is-hidden');
        dom.socialLayoutControls.replaceChildren();
        return;
    }

    dom.socialLayoutControls.classList.remove('is-hidden');
    const items = images.map(image => renderImageLayoutControl(image));
    const blockList = renderSocialBlockList(blocks);
    const pageLayout = renderSocialPageLayout();
    const children = [];
    if (items.length) {
        const title = document.createElement('div');
        title.className = 'social-layout-title';
        title.textContent = '图片排版调整';
        children.push(title, ...items);
    }
    children.push(blockList);
    if (pageLayout) children.push(pageLayout);
    dom.socialLayoutControls.replaceChildren(...children);
}

function renderSocialExportPanel() {
    if (!dom.socialExportPanel) return;
    const output = appState.outputs.social_cards;
    if (appState.outputMode !== 'social_cards' || !output.generated || output.dirty) {
        dom.socialExportPanel.classList.add('is-hidden');
        dom.socialExportPanel.replaceChildren();
        return;
    }

    dom.socialExportPanel.classList.remove('is-hidden');
    const summary = document.createElement('div');
    summary.className = 'social-export-summary';
    summary.textContent = `已生成 ${output.imageUrls.length} 张 PNG`;

    const actions = document.createElement('div');
    actions.className = 'social-export-actions';
    if (output.zipUrl) {
        const zipLink = document.createElement('a');
        zipLink.className = 'btn btn-secondary';
        zipLink.href = output.zipUrl;
        zipLink.textContent = '下载 ZIP';
        zipLink.setAttribute('download', '');
        actions.append(zipLink);
    }
    actions.append(
        socialExportButton('复制图片链接', 'copy-links'),
        socialExportButton('打开输出目录', 'open-folder')
    );
    dom.socialExportPanel.replaceChildren(summary, actions);
}

function socialExportButton(text, action) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'btn btn-secondary';
    button.dataset.socialExportAction = action;
    button.textContent = text;
    return button;
}

async function handleSocialExportAction(event) {
    const button = event.target.closest('[data-social-export-action]');
    if (!button) return;
    const action = button.dataset.socialExportAction;
    const output = appState.outputs.social_cards;
    if (action === 'copy-links') {
        const text = output.imageUrls.map(url => new URL(url, window.location.origin).href).join('\n');
        try {
            await navigator.clipboard.writeText(text);
            showNotify('图片链接已复制');
        } catch (e) {
            console.error(e);
            showNotify('复制失败', 'error');
        }
        return;
    }
    if (action === 'open-folder') {
        try {
            const data = await api.openOutputFolder({
                filename: dom.filenameInput.value,
                session_id: sessionId
            });
            showNotify(data.message || '已打开输出目录');
        } catch (e) {
            console.error(e);
            showNotify('打开输出目录失败', 'error');
        }
    }
}

function renderSocialQualityPanel() {
    if (!dom.socialQualityPanel) return;
    if (appState.outputMode !== 'social_cards') {
        dom.socialQualityPanel.classList.add('is-hidden');
        dom.socialQualityPanel.replaceChildren();
        return;
    }

    const output = appState.outputs.social_cards;
    const checks = output.generated && !output.dirty
        ? output.qualityChecks
        : buildLocalSocialQualityChecks(dom.editor.value);
    dom.socialQualityPanel.classList.remove('is-hidden');

    const title = document.createElement('div');
    title.className = 'social-quality-title';
    title.textContent = '排版检查';
    if (!checks.length) {
        const ok = document.createElement('div');
        ok.className = 'social-quality-item social-quality-ok';
        ok.textContent = '暂未发现明显问题';
        dom.socialQualityPanel.replaceChildren(title, ok);
        return;
    }
    const items = checks.slice(0, 6).map(check => {
        const item = document.createElement('div');
        item.className = `social-quality-item social-quality-${check.level || 'info'}`;
        item.textContent = check.message;
        return item;
    });
    dom.socialQualityPanel.replaceChildren(title, ...items);
}

function renderImageLayoutControl(image) {
    const row = document.createElement('div');
    row.className = 'social-layout-row';

    const label = document.createElement('div');
    label.className = 'social-layout-label';
    label.textContent = image.alt || image.src;

    const layoutSelect = document.createElement('select');
    layoutSelect.dataset.index = image.index;
    layoutSelect.dataset.field = 'layout';
    [
        ['auto', '自动'],
        ['wide', '独立图'],
        ['portrait', '竖图居中'],
        ['square', '方图居中'],
        ['side', '旁侧图卡'],
    ].forEach(([value, text]) => layoutSelect.add(new Option(text, value)));

    const sizeSelect = document.createElement('select');
    sizeSelect.dataset.index = image.index;
    sizeSelect.dataset.field = 'size';
    [
        ['auto', '自动尺寸'],
        ['small', '小'],
        ['medium', '中'],
        ['large', '大'],
    ].forEach(([value, text]) => sizeSelect.add(new Option(text, value)));

    const captionLabel = document.createElement('label');
    captionLabel.className = 'social-layout-caption';
    const captionCheckbox = document.createElement('input');
    captionCheckbox.type = 'checkbox';
    captionCheckbox.dataset.index = image.index;
    captionCheckbox.dataset.field = 'show_caption';
    captionLabel.append(captionCheckbox, document.createTextNode('显示说明'));

    const override = appState.socialLayoutOverrides[image.index] || {};
    layoutSelect.value = override.layout || 'auto';
    sizeSelect.value = override.size || 'auto';
    captionCheckbox.checked = override.show_caption !== false;

    [layoutSelect, sizeSelect, captionCheckbox].forEach(control => {
        control.addEventListener('change', updateSocialLayoutOverride);
    });

    row.append(label, layoutSelect, sizeSelect, captionLabel);

    const sliders = document.createElement('div');
    sliders.className = 'social-layout-sliders';
    [
        ['zoom', '缩放', 100, 180, 5, '%', override.zoom || 100],
        ['crop_x', '左右裁切', -100, 100, 10, '', override.crop_x || 0],
        ['crop_y', '上下裁切', -100, 100, 10, '', override.crop_y || 0],
        ['margin_top', '上留白', 0, 120, 8, 'px', override.margin_top || 0],
        ['margin_bottom', '下留白', 0, 120, 8, 'px', override.margin_bottom || 0],
    ].forEach(args => sliders.append(renderSocialRangeControl(image.index, ...args)));
    row.append(sliders);
    return row;
}

function renderSocialRangeControl(index, field, labelText, min, max, step, unit, value) {
    const wrapper = document.createElement('label');
    wrapper.className = 'social-layout-range';

    const label = document.createElement('span');
    label.textContent = labelText;

    const range = document.createElement('input');
    range.type = 'range';
    range.min = min;
    range.max = max;
    range.step = step;
    range.value = value;
    range.dataset.index = index;
    range.dataset.field = field;

    const valueLabel = document.createElement('output');
    valueLabel.textContent = `${value}${unit}`;
    range.addEventListener('input', event => {
        valueLabel.textContent = `${event.currentTarget.value}${unit}`;
        updateSocialLayoutOverride(event);
    });

    wrapper.append(label, range, valueLabel);
    return wrapper;
}

function updateSocialLayoutOverride(event) {
    const control = event.currentTarget;
    const index = control.dataset.index;
    const field = control.dataset.field;
    const current = appState.socialLayoutOverrides[index] || {
        layout: 'auto',
        size: 'auto',
        show_caption: true,
        zoom: 100,
        crop_x: 0,
        crop_y: 0,
        margin_top: 0,
        margin_bottom: 0
    };
    current[field] = field === 'show_caption' ? control.checked : normalizeSocialControlValue(field, control.value);
    appState.socialLayoutOverrides[index] = current;
    markOutputDirty('social_cards');
    updateOutputStatuses();
}

function normalizeSocialControlValue(field, value) {
    if (['zoom', 'crop_x', 'crop_y', 'margin_top', 'margin_bottom'].includes(field)) {
        return Number(value);
    }
    return value;
}

function renderSocialBlockList(blocks) {
    const section = document.createElement('div');
    section.className = 'social-block-list';

    const heading = document.createElement('div');
    heading.className = 'social-layout-title';
    heading.textContent = '文章结构';
    section.append(heading);

    blocks.slice(0, 24).forEach((block, index) => {
        const item = document.createElement('div');
        item.className = `social-block-item social-block-${block.kind}`;

        const type = document.createElement('span');
        type.className = 'social-block-type';
        type.textContent = block.kind === 'image' ? `图 ${block.index + 1}` : block.kind === 'heading' ? '标题' : '段落';

        const text = document.createElement('span');
        text.className = 'social-block-text';
        text.textContent = block.text || `第 ${index + 1} 个内容块`;

        const actions = document.createElement('div');
        actions.className = 'social-block-actions';
        const controls = appState.socialBlockControls[block.block_index] || {};
        actions.append(
            socialBlockButton('新页', 'page-break', block.block_index, controls.page_break_before),
            socialBlockButton('同页', 'keep-next', block.block_index, controls.keep_with_next),
            socialBlockButton('上移', 'move-up', block.block_index, false, index === 0),
            socialBlockButton('下移', 'move-down', block.block_index, false, index === blocks.length - 1)
        );

        item.append(type, text, actions);
        section.append(item);
    });

    if (blocks.length > 24) {
        const more = document.createElement('div');
        more.className = 'social-block-more';
        more.textContent = `还有 ${blocks.length - 24} 个内容块`;
        section.append(more);
    }

    return section;
}

function socialBlockButton(text, action, blockIndex, active = false, disabled = false) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'social-block-action';
    button.dataset.socialBlockAction = action;
    button.dataset.blockIndex = blockIndex;
    button.textContent = text;
    if (active) button.classList.add('is-active');
    if (disabled) button.disabled = true;
    return button;
}

function handleSocialBlockAction(event) {
    const button = event.target.closest('[data-social-block-action]');
    if (!button) return;
    const blockIndex = Number(button.dataset.blockIndex);
    const action = button.dataset.socialBlockAction;
    if (action === 'page-break' || action === 'keep-next') {
        const controls = appState.socialBlockControls[blockIndex] || {};
        const key = action === 'page-break' ? 'page_break_before' : 'keep_with_next';
        controls[key] = !controls[key];
        appState.socialBlockControls[blockIndex] = controls;
    } else if (action === 'move-up' || action === 'move-down') {
        moveSocialBlock(blockIndex, action === 'move-up' ? -1 : 1);
    }
    markOutputDirty('social_cards');
    renderOutputMode();
}

function moveSocialBlock(blockIndex, direction) {
    const blocks = applySocialBlockOrder(extractSocialBlocks(dom.editor.value));
    const order = blocks.map(block => block.block_index);
    const currentIndex = order.indexOf(blockIndex);
    const nextIndex = currentIndex + direction;
    if (currentIndex < 0 || nextIndex < 0 || nextIndex >= order.length) return;
    [order[currentIndex], order[nextIndex]] = [order[nextIndex], order[currentIndex]];
    appState.socialBlockOrder = order;
}

function applySocialBlockOrder(blocks) {
    if (!Array.isArray(appState.socialBlockOrder) || !appState.socialBlockOrder.length) {
        return blocks;
    }
    const positions = new Map(appState.socialBlockOrder.map((blockIndex, index) => [blockIndex, index]));
    return [...blocks].sort((a, b) => {
        const aOrder = positions.has(a.block_index) ? positions.get(a.block_index) : a.block_index;
        const bOrder = positions.has(b.block_index) ? positions.get(b.block_index) : b.block_index;
        return aOrder - bOrder;
    });
}

function buildSocialBlockPayload() {
    const blocks = applySocialBlockOrder(extractSocialBlocks(dom.editor.value));
    const payload = {};
    blocks.forEach((block, order) => {
        const controls = appState.socialBlockControls[block.block_index] || {};
        payload[block.block_index] = {
            order,
            page_break_before: !!controls.page_break_before,
            keep_with_next: !!controls.keep_with_next
        };
    });
    return payload;
}

function renderSocialPageLayout() {
    const output = appState.outputs.social_cards;
    if (!output.generated || output.dirty || !output.pageLayout.length) return null;
    const section = document.createElement('div');
    section.className = 'social-page-layout';
    const heading = document.createElement('div');
    heading.className = 'social-layout-title';
    heading.textContent = '分页结果';
    section.append(heading);

    output.pageLayout.forEach(page => {
        const row = document.createElement('div');
        row.className = 'social-page-row';
        const label = document.createElement('span');
        label.className = 'social-page-label';
        label.textContent = `第 ${page.page} 页`;
        const text = document.createElement('span');
        text.className = 'social-page-text';
        text.textContent = (page.blocks || [])
            .map(block => block.kind === 'image' ? `图:${block.text || block.block_index}` : block.text)
            .filter(Boolean)
            .join(' / ') || '空';
        row.append(label, text);
        section.append(row);
    });
    return section;
}

function extractSocialBlocks(content) {
    const blocks = [];
    const images = [];
    let blockIndex = 0;
    const pattern = /^!\[(.*?)\]\((.*?)\)(?:\{[^}]*\})?$/;
    content.split(/\r?\n/).forEach(line => {
        const trimmed = line.trim();
        if (!trimmed) return;
        const imageMatch = trimmed.match(pattern);
        if (imageMatch) {
            const image = {
                kind: 'image',
                block_index: blockIndex,
                index: images.length,
                alt: imageMatch[1].trim(),
                src: imageMatch[2].trim(),
                text: imageMatch[1].trim() || imageMatch[2].trim()
            };
            images.push(image);
            blocks.push(image);
            blockIndex += 1;
            return;
        }
        if (trimmed.startsWith('# ')) return;
        blocks.push({
            block_index: blockIndex,
            kind: trimmed.startsWith('## ') ? 'heading' : 'body',
            text: trimSocialBlockText(trimmed.replace(/^#{1,6}\s+/, '').replace(/^[-*+]\s+/, ''))
        });
        blockIndex += 1;
    });
    return blocks;
}

function buildLocalSocialQualityChecks(content) {
    const checks = [];
    const blocks = extractSocialBlocks(content);
    const images = blocks.filter(block => block.kind === 'image');
    const bodyText = content
        .split(/\r?\n/)
        .map(line => line.trim())
        .filter(line => line && !line.startsWith('![') && !line.startsWith('# '))
        .join('');

    if (bodyText.length < 120) {
        checks.push({ level: 'info', message: '正文偏短，可能更适合做单图或金句卡片。' });
    }
    if (!images.length) {
        checks.push({ level: 'info', message: '当前没有插入图片，会生成纯文字长图。' });
    }
    images.forEach(image => {
        if (!image.src) {
            checks.push({ level: 'error', message: '有图片缺少文件路径。' });
        }
        if (image.src.startsWith('http://') || image.src.startsWith('https://')) {
            checks.push({ level: 'warning', message: `远程图片「${image.src.slice(0, 22)}...」可能无法进入本地生成。` });
        }
        if ((image.alt || '').length > 42) {
            checks.push({ level: 'warning', message: `图片说明「${image.alt.slice(0, 16)}...」偏长。` });
        }
    });
    if (blocks.length > 28) {
        checks.push({ level: 'info', message: '内容块较多，生成后建议检查是否需要拆成两篇。' });
    }
    return checks;
}

function trimSocialBlockText(text) {
    const clean = text.replace(/\*\*/g, '').replace(/^>\s+/, '').trim();
    return clean.length > 34 ? `${clean.slice(0, 34)}...` : clean;
}

function updateOutputStatuses() {
    const wechatText = outputStatusText('wechat_article');
    const socialText = outputStatusText('social_cards');

    if (dom.wechatOutputStatus) dom.wechatOutputStatus.textContent = wechatText;
    if (dom.socialOutputStatus) dom.socialOutputStatus.textContent = socialText;
    if (dom.generationStatus) dom.generationStatus.textContent = outputStatusText(appState.outputMode);
}

function outputStatusText(mode) {
    const output = appState.outputs[mode];
    const copy = OUTPUT_COPY[mode];
    if (!output.generated) return copy.idle;
    if (output.dirty) return copy.dirty;
    if (mode === 'social_cards') return copy.generated(output.imageUrls.length);
    return copy.generated;
}

function showEmptyState(mode) {
    const copy = OUTPUT_COPY[mode];
    dom.previewFrame.classList.add('is-hidden');
    dom.previewFrame.removeAttribute('src');
    dom.previewFrame.removeAttribute('srcdoc');
    dom.emptyPreview.classList.remove('is-hidden');
    if (dom.emptyPreviewTitle) dom.emptyPreviewTitle.textContent = copy.emptyTitle;
    if (dom.emptyPreviewDetail) dom.emptyPreviewDetail.textContent = copy.emptyDetail;
}

function resetOutputs() {
    appState.previewGenerated = false;
    appState.outputs.wechat_article = {
        generated: false,
        dirty: false,
        url: '',
        cacheToken: 0
    };
    appState.outputs.social_cards = {
        generated: false,
        dirty: false,
        imageUrls: [],
        zipUrl: '',
        qualityChecks: [],
        pageLayout: [],
        cacheToken: 0
    };
    appState.socialLayoutOverrides = {};
    appState.socialBlockControls = {};
    appState.socialBlockOrder = [];
}

function markAllOutputsDirty() {
    markOutputDirty('wechat_article');
    markOutputDirty('social_cards');
}

function markOutputDirty(mode) {
    const output = appState.outputs[mode];
    if (!output) return;
    if (mode === 'wechat_article') appState.previewGenerated = false;
    if (output.generated) output.dirty = true;
}
