window.WriterStudioNotifications = (() => {
    function show(element, msg, type = 'success') {
        element.textContent = msg;
        element.style.backgroundColor = type === 'error' ? '#ff4d4f' : '#E6C35C';
        element.classList.add('show');
        setTimeout(() => element.classList.remove('show'), 3000);
    }

    return {
        show
    };
})();
