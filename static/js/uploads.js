window.WriterStudioUploads = (() => {
    let context = null;

    function configure(nextContext) {
        context = nextContext;
    }

    async function uploadImage(input) {
        if (input.files && input.files[0]) {
            try {
                const data = await context.api.uploadImage(input.files[0], context.sessionId);
                if (data.status === 'success') {
                    context.insertFormat(`![image](${data.filename})`);
                    context.notify('Image uploaded!');
                } else {
                    context.notify('Upload failed', 'error');
                }
            } catch (e) {
                console.error(e);
                context.notify('Error uploading image', 'error');
            }
        }
        input.value = '';
    }

    async function uploadFeatureImage(input) {
        if (input.files && input.files[0]) {
            try {
                context.notify('上传头图中...', 'success');
                const data = await context.api.uploadImage(input.files[0], context.sessionId, true);
                if (data.status === 'success') {
                    context.notify('✅ 头图已上传！生成时会自动拼接到文章头部');
                } else {
                    context.notify('上传失败', 'error');
                }
            } catch (e) {
                console.error(e);
                context.notify('上传头图失败', 'error');
            }
        }
        input.value = '';
    }

    return {
        configure,
        uploadImage,
        uploadFeatureImage
    };
})();
