window.WriterStudioSettings = (() => {
    const modal = document.getElementById('settings-modal');
    const appIdInput = document.getElementById('st-appid');
    const appSecretInput = document.getElementById('st-secret');
    const authorInput = document.getElementById('st-author');
    const serverConfig = readServerConfig();

    function readServerConfig() {
        const configElement = document.getElementById('server-config');
        if (!configElement) return {};

        try {
            return JSON.parse(configElement.textContent || '{}');
        } catch (e) {
            console.warn('Unable to parse server config', e);
            return {};
        }
    }

    function storedOrServerValue(storageKey, configKey) {
        return localStorage.getItem(storageKey) || serverConfig[configKey] || '';
    }

    function getConfig() {
        return {
            app_id: storedOrServerValue('ws_app_id', 'app_id'),
            app_secret: storedOrServerValue('ws_app_secret', 'app_secret'),
            author_name: storedOrServerValue('ws_author_name', 'author_name')
        };
    }

    function getAuthorName(defaultName = '') {
        return localStorage.getItem('ws_author_name') || defaultName;
    }

    function open() {
        const config = getConfig();
        appIdInput.value = config.app_id;
        appSecretInput.value = config.app_secret;
        authorInput.value = config.author_name;
        modal.style.display = 'flex';
    }

    function close() {
        modal.style.display = 'none';
    }

    function save() {
        const config = {
            app_id: appIdInput.value.trim(),
            app_secret: appSecretInput.value.trim(),
            author_name: authorInput.value.trim()
        };

        localStorage.setItem('ws_app_id', config.app_id);
        localStorage.setItem('ws_app_secret', config.app_secret);
        localStorage.setItem('ws_author_name', config.author_name);
        close();
        return config;
    }

    return {
        getConfig,
        getAuthorName,
        open,
        close,
        save
    };
})();
