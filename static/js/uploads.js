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
                    if (context.onFeatureUploaded) context.onFeatureUploaded(data.filename);
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

    async function removeFeatureImage() {
        try {
            const data = await context.api.removeFeatureImage({
                session_id: context.sessionId
            });
            if (data.status === 'success') {
                if (context.onFeatureRemoved) context.onFeatureRemoved();
                context.notify(data.message || '头图已移除');
            } else {
                context.notify(data.message || '移除头图失败', 'error');
            }
        } catch (e) {
            console.error(e);
            context.notify('移除头图失败', 'error');
        }
    }

    return {
        configure,
        uploadImage,
        uploadFeatureImage,
        removeFeatureImage
    };
})();
