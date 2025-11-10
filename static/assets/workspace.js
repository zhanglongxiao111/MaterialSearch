const WorkspaceApp = Vue.createApp({
    data() {
        const savedLibrary = localStorage.getItem('currentLibrary') || 'permanent';
        const allowedGroupIds = ['images', 'videos', 'frames', 'queue'];
        const savedGroup = localStorage.getItem('workspace-permanent-group');
        const initialGroup = allowedGroupIds.includes(savedGroup) ? savedGroup : 'images';
        const savedThumb = Number(localStorage.getItem('workspace-thumb-scale'));
        const normalizedThumb = Number.isFinite(savedThumb)
            ? (savedThumb > 6 ? Math.min(6, Math.max(2, Math.round(savedThumb / 30))) : savedThumb)
            : 4;
        return {
            sidebarLibrary: savedLibrary === 'permanent' ? 'permanent' : 'project',
            projects: [],
            currentLibrary: savedLibrary,
            permanentGroupMeta: [
                { id: 'images', name: '全部图片', field: 'total_images', description: '永久库已索引图片', path: '' },
                { id: 'videos', name: '视频素材', field: 'total_videos', description: '永久库视频素材', path: '' },
                { id: 'frames', name: '视频帧', field: 'total_video_frames', description: '提取的视频帧样本', path: '' },
                { id: 'queue', name: '扫描队列', field: 'scanning_files', description: '等待扫描的文件数', path: '' }
            ],
            activePermanentGroup: initialGroup,
            files: [],
            isLoading: false,
            lastSearchError: '',
            activeTab: 'search',
            advancedOpen: false,
            viewMode: localStorage.getItem('workspace-view-mode') || 'masonry',
            thumbnailScale: normalizedThumb || 4,
            searchModes: [
                { value: 0, label: '文本', icon: 'type', searchType: 0, description: '文本搜索图片' },
                { value: 1, label: '图片', icon: 'image', searchType: 1, description: '相似图检索（即将上线）', disabled: true },
                { value: 2, label: '视频', icon: 'film', searchType: 2, description: '文本搜索视频' }
            ],
            searchMode: Number(localStorage.getItem('workspace-search-mode') || 0),
            form: {
                positive: '',
                negative: '',
                top_n: localStorage.getItem('workspace-top-n') || '30',
                path: '',
                library_type: 'permanent',
                project_id: null,
                search_type: 0,
                positive_threshold: Number(localStorage.getItem('form.positive_threshold') || 20),
                negative_threshold: Number(localStorage.getItem('form.negative_threshold') || 30),
                image_threshold: Number(localStorage.getItem('form.image_threshold') || 75),
                img_id: -1,
                start_time: 0,
                end_time: 0
            },
            themeMode: localStorage.getItem('workspace-theme') || 'auto',
            timeFilterLabel: '',
            toast: {
                message: '',
                type: '',
                visible: false,
                timer: null
            },
            statusSummary: {
                total_images: 0,
                total_videos: 0,
                total_video_frames: 0,
                scanning_files: 0,
                remain_files: 0,
                progress: 0
            },
            statusTimer: null,
            detailDialog: {
                visible: false,
                item: null,
                viewer: null
            },
            selectedIds: [],
            selectionProjectId: null,
            actionLoading: false,
            uploadStep: 0,
            uploadPathInput: '',
            uploadHistory: [],
            uploadHistoryKey: 'materialPathHistory',
            uploadLoadingPreview: false,
            uploadPreviewFiles: [],
            uploadFilter: 'all',
            uploadSelectedPaths: [],
            uploadTaskId: null,
            uploadTaskInfo: {
                total: 0,
                processed: 0,
                success: 0,
                failed: [],
                duplicates: [],
                status: ''
            },
            uploadTaskProgress: 0,
            uploadTaskStatus: '',
            uploadCurrentFile: '',
            uploadPollingTimer: null,
            uploadShowDetails: false,
            uploadActiveDetails: [],
            uploadCancelling: false,
            uploadDuplicateDialog: {
                visible: false,
                payload: null,
                remember: false,
                loading: false
            }
        };
    },
    computed: {
        permanentGroups() {
            return this.permanentGroupMeta.map((meta) => {
                const value = Number(this.statusSummary[meta.field] || 0);
                return {
                    ...meta,
                    countValue: value,
                    countDisplay: this.formatNumber(value)
                };
            });
        },
        activeGroupName() {
            const group = this.permanentGroups.find((g) => g.id === this.activePermanentGroup);
            return group ? group.name : '全部素材';
        },
        scopeHeadline() {
            if (this.currentLibrary === 'permanent') {
                return `永久库 · ${this.activeGroupName}`;
            }
            return `项目库 · ${this.currentProject?.name || '未命名'}`;
        },
        scopeDescription() {
            if (this.currentLibrary === 'permanent') {
                const group = this.permanentGroups.find((g) => g.id === this.activePermanentGroup);
                const count = group ? group.countDisplay : this.formatNumber(this.statusSummary.total_images);
                return `${this.activeGroupName} · ${count}`;
            }
            const project = this.currentProject;
            if (!project) {
                return '项目库 · 暂无项目';
            }
            return `${project.name} · 图片 ${this.formatNumber(project.image_count)} · 视频 ${this.formatNumber(project.video_count)}`;
        },
        currentProject() {
            return this.projects.find((p) => p.id === this.currentLibrary);
        },
        themeLabel() {
            if (this.themeMode === 'auto') return '系统自动';
            if (this.themeMode === 'light') return '浅色';
            return '深色';
        },
        columnCount() {
            return Math.min(6, Math.max(2, Math.round(this.thumbnailScale)));
        },
        resultsWrapperStyle() {
            if (this.viewMode === 'grid') {
                return {
                    display: 'grid',
                    gridTemplateColumns: `repeat(${this.columnCount}, minmax(180px, 1fr))`,
                    gap: '16px'
                };
            }
            return { columnCount: this.columnCount };
        },
        statusChips() {
            return [
                { label: '图片素材', value: this.formatNumber(this.statusSummary.total_images), hint: '永久库' },
                { label: '视频素材', value: this.formatNumber(this.statusSummary.total_videos), hint: '永久库' },
                { label: '视频帧', value: this.formatNumber(this.statusSummary.total_video_frames), hint: '帧索引' },
                { label: '扫描队列', value: `${this.formatNumber(this.statusSummary.scanning_files)} / ${this.formatNumber(this.statusSummary.remain_files)}`, hint: '排队 / 剩余' }
            ];
        },
        scopeStats() {
            if (this.currentLibrary === 'permanent') {
                return [
                    { label: '图片', value: this.formatNumber(this.statusSummary.total_images) },
                    { label: '视频', value: this.formatNumber(this.statusSummary.total_videos) },
                    { label: '帧数', value: this.formatNumber(this.statusSummary.total_video_frames) }
                ];
            }
            const project = this.currentProject;
            if (!project) return [];
            return [
                { label: '项目图片', value: this.formatNumber(project.image_count) },
                { label: '项目视频', value: this.formatNumber(project.video_count) },
                { label: '占用空间', value: project.total_size ? this.formatBytes(project.total_size) : '--' }
            ];
        },
        detailImageSrc() {
            if (!this.detailDialog.item) return '';
            return this.resultImage(this.detailDialog.item);
        },
        detailItemName() {
            if (!this.detailDialog.item) return '';
            return this.formatName(this.detailDialog.item);
        },
        detailMetadata() {
            if (!this.detailDialog.item) return [];
            const item = this.detailDialog.item;
            const meta = [
                { label: '来源', value: this.formatSource(item) },
                { label: '匹配度', value: this.formatScore(item.score) },
                { label: '库类型', value: item.library_type === 'project' ? '项目库' : '永久库' }
            ];
            if (item.project_id) {
                meta.push({ label: '所属项目', value: item.project_id });
            }
            if (item.size) {
                meta.push({ label: '文件大小', value: this.formatBytes(item.size) });
            }
            if (item.width && item.height) {
                meta.push({ label: '分辨率', value: `${item.width} × ${item.height}` });
            }
            if (item.captured_at) {
                meta.push({ label: '采集时间', value: this.formatTimestamp(item.captured_at) });
            }
            return meta;
        },

        isProjectMode() {
            return this.currentLibrary !== 'permanent';
        },
        selectedCount() {
            return this.selectedIds.length;
        },
        selectionVisible() {
            return this.activeTab === 'search' && this.selectedCount > 0;
        },
        canArchiveSelected() {
            return this.selectionVisible && this.isProjectMode;
        },
        canDeleteSelected() {
            return this.selectionVisible && this.isProjectMode;
        },
        selectedItems() {
            if (!this.selectedIds.length) return [];
            const lookup = new Map(this.files.map(item => [String(item.id), item]));
            return this.selectedIds.map(id => lookup.get(id)).filter(Boolean);
        },
        skeletonCount() {
            return this.viewMode === 'grid' ? 8 : 6;
        },
        filteredUploadFiles() {
            if (!this.uploadPreviewFiles.length) return [];
            if (this.uploadFilter === 'image') {
                return this.uploadPreviewFiles.filter((file) => file.type === 'image');
            }
            if (this.uploadFilter === 'video') {
                return this.uploadPreviewFiles.filter((file) => file.type === 'video');
            }
            return this.uploadPreviewFiles;
        },
        uploadSelectedFiles() {
            if (!this.uploadSelectedPaths.length) return [];
            const selected = new Set(this.uploadSelectedPaths);
            return this.uploadPreviewFiles.filter((file) => selected.has(file.path));
        },
        uploadSelectedCount() {
            return this.uploadSelectedPaths.length;
        },
        uploadSelectedSize() {
            return this.uploadSelectedFiles.reduce((total, file) => {
                const size = Number(file.size || 0);
                return total + (Number.isNaN(size) ? 0 : size);
            }, 0);
        },
        duplicateNewFile() {
            const payload = this.uploadDuplicateDialog.payload;
            if (payload && payload.new_file) {
                return payload.new_file;
            }
            return null;
        },
        duplicateExistingFile() {
            const payload = this.uploadDuplicateDialog.payload;
            if (payload && payload.existing_file) {
                return payload.existing_file;
            }
            return null;
        }
    },

    watch: {
        currentLibrary(val) {
            localStorage.setItem('currentLibrary', val);
            this.sidebarLibrary = val === 'permanent' ? 'permanent' : 'project';
            this.syncScopeToForm();
            this.clearSelection();
            this.refreshUploadHistory();
            this.resetUploadWizard({ keepInput: false });
        },
        searchMode(val) {
            localStorage.setItem('workspace-search-mode', val);
            this.form.search_type = this.resolveSearchType(val);
        },
        viewMode(val) {
            localStorage.setItem('workspace-view-mode', val);
        },
        thumbnailScale(val) {
            localStorage.setItem('workspace-thumb-scale', val);
        },
        'form.top_n'(val) {
            localStorage.setItem('workspace-top-n', val);
        },
        'detailDialog.visible'(val) {
            if (val) {
                this.$nextTick(() => this.initDetailViewer());
            } else {
                this.destroyDetailViewer();
            }
        },
        'detailDialog.item'(val) {
            if (val && this.detailDialog.visible) {
                this.$nextTick(() => this.initDetailViewer());
            }
        },
        'files'() {
            this.syncSelection();
        },
        activeTab(val) {
            if (val !== 'search') {
                this.clearSelection();
            }
            if (val !== 'upload') {
                this.uploadDuplicateDialog.visible = false;
            }
        },
        uploadPreviewFiles() {
            this.syncUploadSelection();
        }
    },

    mounted() {
        document.body.classList.add('workspace');
        this.sidebarLibrary = this.currentLibrary === 'permanent' ? 'permanent' : 'project';
        this.form.search_type = this.resolveSearchType(this.searchMode);
        this.syncScopeToForm();
        this.refreshUploadHistory();
        this.applyTheme();
        this.loadProjects();
        this.loadStatus();
        this.statusTimer = setInterval(() => this.loadStatus(), 15000);
        this.refreshIcons();
    },
    beforeUnmount() {
        if (this.statusTimer) {
            clearInterval(this.statusTimer);
            this.statusTimer = null;
        }
        this.destroyDetailViewer();
        this.clearUploadPolling();
    },
    methods: {
        resolveSearchType(modeValue) {
            const mode = this.searchModes.find((item) => item.value === modeValue);
            return mode ? mode.searchType : 0;
        },
        async loadProjects() {
            try {
                const { data } = await axios.get('/api/projects');
                if (data?.success) {
                    this.projects = (data.data || []).map((p) => ({
                        ...p,
                        image_count: p.image_count || 0,
                        video_count: p.video_count || 0,
                        total_size: p.total_size || 0
                    }));
                } else {
                    this.projects = [];
                    this.showToast('error', data?.error || '加载项目列表失败');
                }
            } catch (error) {
                console.error('加载项目列表失败', error);
                this.projects = [];
                this.showToast('error', '加载项目列表失败');
            } finally {
                if (this.currentLibrary !== 'permanent') {
                    const exists = this.projects.some((project) => project.id === this.currentLibrary);
                    if (!exists) {
                        this.currentLibrary = this.projects[0]?.id || 'permanent';
                    }
                }
                this.sidebarLibrary = this.currentLibrary === 'permanent' ? 'permanent' : 'project';
                this.syncScopeToForm();
            }
        },
        async loadStatus() {
            try {
                const { data } = await axios.get('/api/status');
                if (data) {
                    this.statusSummary = {
                        total_images: Number(data.total_images || 0),
                        total_videos: Number(data.total_videos || 0),
                        total_video_frames: Number(data.total_video_frames || 0),
                        scanning_files: Number(data.scanning_files || 0),
                        remain_files: Number(data.remain_files || 0),
                        progress: Number(data.progress || 0)
                    };
                }
            } catch (error) {
                console.error('加载状态失败', error);
            }
        },
        syncScopeToForm() {
            if (this.currentLibrary === 'permanent') {
                this.form.library_type = 'permanent';
                this.form.project_id = null;
            } else {
                this.form.library_type = 'project';
                this.form.project_id = this.currentLibrary;
            }
        },
        switchSidebar(type) {
            this.sidebarLibrary = type;
            if (type === 'permanent') {
                this.currentLibrary = 'permanent';
            } else if (this.projects.length > 0) {
                this.currentLibrary = this.projects[0].id;
            } else {
                this.showToast('warning', '当前没有可用项目，请先在经典界面创建项目');
            }
            this.clearSelection();
        },
        selectPermanentGroup(group) {
            this.activePermanentGroup = group.id;
            this.form.path = group.path || '';
            localStorage.setItem('workspace-permanent-group', group.id);
            this.currentLibrary = 'permanent';
            this.clearSelection();
        },
        selectProject(project) {
            this.currentLibrary = project.id;
            this.activeTab = 'search';
            this.clearSelection();
        },
        selectSearchMode(modeValue) {
            const mode = this.searchModes.find((item) => item.value === modeValue);
            if (mode?.disabled) {
                this.showToast('info', '图片相似搜索将在下一阶段开放，可先使用经典 UI');
                return;
            }
            this.searchMode = modeValue;
        },
        setActiveTab(tab) {
            this.activeTab = tab;
        },
        setViewMode(mode) {
            this.viewMode = mode;
        },
        copyAllPaths() {
            if (!this.files.length) {
                this.showToast('warning', '没有可复制的路径');
                return;
            }
            const text = this.files.map((file) => file.path).filter(Boolean).join('\n');
            this.copyText(text, '已复制全部路径');
        },
        copyPath(path) {
            if (!path) {
                this.showToast('warning', '无可用路径');
                return;
            }
            this.copyText(path, '路径已复制');
        },
        copyText(text, successMessage) {
            if (!navigator.clipboard) {
                this.fallbackCopy(text, successMessage);
                return;
            }
            navigator.clipboard.writeText(text).then(
                () => this.showToast('success', successMessage),
                () => this.fallbackCopy(text, successMessage)
            );
        },
        fallbackCopy(text, successMessage) {
            const textarea = document.createElement('textarea');
            textarea.value = text;
            textarea.style.position = 'fixed';
            textarea.style.opacity = '0';
            document.body.appendChild(textarea);
            textarea.select();
            try {
                document.execCommand('copy');
                this.showToast('success', successMessage);
            } catch (err) {
                this.showToast('error', '复制失败，请手动复制');
                console.error('复制失败', err);
            } finally {
                document.body.removeChild(textarea);
            }
        },
        applyTimeFilter(days) {
            const now = Math.floor(Date.now() / 1000);
            this.form.end_time = now;
            this.form.start_time = now - days * 24 * 60 * 60;
            this.timeFilterLabel = `最近${days}天`;
        },
        clearTimeFilter() {
            this.form.start_time = 0;
            this.form.end_time = 0;
            this.timeFilterLabel = '';
        },
        async search() {
            if (this.isLoading) return;
            if (!this.form.positive && !this.form.path) {
                this.showToast('warning', '请输入关键词或限定路径');
                return;
            }
            if (this.form.library_type === 'project' && !this.form.project_id) {
                this.showToast('warning', '请选择一个项目后再搜索');
                return;
            }
            this.isLoading = true;
            this.lastSearchError = '';
            this.clearSelection();
            const payload = {
                ...this.form,
                positive: this.form.positive.trim(),
                negative: this.form.negative.trim(),
                top_n: parseInt(this.form.top_n, 10) || 30,
                search_type: this.resolveSearchType(this.searchMode)
            };
            try {
                const { data } = await axios.post('/api/match', payload);
                if (Array.isArray(data)) {
                    this.files = data.map((item, index) => this.normalizeResult(item, index));
                    this.showToast('success', `共 ${this.files.length} 条结果`);
                } else {
                    this.files = [];
                    this.showToast('warning', '没有找到匹配的素材');
                }
            } catch (error) {
                console.error('搜索失败', error);
                this.files = [];
                this.lastSearchError = error?.response?.data?.error || '搜索失败，请稍后重试';
                this.showToast('error', this.lastSearchError);
            } finally {
                this.isLoading = false;
                this.refreshIcons();
            }
        },
        normalizeResult(item, index) {
            const libraryType = item.library_type || (this.form.library_type || 'permanent');
            const projectId = item.project_id || (libraryType === 'project' ? this.form.project_id : null);
            return {
                id: item.id ?? `${item.path || 'result'}-${index}`,
                path: item.path || '',
                url: item.url || '',
                thumbnail: item.thumbnail || item.preview || item.url || '',
                filename: item.filename || '',
                source: item.source || (libraryType === 'permanent' ? '永久库' : '项目库'),
                score: typeof item.score === 'number' ? item.score : parseFloat(item.score) || null,
                library_type: libraryType,
                project_id: projectId,
                size: item.size || item.file_size || item.filesize || 0,
                width: item.width,
                height: item.height,
                captured_at: item.captured_at || item.created_at || item.timestamp || null
            };
        },
        formatScore(score) {
            if (score === null || score === undefined || Number.isNaN(score)) {
                return '--';
            }
            const percent = score > 1 ? score : score * 100;
            return `${Math.round(percent)}%`;
        },
        formatName(item) {
            if (item.filename) return item.filename;
            if (!item.path) return '未命名素材';
            const normalized = item.path.replace(/\\/g, '/');
            return normalized.split('/').pop() || '未命名素材';
        },
        formatSource(item) {
            if (item.source) return item.source;
            return item.library_type === 'project' ? '项目库' : '永久库';
        },
        resultImage(item) {
            if (item.thumbnail) return item.thumbnail;
            if (item.url) return item.url;
            return '';
        },
        cycleTheme() {
            const next = this.themeMode === 'auto' ? 'light' : this.themeMode === 'light' ? 'dark' : 'auto';
            this.themeMode = next;
            localStorage.setItem('workspace-theme', next);
            this.applyTheme();
        },
        applyTheme() {
            const html = document.documentElement;
            html.dataset.theme = this.themeMode;
            html.style.colorScheme = this.themeMode === 'auto' ? '' : this.themeMode;
        },
        openClassic() {
            window.location.href = '/classic';
        },
        showToast(type, message) {
            this.toast.type = type;
            this.toast.message = message;
            this.toast.visible = true;
            if (this.toast.timer) {
                clearTimeout(this.toast.timer);
            }
            this.toast.timer = setTimeout(() => {
                this.toast.visible = false;
                this.toast.timer = null;
            }, 3200);
        },
        refreshIcons() {
            this.$nextTick(() => {
                if (window.lucide?.createIcons) {
                    window.lucide.createIcons();
                }
            });
        },
        formatNumber(value) {
            if (value === undefined || value === null) return '--';
            const num = Number(value);
            if (Number.isNaN(num)) return '--';
            return num.toLocaleString('zh-CN');
        },
        formatBytes(bytes) {
            const num = Number(bytes);
            if (Number.isNaN(num) || num < 0) return '--';
            if (num === 0) return '0 B';
            if (num < 1024) return `${num} B`;
            const units = ['KB', 'MB', 'GB', 'TB'];
            let value = num;
            let unitIndex = -1;
            do {
                value /= 1024;
                unitIndex++;
            } while (value >= 1024 && unitIndex < units.length - 1);
            return `${value.toFixed(1)} ${units[unitIndex]}`;
        },
        formatTimestamp(ts) {
            if (!ts) return '--';
            const date = new Date(ts);
            if (Number.isNaN(date.getTime())) return ts;
            return date.toLocaleString('zh-CN');
        },
        openDetail(item) {
            this.detailDialog.item = { ...item };
            this.detailDialog.visible = true;
            this.$nextTick(() => this.refreshIcons());
        },
        closeDetail() {
            this.detailDialog.visible = false;
            this.detailDialog.item = null;
        },
        initDetailViewer() {
            if (!window.Viewer || !this.$refs.detailViewer) {
                return;
            }
            this.destroyDetailViewer();
            this.detailDialog.viewer = new window.Viewer(this.$refs.detailViewer, {
                inline: true,
                navbar: false,
                toolbar: {
                    zoomIn: true,
                    zoomOut: true,
                    oneToOne: true,
                    reset: true,
                    rotateLeft: true,
                    rotateRight: true,
                    flipHorizontal: true,
                    flipVertical: true
                },
                tooltip: false,
                movable: true,
                rotatable: true,
                scalable: true,
                transition: false
            });
        },
        destroyDetailViewer() {
            if (this.detailDialog.viewer) {
                this.detailDialog.viewer.destroy();
                this.detailDialog.viewer = null;
            }
        },
        isProjectResult(item) {
            const libraryType = item.library_type || this.form.library_type || 'permanent';
            return libraryType === 'project' || Boolean(item.project_id);
        },
        toggleSelection(item) {
            if (!this.isProjectResult(item) || !this.isProjectMode) {
                this.showToast('info', '仅项目素材支持选择');
                return;
            }
            const itemId = item.id != null ? String(item.id) : null;
            const projectId = item.project_id || this.currentLibrary;
            if (!itemId) {
                this.showToast('warning', '当前素材缺少 ID，无法操作');
                return;
            }
            if (this.selectionProjectId && this.selectionProjectId !== projectId) {
                this.showToast('info', '不同项目的素材请分批操作');
                return;
            }
            const exists = this.selectedIds.includes(itemId);
            if (exists) {
                this.selectedIds = this.selectedIds.filter(id => id !== itemId);
                if (!this.selectedIds.length) {
                    this.selectionProjectId = null;
                }
            } else {
                this.selectedIds = [...this.selectedIds, itemId];
                this.selectionProjectId = projectId;
            }
        },
        isSelected(item) {
            const itemId = item.id != null ? String(item.id) : null;
            if (!itemId) return false;
            return this.selectedIds.includes(itemId);
        },
        clearSelection() {
            this.selectedIds = [];
            this.selectionProjectId = null;
        },
        syncSelection() {
            if (!this.selectedIds.length) return;
            const availableIds = new Set(this.files.map(item => String(item.id)));
            const filtered = this.selectedIds.filter(id => availableIds.has(id));
            if (filtered.length !== this.selectedIds.length) {
                this.selectedIds = filtered;
                if (!filtered.length) {
                    this.selectionProjectId = null;
                }
            }
        },
        extractActionIds(items) {
            return Array.from(new Set(items
                .map(item => item.id)
                .filter(id => id !== undefined && id !== null)
                .map(id => Number(id))));
        },
        archiveItems(items) {
            if (!items || !items.length) return;
            const projectId = this.selectionProjectId || this.currentLibrary;
            if (!this.isProjectMode || projectId === 'permanent') {
                this.showToast('info', '仅项目素材支持归档');
                return;
            }
            const ids = this.extractActionIds(items);
            if (!ids.length) {
                this.showToast('warning', '所选素材缺少 ID，无法归档');
                return;
            }
            this.performAction('archive', ids, (targetProjectId, payloadIds) => {
                return axios.post(`/api/projects/${targetProjectId}/archive`, {
                    image_ids: payloadIds,
                    mark_archived: true
                });
            });
        },
        archiveSelected() {
            this.archiveItems(this.selectedItems);
        },
        deleteItems(items) {
            if (!items || !items.length) return;
            const projectId = this.selectionProjectId || this.currentLibrary;
            if (!this.isProjectMode || projectId === 'permanent') {
                this.showToast('info', '仅项目素材支持删除');
                return;
            }
            const ids = this.extractActionIds(items);
            if (!ids.length) {
                this.showToast('warning', '所选素材缺少 ID，无法删除');
                return;
            }
            this.performAction('delete', ids, (targetProjectId, payloadIds) => {
                return axios.post(`/api/projects/${targetProjectId}/images/delete`, {
                    image_ids: payloadIds
                });
            });
        },
        deleteSelected() {
            this.deleteItems(this.selectedItems);
        },
        async performAction(actionName, ids, handler) {
            if (!ids.length) return;
            const projectId = this.selectionProjectId || this.currentLibrary;
            this.actionLoading = true;
            try {
                const response = await handler(projectId, ids);
                if (response.data?.success) {
                    this.removeItemsByIds(ids);
                    this.clearSelection();
                    this.loadStatus();
                    this.loadProjects();
                    const payload = response.data?.data;
                    let message = actionName === 'delete' ? '删除成功' : '归档指令已发送';
                    if (payload && typeof payload.deleted === 'number') {
                        message = `已删除 ${payload.deleted} 项素材`;
                    } else if (payload && typeof payload.success === 'number') {
                        message = `已归档 ${payload.success} 项素材`;
                    }
                    this.showToast('success', message);
                } else {
                    this.showToast('error', response.data?.error || '操作失败');
                }
            } catch (error) {
                console.error('操作失败', error);
                this.showToast('error', error.response?.data?.error || '操作失败');
            } finally {
                this.actionLoading = false;
            }
        },
        removeItemsByIds(ids) {
            if (!ids.length) return;
            const idSet = new Set(ids.map(id => Number(id)));
            this.files = this.files.filter(item => !idSet.has(Number(item.id)));
        },
        handleUploadPathPaste() {
            setTimeout(() => {
                const lines = this.uploadPathInput
                    .split('\n')
                    .map((line) => line.trim().replace(/^["']|["']$/g, ''))
                    .filter(Boolean);
                this.uploadPathInput = lines.join('\n');
            }, 10);
        },
        clearUploadInput() {
            this.uploadPathInput = '';
        },
        loadUploadHistoryStore() {
            try {
                return JSON.parse(localStorage.getItem(this.uploadHistoryKey) || '[]');
            } catch (error) {
                console.warn('无法解析历史路径', error);
                return [];
            }
        },
        saveUploadHistoryStore(store) {
            localStorage.setItem(this.uploadHistoryKey, JSON.stringify(store));
        },
        refreshUploadHistory() {
            const store = this.loadUploadHistoryStore();
            const entry = store.find((item) => item.project === this.currentLibrary);
            const paths = entry ? entry.paths : [];
            this.uploadHistory = paths.map((item) => ({
                path: item.path,
                updatedAt: item.updatedAt,
                timeLabel: this.formatHistoryTime(item.updatedAt)
            }));
        },
        persistUploadPaths(paths) {
            if (!paths || !paths.length) return;
            const store = this.loadUploadHistoryStore();
            const project = this.currentLibrary;
            let entry = store.find((item) => item.project === project);
            if (!entry) {
                entry = { project, paths: [] };
                store.push(entry);
            }
            const now = Date.now();
            paths.forEach((rawPath) => {
                const normalized = rawPath.trim();
                if (!normalized) return;
                entry.paths = entry.paths.filter((item) => item.path !== normalized);
                entry.paths.unshift({ path: normalized, updatedAt: now });
            });
            entry.paths = entry.paths.slice(0, 10);
            this.saveUploadHistoryStore(store);
            this.refreshUploadHistory();
        },
        applyUploadHistory(path) {
            if (!path) return;
            const lines = this.uploadPathInput
                ? this.uploadPathInput.split('\n').map((line) => line.trim()).filter(Boolean)
                : [];
            if (!lines.includes(path)) {
                lines.push(path);
            }
            this.uploadPathInput = lines.join('\n');
        },
        resetUploadWizard(options = {}) {
            const { keepInput = false } = options;
            this.clearUploadPolling();
            this.uploadStep = 0;
            if (!keepInput) {
                this.uploadPathInput = '';
            }
            this.uploadPreviewFiles = [];
            this.uploadFilter = 'all';
            this.uploadSelectedPaths = [];
            this.uploadTaskId = null;
            this.uploadTaskInfo = { total: 0, processed: 0, success: 0, failed: [], duplicates: [] };
            this.uploadTaskProgress = 0;
            this.uploadTaskStatus = '';
            this.uploadCurrentFile = '';
            this.uploadShowDetails = false;
            this.uploadActiveDetails = [];
            this.uploadCancelling = false;
            this.uploadDuplicateDialog.visible = false;
            this.uploadDuplicateDialog.payload = null;
            this.uploadDuplicateDialog.remember = false;
            this.uploadDuplicateDialog.loading = false;
        },
        async previewUploadFiles() {
            const input = this.uploadPathInput.trim();
            if (!input) {
                this.showToast('warning', '请输入文件或文件夹路径');
                return;
            }
            const paths = Array.from(new Set(
                input
                    .split('\n')
                    .map((line) => line.trim())
                    .filter(Boolean)
            ));
            if (!paths.length) {
                this.showToast('warning', '未检测到有效路径');
                return;
            }
            this.uploadLoadingPreview = true;
            this.uploadShowDetails = false;
            try {
                const target = this.currentLibrary === 'permanent' ? 'permanent' : this.currentLibrary;
                const response = await axios.post('/api/preview_files', {
                    paths,
                    target
                });
                const result = Array.isArray(response.data) ? response.data : [];
                this.uploadPreviewFiles = result.map((item) => ({
                    ...item,
                    thumbnailUrl: item.thumbnailUrl || null
                }));
                this.uploadSelectedPaths = this.uploadPreviewFiles
                    .filter((file) => !file.is_indexed)
                    .map((file) => file.path);
                this.uploadFilter = 'all';
                this.uploadStep = 1;
                this.persistUploadPaths(paths);
                this.showToast('success', `已扫描到 ${this.uploadPreviewFiles.length} 个文件`);
            } catch (error) {
                console.error('预览文件失败', error);
                this.showToast('error', error.response?.data?.error || '预览文件失败');
            } finally {
                this.uploadLoadingPreview = false;
            }
        },
        setUploadFilter(filter) {
            this.uploadFilter = filter;
        },
        selectAllUploadFiles() {
            const filteredPaths = this.filteredUploadFiles.map((file) => file.path);
            const unaffected = this.uploadSelectedPaths.filter(
                (path) => !this.filteredUploadFiles.some((file) => file.path === path)
            );
            this.uploadSelectedPaths = [...new Set([...unaffected, ...filteredPaths])];
        },
        invertUploadSelection() {
            const current = new Set(this.uploadSelectedPaths);
            const updated = this.filteredUploadFiles.map((file) => {
                const shouldSelect = !current.has(file.path);
                if (shouldSelect) {
                    return file.path;
                }
                return null;
            }).filter(Boolean);
            const unaffected = this.uploadSelectedPaths.filter(
                (path) => !this.filteredUploadFiles.some((file) => file.path === path)
            );
            this.uploadSelectedPaths = [...new Set([...unaffected, ...updated])];
        },
        toggleUploadSelection(file) {
            if (!file?.path) return;
            if (this.uploadSelectedPaths.includes(file.path)) {
                this.uploadSelectedPaths = this.uploadSelectedPaths.filter((path) => path !== file.path);
            } else {
                this.uploadSelectedPaths = [...this.uploadSelectedPaths, file.path];
            }
        },
        isUploadSelected(file) {
            if (!file?.path) return false;
            return this.uploadSelectedPaths.includes(file.path);
        },
        syncUploadSelection() {
            if (!this.uploadSelectedPaths.length) return;
            const available = new Set(this.uploadPreviewFiles.map((file) => file.path));
            this.uploadSelectedPaths = this.uploadSelectedPaths.filter((path) => available.has(path));
        },
        async startUploadIndex() {
            if (!this.uploadSelectedPaths.length) {
                this.showToast('warning', '请至少选择一个文件');
                return;
            }
            const selectedSet = new Set(this.uploadSelectedPaths);
            const files = this.uploadPreviewFiles.filter((file) => selectedSet.has(file.path));
            if (!files.length) {
                this.showToast('warning', '所选文件已失效，请重新扫描');
                return;
            }
            try {
                const target = this.currentLibrary === 'permanent' ? 'permanent' : this.currentLibrary;
                const response = await axios.post('/api/batch_index', {
                    files,
                    target,
                    duplicate_strategy: 'ask'
                });
                this.uploadTaskId = response.data?.task_id || null;
                if (!this.uploadTaskId) {
                    this.showToast('error', '任务创建失败');
                    return;
                }
                this.uploadTaskInfo = {
                    total: files.length,
                    processed: 0,
                    success: 0,
                    failed: [],
                    duplicates: [],
                    status: 'running'
                };
                this.uploadTaskProgress = 0;
                this.uploadTaskStatus = 'running';
                this.uploadCurrentFile = '准备中...';
                this.uploadShowDetails = false;
                this.uploadStep = 2;
                this.beginUploadPolling();
            } catch (error) {
                console.error('启动批量索引失败', error);
                this.showToast('error', error.response?.data?.error || '启动批量索引失败');
            }
        },
        beginUploadPolling() {
            this.clearUploadPolling();
            this.fetchUploadStatus();
            this.uploadPollingTimer = setInterval(() => {
                this.fetchUploadStatus();
            }, 1200);
        },
        clearUploadPolling() {
            if (this.uploadPollingTimer) {
                clearInterval(this.uploadPollingTimer);
                this.uploadPollingTimer = null;
            }
        },
        async fetchUploadStatus() {
            if (!this.uploadTaskId) return;
            try {
                const response = await axios.get(`/api/batch_index/${this.uploadTaskId}/status`);
                const data = response.data || {};
                this.uploadTaskInfo = {
                    total: data.total || 0,
                    processed: data.processed || 0,
                    success: data.success || 0,
                    failed: data.failed || [],
                    duplicates: data.duplicates || [],
                    status: data.status || 'running',
                    remain_time: data.remain_time || 0
                };
                this.uploadTaskProgress = Math.round((data.progress || 0) * 100);
                this.uploadTaskStatus = data.status || 'running';
                this.uploadCurrentFile = data.current_file || '处理中...';

                if (data.pending_duplicate) {
                    this.uploadDuplicateDialog.payload = data.pending_duplicate;
                    this.uploadDuplicateDialog.visible = true;
                    this.uploadDuplicateDialog.loading = false;
                } else if (this.uploadDuplicateDialog.visible) {
                    this.uploadDuplicateDialog.visible = false;
                    this.uploadDuplicateDialog.payload = null;
                    this.uploadDuplicateDialog.remember = false;
                    this.uploadDuplicateDialog.loading = false;
                }

                if (['completed', 'failed', 'cancelled'].includes(this.uploadTaskStatus)) {
                    this.clearUploadPolling();
                    this.uploadStep = 3;
                    this.uploadShowDetails = true;
                    await this.loadStatus();
                    await this.loadProjects();
                }
            } catch (error) {
                console.error('查询索引进度失败', error);
                this.showToast('error', '查询索引进度失败');
                this.clearUploadPolling();
            }
        },
        async cancelUploadTask() {
            if (!this.uploadTaskId || this.uploadCancelling) return;
            try {
                this.uploadCancelling = true;
                await axios.delete(`/api/batch_index/${this.uploadTaskId}`);
                this.showToast('info', '索引任务已取消');
                this.clearUploadPolling();
                this.uploadTaskStatus = 'cancelled';
                if (this.uploadTaskInfo) {
                    this.uploadTaskInfo.status = 'cancelled';
                }
                this.uploadStep = 3;
                await this.loadStatus();
                await this.loadProjects();
            } catch (error) {
                console.error('取消索引失败', error);
                this.showToast('error', error.response?.data?.error || '取消索引失败');
            } finally {
                this.uploadCancelling = false;
            }
        },
        async submitUploadDuplicateDecision(action) {
            if (!this.uploadTaskId || !action || this.uploadDuplicateDialog.loading) {
                return;
            }
            this.uploadDuplicateDialog.loading = true;
            try {
                await axios.post(`/api/batch_index/${this.uploadTaskId}/decision`, {
                    action,
                    apply_to_all: this.uploadDuplicateDialog.remember
                });
                const message = action === 'skip' ? '已跳过当前文件' : '已覆盖当前文件';
                this.showToast('success', message);
                this.uploadDuplicateDialog.visible = false;
                this.uploadDuplicateDialog.payload = null;
                this.uploadDuplicateDialog.remember = false;
                await this.fetchUploadStatus();
            } catch (error) {
                console.error('提交决策失败', error);
                this.showToast('error', error.response?.data?.error || '提交决策失败');
            } finally {
                this.uploadDuplicateDialog.loading = false;
            }
        },
        closeUploadDuplicateDialog() {
            if (this.uploadTaskStatus === 'running' && this.uploadDuplicateDialog.payload) {
                this.showToast('info', '请先选择“跳过”或“覆盖”以继续任务');
                return;
            }
            this.uploadDuplicateDialog.visible = false;
            this.uploadDuplicateDialog.payload = null;
            this.uploadDuplicateDialog.remember = false;
            this.uploadDuplicateDialog.loading = false;
        },
        uploadThumbnail(file) {
            if (!file) return '';
            if (file.thumbnailUrl) return file.thumbnailUrl;
            if (file.thumbnail) return file.thumbnail;
            if (file.path) {
                return `/api/thumbnail?path=${encodeURIComponent(file.path)}&size=96`;
            }
            return '';
        },
        uploadFileTypeLabel(file) {
            if (file?.type === 'video') return '视频';
            return '图片';
        },
        uploadStatusBadge(file) {
            return file?.is_indexed ? '已索引' : '待入库';
        },
        formatHistoryTime(timestamp) {
            if (!timestamp) return '';
            const date = new Date(timestamp);
            if (Number.isNaN(date.getTime())) return '';
            const mm = `${date.getMonth() + 1}`.padStart(2, '0');
            const dd = `${date.getDate()}`.padStart(2, '0');
            const hh = `${date.getHours()}`.padStart(2, '0');
            const mi = `${date.getMinutes()}`.padStart(2, '0');
            return `${mm}-${dd} ${hh}:${mi}`;
        },
        finishUploadWizard() {
            this.resetUploadWizard();
            this.refreshUploadHistory();
        }
    }
});

WorkspaceApp.mount('#app');
