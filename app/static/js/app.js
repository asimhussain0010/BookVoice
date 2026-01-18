/**
 * BookVoice Main JavaScript
 * Additional client-side functionality
 */

// Audio Player Helper
class AudioPlayer {
    constructor(audioElement) {
        this.audio = audioElement;
        this.isPlaying = false;
    }
    
    play() {
        this.audio.play();
        this.isPlaying = true;
    }
    
    pause() {
        this.audio.pause();
        this.isPlaying = false;
    }
    
    toggle() {
        if (this.isPlaying) {
            this.pause();
        } else {
            this.play();
        }
    }
    
    setVolume(volume) {
        this.audio.volume = volume;
    }
    
    seek(time) {
        this.audio.currentTime = time;
    }
}

// File Upload Helper
class FileUploader {
    constructor(options) {
        this.dropzone = options.dropzone;
        this.fileInput = options.fileInput;
        this.onFileSelected = options.onFileSelected;
        this.allowedTypes = options.allowedTypes || [];
        this.maxSize = options.maxSize || 50 * 1024 * 1024; // 50MB
        
        this.init();
    }
    
    init() {
        // Drag and drop events
        this.dropzone.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.dropzone.classList.add('active');
        });
        
        this.dropzone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            this.dropzone.classList.remove('active');
        });
        
        this.dropzone.addEventListener('drop', (e) => {
            e.preventDefault();
            this.dropzone.classList.remove('active');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFile(files[0]);
            }
        });
        
        // File input change
        this.fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleFile(e.target.files[0]);
            }
        });
    }
    
    handleFile(file) {
        // Validate file type
        if (this.allowedTypes.length > 0) {
            const fileExt = '.' + file.name.split('.').pop().toLowerCase();
            if (!this.allowedTypes.includes(fileExt)) {
                showToast(`File type not allowed. Allowed: ${this.allowedTypes.join(', ')}`, 'error');
                return;
            }
        }
        
        // Validate file size
        if (file.size > this.maxSize) {
            const maxMB = this.maxSize / (1024 * 1024);
            showToast(`File too large. Maximum size: ${maxMB}MB`, 'error');
            return;
        }
        
        // Call callback
        if (this.onFileSelected) {
            this.onFileSelected(file);
        }
    }
}

// Progress Bar Helper
function updateProgressBar(elementId, progress) {
    const progressBar = document.getElementById(elementId);
    if (progressBar) {
        progressBar.style.width = `${progress}%`;
        progressBar.setAttribute('aria-valuenow', progress);
    }
}

// Format helpers (already in base.html, but here for reference)
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

// Copy to clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard!', 'success');
    }).catch(() => {
        showToast('Failed to copy', 'error');
    });
}

// Download file
function downloadFile(url, filename) {
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Debounce helper
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Throttle helper
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Export for use in other scripts
window.AudioPlayer = AudioPlayer;
window.FileUploader = FileUploader;
window.updateProgressBar = updateProgressBar;
window.formatFileSize = formatFileSize;
window.formatTime = formatTime;
window.copyToClipboard = copyToClipboard;
window.downloadFile = downloadFile;
window.debounce = debounce;
window.throttle = throttle;