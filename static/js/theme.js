window.WriterStudioTheme = (() => {
    const STORAGE_KEY = 'ws_theme';
    const DEFAULT_THEME = 'black_gold';

    function initialize(selectElement) {
        selectElement.value = getSelectedTheme();
    }

    function getSelectedTheme() {
        return localStorage.getItem(STORAGE_KEY) || DEFAULT_THEME;
    }

    function saveSelectedTheme(theme) {
        localStorage.setItem(STORAGE_KEY, theme);
    }

    return {
        initialize,
        saveSelectedTheme
    };
})();
