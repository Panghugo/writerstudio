window.WriterStudioEditor = (() => {
    function insertFormat(editor, prefix, suffix = '') {
        const start = editor.selectionStart;
        const end = editor.selectionEnd;
        const text = editor.value;
        const before = text.substring(0, start);
        const sel = text.substring(start, end);
        const after = text.substring(end);
        const scrollTop = editor.scrollTop;

        editor.value = before + prefix + sel + suffix + after;
        editor.focus();
        editor.selectionStart = start + prefix.length;
        editor.selectionEnd = end + prefix.length;
        editor.scrollTop = scrollTop;
    }

    return {
        insertFormat
    };
})();
