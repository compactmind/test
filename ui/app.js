/**
 * Enhanced File Manager MCP - Dual UI Application
 * Handles all UI interactions and MCP communication
 */

class FileManagerApp {
    constructor() {
        this.currentPath = '/';
        this.selectedFiles = new Set();
        this.websocket = null;
        this.files = [];
        this.config = {};
        this.isLoading = false;
        this.searchTimeout = null;
        
        this.init();
    }
    
    async init() {
        console.log('🚀 Initializing Enhanced File Manager MCP');
        
        // Initialize WebSocket connection
        this.initWebSocket();
        
        // Load configuration
        await this.loadConfig();
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Apply theme
        this.applyTheme();
        
        // Load initial files
        await this.loadFiles();
        
        console.log('✅ File Manager MCP initialized successfully');
    }
    
    initWebSocket() {
        try {
            const wsPort = parseInt(window.location.port) + 1;
            this.websocket = new WebSocket(`ws://localhost:${wsPort}`);
            
            this.websocket.onopen = () => {
                console.log('🔌 WebSocket connected');
                this.updateStatus('Connected to server');
            };
            
            this.websocket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleWebSocketMessage(data);
                } catch (error) {
                    console.error('❌ WebSocket message error:', error);
                }
            };
            
            this.websocket.onclose = () => {
                console.log('🔌 WebSocket disconnected');
                this.updateStatus('Disconnected from server');
                
                // Try to reconnect after 3 seconds
                setTimeout(() => this.initWebSocket(), 3000);
            };
            
            this.websocket.onerror = (error) => {
                console.error('❌ WebSocket error:', error);
                this.updateStatus('Connection error');
            };
        } catch (error) {
            console.error('❌ WebSocket initialization error:', error);
            this.updateStatus('Failed to connect to server');
        }
    }
    
    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'file_changed':
                this.handleFileChanged(data.data);
                break;
            case 'operation_progress':
                this.handleOperationProgress(data.data);
                break;
            case 'notification':
                this.showNotification(data.data.message, data.data.type);
                break;
            default:
                console.log('📨 Unknown WebSocket message:', data);
        }
    }
    
    handleFileChanged(data) {
        // Refresh files if current path is affected
        if (data.path.startsWith(this.currentPath)) {
            this.loadFiles();
        }
    }
    
    handleOperationProgress(data) {
        // Update progress if needed
        console.log('📊 Operation progress:', data);
    }
    
    async loadConfig() {
        try {
            const response = await this.callMCPTool('get_config');
            if (response.success) {
                this.config = JSON.parse(response.result);
                console.log('⚙️ Config loaded:', this.config);
            }
        } catch (error) {
            console.error('❌ Failed to load config:', error);
            this.config = this.getDefaultConfig();
        }
    }
    
    getDefaultConfig() {
        return {
            theme: 'auto',
            workspace_directory: '/Users/Documents',
            debug_mode: false,
            max_file_size: 100,
            show_hidden_files: false,
            enable_checksums: false,
            backup_on_delete: true
        };
    }
    
    applyTheme() {
        const theme = this.config.theme || 'auto';
        let themeToApply = theme;
        
        if (theme === 'auto') {
            themeToApply = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
        }
        
        const themeLink = document.getElementById('theme-link');
        themeLink.href = `themes/${themeToApply}.css`;
        
        console.log(`🎨 Applied ${themeToApply} theme`);
    }
    
    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const view = e.target.dataset.view;
                this.switchView(view);
            });
        });
        
        // Search
        const searchInput = document.getElementById('search-input');
        searchInput.addEventListener('input', (e) => {
            clearTimeout(this.searchTimeout);
            this.searchTimeout = setTimeout(() => {
                this.searchFiles(e.target.value);
            }, 300);
        });
        
        // File operations
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Delete' && this.selectedFiles.size > 0) {
                this.deleteSelectedFiles();
            }
            if (e.key === 'F5' || (e.ctrlKey && e.key === 'r')) {
                e.preventDefault();
                this.refreshFiles();
            }
        });
        
        // Drag and drop
        document.addEventListener('dragover', (e) => e.preventDefault());
        document.addEventListener('drop', (e) => {
            e.preventDefault();
            this.handleFileDrop(e);
        });
        
        // Window resize
        window.addEventListener('resize', () => {
            this.adjustLayout();
        });
        
        // Theme detection
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
            if (this.config.theme === 'auto') {
                this.applyTheme();
            }
        });
    }
    
    switchView(view) {
        // Update navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-view="${view}"]`).classList.add('active');
        
        // Switch content
        switch (view) {
            case 'files':
                this.showFilesView();
                break;
            case 'search':
                this.showSearchView();
                break;
            case 'settings':
                this.showSettingsView();
                break;
        }
    }
    
    showFilesView() {
        const content = document.getElementById('content');
        content.innerHTML = `
            <div class="loading" id="loading" style="display: none;">Loading files...</div>
            <div class="file-grid" id="file-grid"></div>
        `;
        this.loadFiles();
    }
    
    showSearchView() {
        const content = document.getElementById('content');
        content.innerHTML = `
            <div class="search-section">
                <h2>Advanced Search</h2>
                <div class="search-form">
                    <input type="text" id="search-pattern" placeholder="Search pattern..." class="form-input">
                    <label>
                        <input type="checkbox" id="content-search"> Search in file contents
                    </label>
                    <label>
                        <input type="checkbox" id="case-sensitive"> Case sensitive
                    </label>
                    <button class="btn primary" onclick="app.performAdvancedSearch()">Search</button>
                </div>
                <div id="search-results"></div>
            </div>
        `;
    }
    
    showSettingsView() {
        const content = document.getElementById('content');
        content.innerHTML = `
            <div class="settings-section">
                <h2>Settings</h2>
                <div class="settings-form">
                    <div class="form-group">
                        <label class="form-label">Theme</label>
                        <select class="form-input" id="theme-select">
                            <option value="auto">Auto</option>
                            <option value="dark">Dark</option>
                            <option value="light">Light</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Workspace Directory</label>
                        <input type="text" class="form-input" id="workspace-dir" value="${this.config.workspace_directory || ''}">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Max File Size (MB)</label>
                        <input type="number" class="form-input" id="max-file-size" value="${this.config.max_file_size || 100}">
                    </div>
                    <div class="form-group">
                        <label>
                            <input type="checkbox" id="show-hidden" ${this.config.show_hidden_files ? 'checked' : ''}> Show hidden files
                        </label>
                    </div>
                    <div class="form-group">
                        <label>
                            <input type="checkbox" id="enable-checksums" ${this.config.enable_checksums ? 'checked' : ''}> Enable file checksums
                        </label>
                    </div>
                    <div class="form-group">
                        <label>
                            <input type="checkbox" id="backup-on-delete" ${this.config.backup_on_delete ? 'checked' : ''}> Backup on delete
                        </label>
                    </div>
                    <button class="btn primary" onclick="app.saveSettings()">Save Settings</button>
                </div>
            </div>
        `;
        
        // Set current theme
        document.getElementById('theme-select').value = this.config.theme || 'auto';
    }
    
    async saveSettings() {
        const settings = {
            theme: document.getElementById('theme-select').value,
            workspace_directory: document.getElementById('workspace-dir').value,
            max_file_size: parseInt(document.getElementById('max-file-size').value),
            show_hidden_files: document.getElementById('show-hidden').checked,
            enable_checksums: document.getElementById('enable-checksums').checked,
            backup_on_delete: document.getElementById('backup-on-delete').checked
        };
        
        try {
            for (const [key, value] of Object.entries(settings)) {
                await this.callMCPTool('set_config', { key, value: JSON.stringify(value) });
            }
            
            this.config = { ...this.config, ...settings };
            this.applyTheme();
            this.showNotification('Settings saved successfully', 'success');
        } catch (error) {
            console.error('❌ Failed to save settings:', error);
            this.showNotification('Failed to save settings', 'error');
        }
    }
    
    async loadFiles() {
        if (this.isLoading) return;
        
        this.isLoading = true;
        this.showLoading(true);
        
        try {
            const response = await this.callMCPTool('list_files', {
                path: this.currentPath,
                include_hidden: this.config.show_hidden_files,
                include_metadata: true
            });
            
            if (response.success) {
                const data = JSON.parse(response.result);
                this.files = data.files || [];
                this.renderFiles();
                this.updateFileCount();
                this.updateBreadcrumb();
            } else {
                throw new Error(response.error || 'Failed to load files');
            }
        } catch (error) {
            console.error('❌ Failed to load files:', error);
            this.showError('Failed to load files: ' + error.message);
        } finally {
            this.isLoading = false;
            this.showLoading(false);
        }
    }
    
    renderFiles() {
        const fileGrid = document.getElementById('file-grid');
        if (!fileGrid) return;
        
        fileGrid.innerHTML = '';
        
        if (this.files.length === 0) {
            fileGrid.innerHTML = '<div class="empty-state">No files found</div>';
            return;
        }
        
        this.files.forEach(file => {
            const fileElement = this.createFileElement(file);
            fileGrid.appendChild(fileElement);
        });
        
        fileGrid.style.display = 'grid';
    }
    
    createFileElement(file) {
        const div = document.createElement('div');
        div.className = 'file-item';
        div.dataset.path = file.path;
        div.dataset.name = file.name;
        div.dataset.type = file.type;
        
        const icon = this.getFileIcon(file);
        const size = file.size_formatted || '';
        const modified = file.modified ? new Date(file.modified).toLocaleDateString() : '';
        
        div.innerHTML = `
            <div class="file-icon ${file.type}">${icon}</div>
            <div class="file-name">${file.name}</div>
            <div class="file-meta">${size} ${modified}</div>
        `;
        
        // Event listeners
        div.addEventListener('click', (e) => {
            if (e.ctrlKey || e.metaKey) {
                this.toggleFileSelection(file);
            } else {
                this.selectFile(file);
            }
        });
        
        div.addEventListener('dblclick', () => {
            this.openFile(file);
        });
        
        div.addEventListener('contextmenu', (e) => {
            e.preventDefault();
            this.showContextMenu(e, file);
        });
        
        return div;
    }
    
    getFileIcon(file) {
        if (file.type === 'directory') {
            return '📁';
        }
        
        const extension = file.name.split('.').pop().toLowerCase();
        const iconMap = {
            // Images
            'jpg': '🖼️', 'jpeg': '🖼️', 'png': '🖼️', 'gif': '🖼️', 'svg': '🖼️',
            // Documents
            'pdf': '📄', 'doc': '📄', 'docx': '📄', 'txt': '📄', 'md': '📄',
            // Code
            'js': '💻', 'html': '💻', 'css': '💻', 'py': '💻', 'json': '💻',
            // Archives
            'zip': '📦', 'rar': '📦', 'tar': '📦', 'gz': '📦',
            // Audio/Video
            'mp3': '🎵', 'mp4': '🎬', 'avi': '🎬', 'mov': '🎬'
        };
        
        return iconMap[extension] || '📄';
    }
    
    selectFile(file) {
        this.selectedFiles.clear();
        this.selectedFiles.add(file.path);
        this.updateFileSelection();
    }
    
    toggleFileSelection(file) {
        if (this.selectedFiles.has(file.path)) {
            this.selectedFiles.delete(file.path);
        } else {
            this.selectedFiles.add(file.path);
        }
        this.updateFileSelection();
    }
    
    updateFileSelection() {
        document.querySelectorAll('.file-item').forEach(item => {
            if (this.selectedFiles.has(item.dataset.path)) {
                item.classList.add('selected');
            } else {
                item.classList.remove('selected');
            }
        });
    }
    
    async openFile(file) {
        if (file.type === 'directory') {
            this.navigateToPath(file.path);
        } else {
            // Open file for viewing/editing
            await this.viewFile(file);
        }
    }
    
    async viewFile(file) {
        try {
            const response = await this.callMCPTool('read_file', {
                path: file.path,
                max_size: this.config.max_file_size
            });
            
            if (response.success) {
                const data = JSON.parse(response.result);
                this.showFileViewer(file, data.content);
            } else {
                throw new Error(response.error || 'Failed to read file');
            }
        } catch (error) {
            console.error('❌ Failed to read file:', error);
            this.showNotification('Failed to read file: ' + error.message, 'error');
        }
    }
    
    showFileViewer(file, content) {
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.style.display = 'flex';
        modal.innerHTML = `
            <div class="modal-content" style="max-width: 80%; max-height: 80%;">
                <div class="modal-header">
                    <h3 class="modal-title">${file.name}</h3>
                    <button class="close-btn" onclick="this.closest('.modal').remove()">&times;</button>
                </div>
                <div style="flex: 1; overflow-y: auto;">
                    <pre style="white-space: pre-wrap; font-family: monospace; font-size: 14px; line-height: 1.4;">${content}</pre>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Close on background click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }
    
    navigateToPath(path) {
        this.currentPath = path;
        this.loadFiles();
    }
    
    updateBreadcrumb() {
        const breadcrumb = document.getElementById('breadcrumb');
        if (!breadcrumb) return;
        
        const parts = this.currentPath.split('/').filter(Boolean);
        breadcrumb.innerHTML = '';
        
        // Home
        const homeSpan = document.createElement('span');
        homeSpan.textContent = 'Home';
        homeSpan.dataset.path = '/';
        homeSpan.addEventListener('click', () => this.navigateToPath('/'));
        breadcrumb.appendChild(homeSpan);
        
        // Path parts
        let currentPath = '';
        parts.forEach((part, index) => {
            currentPath += '/' + part;
            
            const separator = document.createElement('span');
            separator.textContent = ' / ';
            separator.style.color = 'var(--text-tertiary)';
            breadcrumb.appendChild(separator);
            
            const span = document.createElement('span');
            span.textContent = part;
            span.dataset.path = currentPath;
            span.addEventListener('click', () => this.navigateToPath(currentPath));
            breadcrumb.appendChild(span);
        });
    }
    
    updateFileCount() {
        const fileCount = document.getElementById('file-count');
        if (fileCount) {
            fileCount.textContent = `${this.files.length} items`;
        }
    }
    
    showLoading(show) {
        const loading = document.getElementById('loading');
        const fileGrid = document.getElementById('file-grid');
        
        if (loading) {
            loading.style.display = show ? 'flex' : 'none';
        }
        if (fileGrid) {
            fileGrid.style.display = show ? 'none' : 'grid';
        }
    }
    
    showError(message) {
        const content = document.getElementById('content');
        content.innerHTML = `<div class="error">${message}</div>`;
    }
    
    updateStatus(message) {
        const statusText = document.getElementById('status-text');
        if (statusText) {
            statusText.textContent = message;
        }
    }
    
    showNotification(message, type = 'info') {
        const notification = document.getElementById('notification');
        notification.textContent = message;
        notification.className = `notification ${type}`;
        notification.classList.add('show');
        
        setTimeout(() => {
            notification.classList.remove('show');
        }, 3000);
    }
    
    async refreshFiles() {
        this.updateStatus('Refreshing...');
        await this.loadFiles();
        this.updateStatus('Ready');
        this.showNotification('Files refreshed', 'success');
    }
    
    async searchFiles(query) {
        if (!query.trim()) {
            this.loadFiles();
            return;
        }
        
        try {
            const response = await this.callMCPTool('search_files', {
                path: this.currentPath,
                pattern: query,
                content_search: false,
                case_sensitive: false
            });
            
            if (response.success) {
                const data = JSON.parse(response.result);
                this.files = data.results || [];
                this.renderFiles();
                this.updateFileCount();
            }
        } catch (error) {
            console.error('❌ Search failed:', error);
            this.showNotification('Search failed: ' + error.message, 'error');
        }
    }
    
    async performAdvancedSearch() {
        const pattern = document.getElementById('search-pattern').value;
        const contentSearch = document.getElementById('content-search').checked;
        const caseSensitive = document.getElementById('case-sensitive').checked;
        
        if (!pattern.trim()) {
            this.showNotification('Please enter a search pattern', 'warning');
            return;
        }
        
        try {
            const response = await this.callMCPTool('search_files', {
                path: this.currentPath,
                pattern,
                content_search: contentSearch,
                case_sensitive: caseSensitive
            });
            
            if (response.success) {
                const data = JSON.parse(response.result);
                const results = data.results || [];
                this.displaySearchResults(results);
            }
        } catch (error) {
            console.error('❌ Advanced search failed:', error);
            this.showNotification('Search failed: ' + error.message, 'error');
        }
    }
    
    displaySearchResults(results) {
        const resultsDiv = document.getElementById('search-results');
        if (!results.length) {
            resultsDiv.innerHTML = '<div class="empty-state">No results found</div>';
            return;
        }
        
        resultsDiv.innerHTML = results.map(result => `
            <div class="search-result" onclick="app.openSearchResult('${result.path}')">
                <div class="result-name">${result.name}</div>
                <div class="result-path">${result.path}</div>
                <div class="result-meta">
                    ${result.filename_match ? '📄 Name match' : ''}
                    ${result.content_match ? '📝 Content match' : ''}
                </div>
            </div>
        `).join('');
    }
    
    async openSearchResult(path) {
        // Navigate to the parent directory and select the file
        const parentPath = path.substring(0, path.lastIndexOf('/'));
        this.currentPath = parentPath;
        await this.loadFiles();
        
        // Select the file
        setTimeout(() => {
            const fileItem = document.querySelector(`[data-path="${path}"]`);
            if (fileItem) {
                fileItem.scrollIntoView();
                fileItem.classList.add('selected');
            }
        }, 100);
    }
    
    // Modal functions
    openCreateModal() {
        document.getElementById('create-modal').style.display = 'flex';
    }
    
    closeModal(modalId) {
        document.getElementById(modalId).style.display = 'none';
    }
    
    async createItem() {
        const type = document.getElementById('create-type').value;
        const name = document.getElementById('create-name').value.trim();
        
        if (!name) {
            this.showNotification('Please enter a name', 'warning');
            return;
        }
        
        const path = this.currentPath + '/' + name;
        
        try {
            if (type === 'directory') {
                await this.callMCPTool('create_directory', { path });
            } else {
                // Create empty file (would need additional tool)
                this.showNotification('File creation not implemented yet', 'info');
                return;
            }
            
            this.closeModal('create-modal');
            this.loadFiles();
            this.showNotification(`${type} created successfully`, 'success');
        } catch (error) {
            console.error('❌ Failed to create item:', error);
            this.showNotification('Failed to create item: ' + error.message, 'error');
        }
    }
    
    async deleteSelectedFiles() {
        if (this.selectedFiles.size === 0) return;
        
        const confirmDelete = confirm(`Delete ${this.selectedFiles.size} item(s)?`);
        if (!confirmDelete) return;
        
        try {
            for (const filePath of this.selectedFiles) {
                await this.callMCPTool('delete_file', {
                    path: filePath,
                    recursive: true,
                    confirm: true
                });
            }
            
            this.selectedFiles.clear();
            this.loadFiles();
            this.showNotification('Files deleted successfully', 'success');
        } catch (error) {
            console.error('❌ Failed to delete files:', error);
            this.showNotification('Failed to delete files: ' + error.message, 'error');
        }
    }
    
    // MCP Communication
    async callMCPTool(toolName, args = {}) {
        // Simulate MCP tool call - in real implementation, this would call the actual MCP server
        const response = await fetch('/api/mcp', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                tool: toolName,
                args: args
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    }
    
    adjustLayout() {
        // Adjust layout for different screen sizes
        const sidebar = document.querySelector('.sidebar');
        const isMobile = window.innerWidth <= 640;
        
        if (isMobile) {
            sidebar.classList.add('mobile');
        } else {
            sidebar.classList.remove('mobile');
        }
    }
    
    handleFileDrop(event) {
        const files = Array.from(event.dataTransfer.files);
        console.log('Files dropped:', files);
        
        // Handle file upload - would need server implementation
        this.showNotification('File upload not implemented yet', 'info');
    }
    
    showContextMenu(event, file) {
        // Remove existing context menu
        document.querySelectorAll('.context-menu').forEach(menu => menu.remove());
        
        const menu = document.createElement('div');
        menu.className = 'context-menu';
        menu.style.left = event.pageX + 'px';
        menu.style.top = event.pageY + 'px';
        
        const menuItems = [
            { label: 'Open', action: () => this.openFile(file) },
            { label: 'Copy', action: () => this.copyFile(file) },
            { label: 'Cut', action: () => this.cutFile(file) },
            { label: 'Delete', action: () => this.deleteFile(file) },
            { label: 'Properties', action: () => this.showFileProperties(file) }
        ];
        
        menuItems.forEach(item => {
            const menuItem = document.createElement('div');
            menuItem.className = 'context-menu-item';
            menuItem.textContent = item.label;
            menuItem.addEventListener('click', () => {
                item.action();
                menu.remove();
            });
            menu.appendChild(menuItem);
        });
        
        document.body.appendChild(menu);
        
        // Remove menu on outside click
        setTimeout(() => {
            document.addEventListener('click', () => menu.remove(), { once: true });
        }, 0);
    }
    
    async copyFile(file) {
        // Implement file copy
        this.showNotification('Copy not implemented yet', 'info');
    }
    
    async cutFile(file) {
        // Implement file cut
        this.showNotification('Cut not implemented yet', 'info');
    }
    
    async deleteFile(file) {
        const confirmDelete = confirm(`Delete ${file.name}?`);
        if (!confirmDelete) return;
        
        try {
            await this.callMCPTool('delete_file', {
                path: file.path,
                recursive: file.type === 'directory',
                confirm: true
            });
            
            this.loadFiles();
            this.showNotification('File deleted successfully', 'success');
        } catch (error) {
            console.error('❌ Failed to delete file:', error);
            this.showNotification('Failed to delete file: ' + error.message, 'error');
        }
    }
    
    async showFileProperties(file) {
        try {
            const response = await this.callMCPTool('get_file_info', {
                path: file.path,
                include_permissions: true,
                include_checksums: this.config.enable_checksums
            });
            
            if (response.success) {
                const data = JSON.parse(response.result);
                this.displayFileProperties(data);
            }
        } catch (error) {
            console.error('❌ Failed to get file properties:', error);
            this.showNotification('Failed to get file properties: ' + error.message, 'error');
        }
    }
    
    displayFileProperties(fileInfo) {
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.style.display = 'flex';
        
        const permissionsHtml = fileInfo.permissions ? `
            <div class="form-group">
                <label class="form-label">Permissions</label>
                <div>
                    Readable: ${fileInfo.permissions.readable ? '✅' : '❌'}<br>
                    Writable: ${fileInfo.permissions.writable ? '✅' : '❌'}<br>
                    Executable: ${fileInfo.permissions.executable ? '✅' : '❌'}
                </div>
            </div>
        ` : '';
        
        const checksumsHtml = fileInfo.checksums ? `
            <div class="form-group">
                <label class="form-label">Checksums</label>
                <div>
                    MD5: ${fileInfo.checksums.md5}<br>
                    SHA-256: ${fileInfo.checksums.sha256}
                </div>
            </div>
        ` : '';
        
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3 class="modal-title">Properties - ${fileInfo.name}</h3>
                    <button class="close-btn" onclick="this.closest('.modal').remove()">&times;</button>
                </div>
                <div class="form-group">
                    <label class="form-label">Name</label>
                    <div>${fileInfo.name}</div>
                </div>
                <div class="form-group">
                    <label class="form-label">Type</label>
                    <div>${fileInfo.type}</div>
                </div>
                <div class="form-group">
                    <label class="form-label">Size</label>
                    <div>${fileInfo.size_formatted}</div>
                </div>
                <div class="form-group">
                    <label class="form-label">Modified</label>
                    <div>${new Date(fileInfo.modified).toLocaleString()}</div>
                </div>
                <div class="form-group">
                    <label class="form-label">Created</label>
                    <div>${new Date(fileInfo.created).toLocaleString()}</div>
                </div>
                ${permissionsHtml}
                ${checksumsHtml}
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Close on background click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }
}

// Global functions for HTML onclick events
window.openCreateModal = () => app.openCreateModal();
window.closeModal = (modalId) => app.closeModal(modalId);
window.createItem = () => app.createItem();
window.refreshFiles = () => app.refreshFiles();

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new FileManagerApp();
});

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FileManagerApp;
} 