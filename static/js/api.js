window.WriterStudioApi = (() => {
    async function postJson(url, payload) {
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        return response.json();
    }

    async function uploadImage(file, sessionId, isFeature = false) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('session_id', sessionId);
        if (isFeature) {
            formData.append('is_feature', 'true');
        }

        const response = await fetch('/api/upload_image', {
            method: 'POST',
            body: formData
        });
        return response.json();
    }

    return {
        uploadImage,
        removeFeatureImage(payload) {
            return postJson('/api/remove_feature_image', payload);
        },
        saveAndGenerate(payload) {
            return postJson('/api/save_and_generate', payload);
        },
        generateSocialImage(payload) {
            return postJson('/api/generate_social_image', payload);
        },
        publishWechat(payload) {
            return postJson('/api/publish', payload);
        },
        publishBlog(payload) {
            return postJson('/api/publish_blog', payload);
        },
        openOutputFolder(payload) {
            return postJson('/api/open_output_folder', payload);
        },
        async listObsidianFiles() {
            const response = await fetch('/api/list_obsidian_files');
            return response.json();
        },
        loadObsidianFile(payload) {
            return postJson('/api/load_obsidian_file', payload);
        }
    };
})();
