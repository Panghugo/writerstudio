window.WriterStudioSession = (() => {
    const STORAGE_KEY = 'ws_session_id';

    function getOrCreateSessionId() {
        const existingSession = localStorage.getItem(STORAGE_KEY);
        if (existingSession) return existingSession;

        const nextSession = uuidv4();
        localStorage.setItem(STORAGE_KEY, nextSession);
        return nextSession;
    }

    function uuidv4() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    return {
        getOrCreateSessionId
    };
})();
