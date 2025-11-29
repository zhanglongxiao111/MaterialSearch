
const app = Vue.createApp({
    data() {
        const includeDupPref = localStorage.getItem('classic-include-duplicates') === 'true';
        return {
            currentTab: "0",
            isScanning: false,
            status: {
                total_images: 0,
                total_pexels_videos: 0,
                total_video_frames: 0,
                total_videos: 0,
            },
            enableLogin: null,
            form: {
                positive: '',
                negative: '',
                top_n: '6',
                search_type: 0,
                positive_threshold: 20,
                negative_threshold: 30,
                image_threshold: 75,
                img_id: -1,
                path: '',
                start_time: 0,
                end_time: 0,
                library_type: 'permanent',
                project_id: null,
                include_duplicates: includeDupPref
            },
            time_filter: null,
            files: [],
            image_url_list: [],
            pexels_videos: [],
            timer: null,
            imageSearchUrl: null,
            activeCollapse: [],
            currentLibrary: localStorage.getItem('currentLibrary') || 'permanent',
            projects: [],
            createProjectDialogVisible: false,
            creatingProject: false,
            newProject: {
                name: '',
                client_name: '',
                description: ''
            },
            projectRules: {
                name: [{required: true, message: '请输入项目名称', trigger: 'blur'}]
            },
            showProjectManager: false,
            loadingProjects: false,
            searchScope: 'permanent',
            scanDialogVisible: false,
            scanTarget: 'permanent',
            scanPaths: [],
            newScanPath: '',
            // 添加素材对话框相关
            showAddMaterialDialog: false,
            addMaterialStep: 0,
            materialPathInput: '',
            previewFiles: [],
            selectedFiles: [],
            loadingPreview: false,
            fileFilter: 'all',
            indexTaskId: null,
            indexTaskInfo: {},
            indexProgress: 0,
            indexStatus: '',
            currentIndexingFile: '',
            indexingInterval: null,
            cancelling: false,
            showIndexDetails: false,
            activeCollapseNames: [],
            historyPaths: [],
            historyStoreKey: 'materialPathHistory',
            thumbnailQueue: [],
            thumbnailTimer: null,
            thumbnailScrollHandler: null,
            duplicateDialogVisible: false,
            pendingDuplicate: null,
            duplicateDecisionLoading: false,
            duplicateRememberChoice: false,
            // Workspace 相关状态
            isWorkspace: document.body.classList.contains('workspace'),
            sidebarLibrary: localStorage.getItem('currentLibrary')?.startsWith('proj_') ? 'project' : 'permanent',
            permanentGroups: [
                { id: 'all', name: '全部素材', count: '12,430', description: '官方永久库全集', path: '' },
                { id: 'cg', name: '效果图', count: '3,210', description: '渲染/空间/产品展示', path: '/cg' },
                { id: 'ai', name: 'AI 生成', count: '1,520', description: 'Midjourney / SD', path: '/ai' },
                { id: 'ref', name: '参考素材', count: '4,380', description: '实拍参考/灵感', path: '/ref' }
            ],
            activePermanentGroup: 'all',
            workspaceActiveTab: 'search',
            workspaceAdvancedOpen: false,
            workspaceViewMode: 'masonry',
            workspaceThumbnailScale: 100,
            workspaceSearchModes: [
                { value: 0, label: '文本', icon: 'type' },
                { value: 1, label: '图片', icon: 'image' },
                { value: 2, label: '视频', icon: 'film' },
                { value: 3, label: '混合', icon: 'sparkles' }
            ],
            workspaceSearchMode: 0,
            themeMode: localStorage.getItem('workspace-theme') || 'auto',
            includeDuplicatesPreference: includeDupPref,
            dedupLatestReport: null,
            dedupLoading: false
        }
    },
    computed: {
        scopeHeadline() {
            if (!this.isWorkspace) return '';
            if (this.currentLibrary === 'permanent') {
                return `永久库 · ${this.activeGroupName}`;
            }
            const project = this.projects.find(p => p.id === this.currentLibrary);
            return project ? `项目库 · ${project.name}` : '项目库';
        },
        scopeDescription() {
            if (!this.isWorkspace) return '';
            if (this.currentLibrary === 'permanent') {
                return `永久库 · ${this.activeGroupName}`;
            }
            const project = this.projects.find(p => p.id === this.currentLibrary);
            return project ? `项目库 · ${project.name}` : '项目库';
        },
        dedupLatestReportText() {
            if (!this.dedupLatestReport) return '尚未执行去重';
            const ts = this.dedupLatestReport.completed_at || this.dedupLatestReport.created_at;
            if (!ts) return '已完成';
            const d = new Date(ts);
            if (Number.isNaN(d.getTime())) return `上次 ${ts}`;
            return `上次 ${d.toLocaleString()}`;
        },
        scopeClass() {
            if (!this.isWorkspace) return '';
            return this.currentLibrary === 'permanent' ? 'text-emerald-600' : 'text-sky-600';
        },
        themeLabel() {
            if (!this.isWorkspace) return '';
            if (this.themeMode === 'auto') return '系统模式自动';
            if (this.themeMode === 'light') return '浅色模式';
            return '深色模式';
        },
        activeGroupName() {
            const group = this.permanentGroups.find(g => g.id === this.activePermanentGroup);
            return group ? group.name : '全部素材';
        },
        resultsWrapperClass() {
            return {
                'results-masonry': this.workspaceViewMode === 'masonry',
                'grid-view': this.workspaceViewMode === 'grid'
            };
        },
        resultsWrapperStyle() {
            if (this.workspaceViewMode === 'grid') {
                const cols = Math.max(2, Math.floor(this.workspaceThumbnailScale / 40));
                return { display: 'grid', gridTemplateColumns: `repeat(${cols}, minmax(220px, 1fr))`, gap: '16px' };
            }
            const count = Math.max(2, Math.floor(this.workspaceThumbnailScale / 35));
            return { columnCount: count };
        },
        selectedFilesCount() {
            return this.selectedFiles.length;
        },
        selectedFilesSize() {
            return this.selectedFiles.reduce((sum, file) => sum + file.size, 0);
        },
        filteredFiles() {
            if (this.fileFilter === 'all') {
                return this.previewFiles;
            } else if (this.fileFilter === 'image') {
                return this.previewFiles.filter(f => f.type === 'image');
            } else if (this.fileFilter === 'video') {
                return this.previewFiles.filter(f => f.type === 'video');
            }
            return this.previewFiles;
        }
    },
    watch: {
        'currentTab'(val) { localStorage.setItem('currentTab', val); },
        'form.top_n'(val) { localStorage.setItem('form.top_n', val); },
        'form.positive_threshold'(val) { localStorage.setItem('form.positive_threshold', val); },
        'form.negative_threshold'(val) { localStorage.setItem('form.negative_threshold', val); },
        'form.image_threshold'(val) { localStorage.setItem('form.image_threshold', val); },
        'currentLibrary'(val) {
            localStorage.setItem('currentLibrary', val);
            this.refreshRecentPaths();
        this.sidebarLibrary = this.currentLibrary === 'permanent' ? 'permanent' : 'project';
        this.form.include_duplicates = this.currentLibrary === 'permanent' ? this.includeDuplicatesPreference : true;
        if (this.isWorkspace) {
            this.applyTheme();
            this.workspaceSearchMode = this.form.search_type || 0;
        }
        this.loadDedupSummary();
            this.sidebarLibrary = val === 'permanent' ? 'permanent' : 'project';
            this.form.include_duplicates = val === 'permanent' ? this.includeDuplicatesPreference : true;
            if (this.isWorkspace && val === 'permanent') {
                this.activePermanentGroup = 'all';
            }
        includeDuplicatesPreference(val) {
            localStorage.setItem('classic-include-duplicates', val ? 'true' : 'false');
            if (this.form.library_type === 'permanent') {
                this.form.include_duplicates = val;
            }
        },
        searchScope(val) {
            this.form.include_duplicates = val === 'permanent' ? this.includeDuplicatesPreference : true;
        },
        },
    },
    mounted: function() {
        fetchServerTimeAndSetOffset();  // 页面加载时获取服务器时间
        this.loadData();
        this.loadProjects();
        this.timer = setInterval(this.loadData, 5000);
        // 加载保存的表单设置
        this.currentTab = localStorage.getItem('currentTab') || '0';
        this.currentLibrary = localStorage.getItem('currentLibrary') || 'permanent';
        this.refreshRecentPaths();
        this.sidebarLibrary = this.currentLibrary === 'permanent' ? 'permanent' : 'project';
        if (this.isWorkspace) {
            this.applyTheme();
            this.workspaceSearchMode = this.form.search_type || 0;
        }
        const keys = ['form.top_n', 'form.positive_threshold',  'form.negative_threshold', 'form.image_threshold'];
        keys.forEach(k => {
            const val = localStorage.getItem(k);
            if (val !== null) {
                const field = k.split('.')[1];
                this.form[field] = field.includes('threshold') ? Number(val) : val;
            }
        });
        // 添加全局粘贴事件监听，实现 Ctrl+V 粘贴图片
        window.addEventListener('paste', async (event) => {
            console.log(event)
            if (!["1", "3"].includes(this.currentTab)) return; // 6不做自动粘贴，因为会覆盖文本框粘贴功能
            await this.pasteImg();
        });
    },
    created() {
        var that = this
        let clipboard = new ClipboardJS(".copy");
        clipboard.on("success", function(e) {
            ElementPlus.ElMessage.success(that.$t('messages.clipboardCopySuccess'));
            e.clearSelection();
        })
    },
    methods: {
        changeLocale(locale) {
            this.$i18n.locale = locale
        },
        cleanCache() {
            var that = this;
            axios.get('api/clean_cache')
                .then(function(response) {
                    ElementPlus.ElMessage.info(response.data);
                })
                .catch(function(error) {
                    console.log(error);
                    ElementPlus.ElMessage.error(error.response.data);
                })
        },
        downloadVideoClip(url, start_time, end_time) {
            var parts = url.split('/');
            var lastPart = parts[parts.length - 1];
            var hashPart = lastPart.split('#')[0];
            window.open(`/api/download_video_clip/${hashPart}/${start_time}/${end_time}`, "_blank");
        },
        loadHistoryStore() {
            try {
                return JSON.parse(localStorage.getItem(this.historyStoreKey) || '[]');
            } catch (e) {
                console.warn('无法解析历史路径', e);
                return [];
            }
        },
        saveHistoryStore(store) {
            localStorage.setItem(this.historyStoreKey, JSON.stringify(store));
        },
        refreshRecentPaths() {
            const store = this.loadHistoryStore();
            const entry = store.find(item => item.project === this.currentLibrary);
            const paths = entry ? entry.paths : [];
            this.historyPaths = paths.map(item => ({
                path: item.path,
                updatedAt: item.updatedAt,
                timeLabel: this.formatHistoryTime(item.updatedAt)
            }));
        },
        persistRecentPaths(paths) {
            if (!paths || paths.length === 0) return;
            const store = this.loadHistoryStore();
            const project = this.currentLibrary;
            let entry = store.find(item => item.project === project);
            if (!entry) {
                entry = { project, paths: [] };
                store.push(entry);
            }
            const now = Date.now();
            paths.forEach(p => {
                const normalized = p.trim();
                if (!normalized) return;
                entry.paths = entry.paths.filter(item => item.path !== normalized);
                entry.paths.unshift({ path: normalized, updatedAt: now });
            });
            entry.paths = entry.paths.slice(0, 10);
            this.saveHistoryStore(store);
            this.refreshRecentPaths();
        this.sidebarLibrary = this.currentLibrary === 'permanent' ? 'permanent' : 'project';
        if (this.isWorkspace) {
            this.applyTheme();
            this.workspaceSearchMode = this.form.search_type || 0;
        }
        },
        applyHistoryPath(path) {
            if (!path) return;
            var lines = this.materialPathInput ? this.materialPathInput.split('\n').map(line => line.trim()).filter(Boolean) : [];
            if (!lines.includes(path)) {
                lines.push(path);
            }
            this.materialPathInput = lines.join('\n');
        },
        formatHistoryTime(timestamp) {
            if (!timestamp) return '';
            var date = new Date(timestamp);
            var mm = (date.getMonth() + 1).toString().padStart(2, '0');
            var dd = date.getDate().toString().padStart(2, '0');
            var hh = date.getHours().toString().padStart(2, '0');
            var mi = date.getMinutes().toString().padStart(2, '0');
            return `${mm}-${dd} ${hh}:${mi}`;
        },
        loadData() {
            var that = this;
            axios.get('api/status')
                .then(function(response) {
                    console.log(response);
                    that.status = response["data"];
                    that.status.remain_time = formatTime(that.status.remain_time);
                    that.isScanning = response["data"]["status"];
                    that.enableLogin = response["data"]["enable_login"];
                })
                .catch(function(error) {
                    console.log(error);
                    ElementPlus.ElMessage.error(error);
                })
        },
        scan() {
            var that = this;

            // 如果是项目库，显示路径输入对话框
            if (that.currentLibrary !== 'permanent') {
                that.scanDialogVisible = true;
                that.scanTarget = that.currentLibrary;
                return;
            }

            // 永久库保持简单确认
            ElementPlus.ElMessageBox.confirm('请选择扫描目标', '扫描确认', {
                confirmButtonText: '扫描到永久库',
                cancelButtonText: '取消',
                type: 'info',
                showCancelButton: true
            }).then(() => {
                axios.get('api/scan?target=permanent')
                    .then(function(response) {
                        console.log(response);
                        that.loadData();
                        ElementPlus.ElMessage.success('已开始扫描到永久库');
                    })
                    .catch(function(error) {
                        console.log(error);
                        ElementPlus.ElMessage.error(error.response.data);
                    });
            });
        },
        startScanFromDialog() {
            var that = this;

            if (that.scanPaths.length === 0) {
                ElementPlus.ElMessage.warning('请至少添加一个扫描路径');
                return;
            }

            // 构建请求URL
            var url = `api/scan?target=${that.scanTarget}`;
            that.scanPaths.forEach(function(path) {
                url += `&path=${encodeURIComponent(path)}`;
            });

            axios.get(url)
                .then(function(response) {
                    console.log(response);
                    that.loadData();
                    that.scanDialogVisible = false;
                    ElementPlus.ElMessage.success(response.data.message);
                })
                .catch(function(error) {
                    console.log(error);
                    ElementPlus.ElMessage.error(error.response.data);
                });
        },
        search(search_type) {
            var that = this;
            var loadingInstance;
            if (search_type === 4) {
                loadingInstance = ElementPlus.ElLoading.service({ fullscreen: true, text: that.$t('messages.matching') });
            } else {
                loadingInstance = ElementPlus.ElLoading.service({ fullscreen: true, text: that.$t('messages.searching') });
            }
            this.upload.clearFiles();
            that.form.search_type = search_type;
            if ((search_type === 4 || search_type == 9) && that.form.positive == "") {
                ElementPlus.ElMessage.error(that.$t('messages.textContentEmpty'));
                loadingInstance.close();
                return;
            }
            if (that.time_filter) {
                that.form.start_time = Math.floor(that.time_filter[0] / 1000);
                that.form.end_time = Math.floor(that.time_filter[1] / 1000);
            } else {
                that.form.start_time = null;
                that.form.end_time = null;
            }

            const libraryType = that.searchScope;
            const projectId = (that.searchScope === 'project') ? that.currentLibrary : null;
            that.form.library_type = libraryType;
            that.form.project_id = projectId;
            that.form.include_duplicates = libraryType === 'permanent' ? that.includeDuplicatesPreference : true;

            const requestedTopN = parseInt(that.form.top_n, 10);
            const blankQuery = (search_type === 0 || search_type === 2) &&
                !(that.form.start_time || that.form.end_time) &&
                !(that.form.path && that.form.path.trim()) &&
                !(that.form.positive && that.form.positive.trim()) &&
                !(that.form.negative && that.form.negative.trim());
            if (libraryType === 'permanent' && blankQuery) {
                ElementPlus.ElMessage.warning('永久库数据量较大，请输入关键词或路径后再搜索');
                loadingInstance.close();
                return;
            }
            const payload = {
                ...that.form,
                positive: (that.form.positive || '').trim(),
                negative: (that.form.negative || '').trim(),
                library_type: libraryType,
                project_id: projectId,
                include_duplicates: libraryType === 'permanent' ? that.includeDuplicatesPreference : true,
                top_n: Number.isFinite(requestedTopN) ? requestedTopN : 6
            };
            if (blankQuery) {
                payload.top_n = 0; // 0 表示请求全部素材
            }

            axios.post('/api/match', payload)
                .then(function(response) {
                    console.log(response);
                    loadingInstance.close();
                    if (search_type === 0 || search_type === 1 || search_type === 5) {
                        that.files = response["data"];
                        that.image_url_list = [];
                        that.files.forEach(function(element) {
                            that.image_url_list.push(element.url);
                        });
                        ElementPlus.ElMessage.info(that.$t('messages.totalSearchResult') + that.files.length + that.$t('messages.photos'));
                        return;
                    }
                    if (search_type === 2 || search_type === 3 || search_type === 6) {
                        that.files = response["data"];
                        ElementPlus.ElMessage.info(that.$t('messages.totalSearchResult') + that.files.length + that.$t('messages.videos'));
                        return;
                    }
                    if (search_type === 9) {
                        that.pexels_videos = response["data"];
                        return;
                    }
                    if (search_type === 4) {
                        ElementPlus.ElMessage.info(that.$t('messages.matchingSimilarityInfo') + response["data"]["score"] + "%");
                        return;
                    }
                })
                .catch(function(error) {
                    console.log(error);
                    loadingInstance.close();
                    ElementPlus.ElMessage.error(error.response.data);
                })
        },
        searchFromImage(search_type, img_url) {
            console.log(this.currentTab);
            if (search_type === 5) {
                this.currentTab = "1";
            } else if (search_type === 6) {
                this.currentTab = "3";
            }
            this.form.search_type = search_type;
            this.form.positive = '';
            this.form.negative = '';
            var id_str = img_url.match(/(\d+)$/);
            if (id_str) {
                var id_num = parseInt(id_str[1], 10);
                this.form.img_id = id_num;
                this.search(search_type);
            } else {
                ElementPlus.ElMessage.error(that.$t('messages.imgIdNotFound'));
            }
        },
        handleBeforeUpload(file) {
            console.log(file);
            return new Promise((resolve) => {
                const reader = new FileReader();
                reader.onload = (e) => {
                    this.imageSearchUrl = e.target.result;
                    resolve(true);
                };
                reader.readAsDataURL(file);
            });
        },
        async pasteImg() {
            // 检查浏览器是否支持剪切板 API 和 Image 对象
            if (navigator.clipboard && window.Image) {
                try {
                    // 读取剪切板中的内容，返回一个 Promise，解析为一个 ClipboardItem 数组
                    const clipboardItems = await navigator.clipboard.read();
                    // 检查剪切板中是否有内容，并且第一个项目是否包含图片类型（PNG 或 JPEG）
                    if (clipboardItems.length > 0 && (clipboardItems[0].types.includes('image/png') || clipboardItems[0].types.includes('image/jpeg'))) {
                        // 获取剪切板中的第一个图片项目
                        const [imageItem] = clipboardItems;
                        // 获取图片的 Blob 数据
                        const blob = await imageItem.getType('image/png');
                        // 将 Blob 对象转换为 File 对象
                        const file = this.blobToFile(blob, 'pasteboard.png');
                        // 清空当前文件列表
                        this.upload.clearFiles();
                        // 开始处理文件
                        this.upload.handleStart(file);
                        // 提交文件上传请求
                        this.upload.submit();
                    } else {
                        ElementPlus.ElMessage.error(this.$t('剪切板没有图片'));
                    }
                } catch (error) {
                    // 捕获并处理可能的错误
                    console.error('读取剪切板失败:', error);
                    ElementPlus.ElMessage.error(this.$t('messages.clipboardReadFailed'));
                }
            } else {
                ElementPlus.ElMessage.error(this.$t('messages.clipboardNotSupported'));
            }
        },
        blobToFile(blob, fileName) {
            return new File([blob], fileName, { type: blob.type });
        },
        copyAllPaths() {
            if (!this.files || this.files.length === 0) {
                ElementPlus.ElMessage.warning(this.$t('messages.noFilesToCopy'));
                return;
            }
            const allPaths = this.files.map(f => f.path).join('\n');
            if (window.Clipboard && window.Clipboard.copy) {
                window.Clipboard.copy(allPaths);
            } else if (navigator.clipboard) {
                navigator.clipboard.writeText(allPaths).then(() => {
                    ElementPlus.ElMessage.success(this.$t('messages.clipboardCopySuccess'));
                }, () => {
                    ElementPlus.ElMessage.error(this.$t('messages.clipboardReadFailed'));
                });
            } else {
                // fallback
                const textarea = document.createElement('textarea');
                textarea.value = allPaths;
                document.body.appendChild(textarea);
                textarea.select();
                try {
                    document.execCommand('copy');
                    ElementPlus.ElMessage.success(this.$t('messages.clipboardCopySuccess'));
                } catch (err) {
                    ElementPlus.ElMessage.error(this.$t('messages.clipboardReadFailed'));
                }
                document.body.removeChild(textarea);
            }
        },
        async loadDedupSummary() {
            try {
                const { data } = await axios.get('/api/dedup/jobs/latest');
                if (data?.success) {
                    this.dedupLatestReport = data.data;
                }
            } catch (error) {
                console.error('加载去重报告失败', error);
            }
        },
        async startDedupJobClassic() {
            if (this.dedupLoading) return;
            if (!window.confirm('将对永久库执行去重扫描，耗时取决于素材数量，确认继续吗？')) {
                return;
            }
            this.dedupLoading = true;
            try {
                const { data } = await axios.post('/api/dedup/jobs', { library_type: 'permanent' });
                if (data?.success) {
                    ElementPlus.ElMessage.success('去重任务已启动');
                    this.loadDedupSummary();
                } else {
                    throw new Error(data?.error || '启动失败');
                }
            } catch (error) {
                const message = error?.response?.data?.error || error.message || '去重任务启动失败';
                ElementPlus.ElMessage.error(message);
            } finally {
                this.dedupLoading = false;
            }
        },
        handleLibraryChange(value) {
            if (value === '__new__') {
                this.createProjectDialogVisible = true;
                this.$nextTick(() => {
                    this.currentLibrary = this.currentLibrary || 'permanent';
                });
            } else {
                this.currentLibrary = value;
                // 自动更新搜索范围：永久库时为permanent，项目库时为project
                if (this.currentLibrary === 'permanent') {
                    this.searchScope = 'permanent';
                } else {
                    this.searchScope = 'project';
                }
                this.form.include_duplicates = this.searchScope === 'permanent' ? this.includeDuplicatesPreference : true;
                ElementPlus.ElMessage.success(`已切换到 ${value === 'permanent' ? '永久素材库' : '项目'}`);
            }
        },
        async loadProjects() {
            var that = this;
            try {
                const response = await axios.get('/api/projects');
                that.projects = response.data.data || [];
            } catch (error) {
                console.error('加载项目列表失败:', error);
                ElementPlus.ElMessage.error('加载项目列表失败');
            }
        },
        async createProject() {
            var that = this;
            await that.$refs.projectForm.validate(async(valid) => {
                if (valid) {
                    that.creatingProject = true;
                    try {
                        const response = await axios.post('/api/projects', {
                            name: that.newProject.name,
                            client_name: that.newProject.client_name,
                            description: that.newProject.description,
                            status: 'active'
                        });
                        ElementPlus.ElMessage.success('项目创建成功');
                        that.createProjectDialogVisible = false;
                        that.newProject = {name: '', client_name: '', description: ''};
                        await that.loadProjects();
                        that.currentLibrary = response.data.id;
                    } catch (error) {
                        console.error('创建项目失败:', error);
                        ElementPlus.ElMessage.error(error.response?.data?.error || '创建项目失败');
                    } finally {
                        that.creatingProject = false;
                    }
                }
            });
        },
        switchToProject(projectId) {
            this.currentLibrary = projectId;
            this.showProjectManager = false;
            ElementPlus.ElMessage.success('已切换到项目');
        },
        async deleteProject(projectId) {
            var that = this;
            try {
                await axios.delete(`/api/projects/${projectId}`);
                ElementPlus.ElMessage.success('项目已删除');
                await that.loadProjects();
                if (that.currentLibrary === projectId) {
                    that.currentLibrary = 'permanent';
                    if (that.searchScope === 'project') {
                        that.searchScope = 'permanent';
                    }
                }
            } catch (error) {
                console.error('删除项目失败:', error);
                ElementPlus.ElMessage.error(error.response?.data?.error || '删除项目失败');
            }
        },
        addScanPath() {
            var that = this;
            var path = that.newScanPath.trim();
            if (!path) {
                ElementPlus.ElMessage.warning('请输入有效路径');
                return;
            }
            if (that.scanPaths.includes(path)) {
                ElementPlus.ElMessage.warning('路径已存在');
                return;
            }
            that.scanPaths.push(path);
            that.newScanPath = '';
            ElementPlus.ElMessage.success('路径已添加');
        },
        removeScanPath(index) {
            this.scanPaths.splice(index, 1);
            ElementPlus.ElMessage.info('路径已删除');
        },
        clearScanPaths() {
            this.scanPaths = [];
            ElementPlus.ElMessage.info('已清空所有路径');
        },
        // ========== 添加素材对话框方法 ==========
        handlePathPaste(event) {
            // 粘贴事件处理 - 自动解析路径
            setTimeout(() => {
                var input = this.materialPathInput;
                // 去除引号并按行分割
                var lines = input.split('\n').map(line => line.trim().replace(/^["']|["']$/g, '')).filter(line => line);
                this.materialPathInput = lines.join('\n');
            }, 10);
        },
                async handlePreviewFiles() {
            var that = this;
            var input = that.materialPathInput.trim();
            if (!input) {
                ElementPlus.ElMessage.warning('请输入文件或文件夹路径');
                return;
            }

            that.loadingPreview = true;
            var paths = input.split('\n').map(line => line.trim()).filter(line => line);
            that.detachThumbnailHelpers();

            try {
                const response = await axios.post('/api/preview_files', {
                    paths: paths,
                    target: that.currentLibrary
                });
                that.persistRecentPaths(paths);
                that.previewFiles = (response.data || []).map(item => ({
                    ...item,
                    thumbnailUrl: item.thumbnailUrl || null
                }));
                that.selectedFiles = that.previewFiles.filter(f => !f.is_indexed);
                that.fileFilter = 'all';
                that.addMaterialStep = 1;
                ElementPlus.ElMessage.success(`已扫描到 ${response.data.length} 个文件`);

                that.$nextTick(() => {
                    that.$refs.fileTable?.clearSelection();
                    that.previewFiles.forEach(row => {
                        that.$refs.fileTable?.toggleRowSelection(row, !row.is_indexed);
                    });
                    that.initThumbnailLoader();
                });
            } catch (error) {
                console.error('预览文件失败:', error);
                ElementPlus.ElMessage.error(error.response?.data?.error || '预览文件失败');
            } finally {
                that.loadingPreview = false;
            }
        },        selectAllFiles() {
            this.$refs.fileTable?.clearSelection();
            this.filteredFiles.forEach(row => {
                this.$refs.fileTable?.toggleRowSelection(row, true);
            });
        },
        invertSelection() {
            var currentSelected = new Set(this.selectedFiles.map(f => f.path));
            this.filteredFiles.forEach(row => {
                var shouldSelect = !currentSelected.has(row.path);
                this.$refs.fileTable?.toggleRowSelection(row, shouldSelect);
            });
        },        filterImageOnly() {
            this.fileFilter = 'image';
        },
        filterVideoOnly() {
            this.fileFilter = 'video';
        },
        showAllFiles() {
            this.fileFilter = 'all';
        },
        handleSelectionChange(selection) {
            this.selectedFiles = selection;
        },
        async startBatchIndex() {
            var that = this;
            if (that.selectedFiles.length === 0) {
                ElementPlus.ElMessage.warning('请选择要索引的文件');
                return;
            }

            try {
                that.duplicateDialogVisible = false;
                that.pendingDuplicate = null;
                that.duplicateRememberChoice = false;
                const response = await axios.post('/api/batch_index', {
                    files: that.selectedFiles,
                    target: that.currentLibrary,
                    duplicate_strategy: 'ask'
                });

                that.indexTaskId = response.data.task_id;
                that.addMaterialStep = 2;
                that.indexProgress = 0;
                that.indexStatus = 'running';
                that.currentIndexingFile = '准备中...';

                // 开始轮询进度
                that.pollIndexProgress();
            } catch (error) {
                console.error('启动批量索引失败:', error);
                ElementPlus.ElMessage.error(error.response?.data?.error || '启动批量索引失败');
            }
        },
        async pollIndexProgress() {
            var that = this;
            if (!that.indexTaskId) return;

            that.indexingInterval = setInterval(async () => {
                try {
                    const response = await axios.get(`/api/batch_index/${that.indexTaskId}/status`);
                    that.indexTaskInfo = response.data;
                    that.indexProgress = Math.round(((response.data.progress || 0) * 100));
                    that.currentIndexingFile = response.data.current_file || '处理中...';
                    that.indexStatus = response.data.status;

                    if (response.data.status === 'waiting_duplicate' && response.data.pending_duplicate) {
                        that.pendingDuplicate = response.data.pending_duplicate;
                        that.duplicateDialogVisible = true;
                        that.duplicateDecisionLoading = false;
                    } else if (that.duplicateDialogVisible && response.data.status !== 'waiting_duplicate') {
                        that.duplicateDialogVisible = false;
                        that.pendingDuplicate = null;
                        that.duplicateRememberChoice = false;
                    }

                    if (['completed', 'failed', 'cancelled'].includes(response.data.status)) {
                        clearInterval(that.indexingInterval);
                        that.indexingInterval = null;
                        that.addMaterialStep = 3;

                        await that.loadProjects();
                        await that.loadData();
                    }
                } catch (error) {
                    console.error('查询索引进度失败:', error);
                    clearInterval(that.indexingInterval);
                    that.indexingInterval = null;
                    ElementPlus.ElMessage.error('查询索引进度失败');
                }
            }, 500);
        },
        async cancelBatchIndex() {
            var that = this;
            if (!that.indexTaskId) return;

            try {
                that.cancelling = true;
                await axios.delete(`/api/batch_index/${that.indexTaskId}`);
                ElementPlus.ElMessage.info('索引任务已取消');
                that.duplicateDialogVisible = false;
                that.pendingDuplicate = null;
                that.duplicateRememberChoice = false;

                if (that.indexingInterval) {
                    clearInterval(that.indexingInterval);
                    that.indexingInterval = null;
                }

                that.addMaterialStep = 3;
                that.indexStatus = 'cancelled';
            } catch (error) {
                console.error('取消索引失败:', error);
                ElementPlus.ElMessage.error(error.response?.data?.error || '取消索引失败');
            } finally {
                that.cancelling = false;
            }
        },
        async submitDuplicateDecision(action) {
            if (!this.indexTaskId || !action) return;
            this.duplicateDecisionLoading = true;
            try {
                await axios.post(`/api/batch_index/${this.indexTaskId}/decision`, {
                    action: action,
                    apply_to_all: this.duplicateRememberChoice
                });
                ElementPlus.ElMessage.success(action === 'skip' ? '已跳过当前文件' : '已覆盖当前文件');
                this.duplicateDialogVisible = false;
                this.pendingDuplicate = null;
                this.duplicateRememberChoice = false;
            } catch (error) {
                console.error('提交决策失败:', error);
                ElementPlus.ElMessage.error(error.response?.data?.error || '提交决策失败');
            } finally {
                this.duplicateDecisionLoading = false;
            }
        },        closeAddMaterialDialog() {
            var that = this;
            if (that.indexingInterval) {
                clearInterval(that.indexingInterval);
                that.indexingInterval = null;
            }
            that.detachThumbnailHelpers();

            // 重置状态
            that.showAddMaterialDialog = false;
            that.addMaterialStep = 0;
            that.materialPathInput = '';
            that.previewFiles = [];
            that.selectedFiles = [];
            that.fileFilter = 'all';
            that.indexTaskId = null;
            that.indexTaskInfo = {};
            that.indexProgress = 0;
            that.indexStatus = '';
            that.currentIndexingFile = '';
            that.cancelling = false;
            that.showIndexDetails = false;
            that.activeCollapseNames = [];
        },
        initThumbnailLoader() {
            var that = this;
            if (!that.previewFiles.length) return;
            that.detachThumbnailHelpers();
            var immediate = that.previewFiles.slice(0, 20);
            immediate.forEach(file => {
                if (!file.thumbnailUrl) {
                    that.$set(file, 'thumbnailUrl', `/api/thumbnail?path=${encodeURIComponent(file.path)}&size=128`);
                }
            });
            that.thumbnailQueue = that.previewFiles.slice(20);
            that.scheduleThumbnailLoading();
            that.$nextTick(() => {
                const body = that.$refs.fileTable?.$el?.querySelector('.el-table__body-wrapper');
                if (!body) return;
                if (!that.thumbnailScrollHandler) {
                    that.thumbnailScrollHandler = that.handleThumbnailScroll.bind(that);
                }
                body.addEventListener('scroll', that.thumbnailScrollHandler);
            });
        },
        scheduleThumbnailLoading() {
            if (!this.thumbnailQueue.length || this.thumbnailTimer) return;
            const batch = this.thumbnailQueue.splice(0, 5);
            batch.forEach(file => {
                if (!file.thumbnailUrl) {
                    this.$set(file, 'thumbnailUrl', `/api/thumbnail?path=${encodeURIComponent(file.path)}&size=128`);
                }
            });
            if (this.thumbnailQueue.length) {
                this.thumbnailTimer = setTimeout(() => {
                    this.thumbnailTimer = null;
                    this.scheduleThumbnailLoading();
                }, 400);
            }
        },
        handleThumbnailScroll() {
            const body = this.$refs.fileTable?.$el?.querySelector('.el-table__body-wrapper');
            if (!body || !this.thumbnailQueue.length) return;
            if (body.scrollTop + body.clientHeight >= body.scrollHeight - 120) {
                if (!this.thumbnailTimer) {
                    this.scheduleThumbnailLoading();
                }
            }
        },
        closeAddMaterialDialog() {
            var that = this;
            if (that.indexingInterval) {
                clearInterval(that.indexingInterval);
                that.indexingInterval = null;
            }
            that.detachThumbnailHelpers();

            that.showAddMaterialDialog = false;
            that.addMaterialStep = 0;
            that.materialPathInput = '';
            that.previewFiles = [];
            that.selectedFiles = [];
            that.fileFilter = 'all';
            that.indexTaskId = null;
            that.indexTaskInfo = {};
            that.indexProgress = 0;
            that.indexStatus = '';
            that.currentIndexingFile = '';
            that.cancelling = false;
            that.showIndexDetails = false;
            that.activeCollapseNames = [];
            that.duplicateDialogVisible = false;
            that.pendingDuplicate = null;
            that.duplicateRememberChoice = false;
        },
        detachThumbnailHelpers() {
            if (this.thumbnailTimer) {
                clearTimeout(this.thumbnailTimer);
                this.thumbnailTimer = null;
            }
            const body = this.$refs.fileTable?.$el?.querySelector('.el-table__body-wrapper');
            if (body && this.thumbnailScrollHandler) {
                body.removeEventListener('scroll', this.thumbnailScrollHandler);
            }
            this.thumbnailScrollHandler = null;
            this.thumbnailQueue = [];
        },        formatFileSize(bytes) {
            if (bytes === 0) return '0 B';
            const k = 1024;
            const sizes = ['B', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return (bytes / Math.pow(k, i)).toFixed(2) + ' ' + sizes[i];
        },
        formatDuration(seconds) {
            if (seconds < 60) return `${seconds}秒`;
            const minutes = Math.floor(seconds / 60);
            const secs = seconds % 60;
            return `${minutes}分${secs}秒`;
        }
    },
    setup() {
        const upload = Vue.ref();
        const { t } = VueI18n.useI18n({ useScope: "global" });
        function handleExceed(files, fileList) {
            upload.value.clearFiles();
            upload.value.handleStart(files[0]);
            upload.value.submit();
        }
        function handleSuccess() {
            ElementPlus.ElMessage.success(t('messages.uploadSuccess'));
        }
        return {
            upload,
            handleExceed,
            handleSuccess,
        };
    },
})





