/**
 * DATETIME COPY/PASTE MODULE
 * 
 * Chức năng:
 * - Copy/Paste giá trị đơn lẻ (right-click)
 * - Copy/Paste toàn bộ cột
 */

// Wrap trong IIFE để tránh duplicate declaration
(function() {
    'use strict';
    
    // Kiểm tra xem đã được khai báo chưa
    if (window.DateTimeCopyPasteModule) {
        return; // Đã load rồi, không load lại
    }
    
    // Clipboard storage
    const DateTimeClipboard = {
        single: null,
        column: null,
        columnName: null
    };

/**
 * Initialize copy/paste cho tất cả datetime inputs
 */
function initializeCopyPaste() {
    const datetimeInputs = document.querySelectorAll('.datetime-input');
    
    datetimeInputs.forEach(function(input) {
        // Right-click context menu
        input.addEventListener('contextmenu', function(e) {
            e.preventDefault();
            showContextMenu(e, input);
        });
    });
    
    // Setup column headers cho copy/paste cột
    setupColumnHeaders();
}

/**
 * Hiển thị context menu
 */
function showContextMenu(e, input) {
    // Remove existing menu
    const existingMenu = document.querySelector('.datetime-context-menu');
    if (existingMenu) existingMenu.remove();
    
    const menu = document.createElement('div');
    menu.className = 'datetime-context-menu';
    menu.style.position = 'fixed';
    menu.style.left = e.pageX + 'px';
    menu.style.top = e.pageY + 'px';
    menu.style.zIndex = '1060';
    menu.style.background = 'white';
    menu.style.border = '1px solid #dee2e6';
    menu.style.borderRadius = '4px';
    menu.style.boxShadow = '0 2px 8px rgba(0,0,0,0.15)';
    menu.style.padding = '5px 0';
    menu.style.minWidth = '150px';
    
    menu.innerHTML = `
        <div class="context-menu-item" data-action="copy">
            <i class="fas fa-copy me-2"></i> Copy
        </div>
        <div class="context-menu-item" data-action="paste" ${DateTimeClipboard.single ? '' : 'style="opacity: 0.5; cursor: not-allowed;"'}>
            <i class="fas fa-paste me-2"></i> Paste
        </div>
    `;
    
    document.body.appendChild(menu);
    
    // Event listeners
    menu.querySelector('[data-action="copy"]').addEventListener('click', function() {
        copyDateTime(input);
        menu.remove();
    });
    
    const pasteItem = menu.querySelector('[data-action="paste"]');
    if (DateTimeClipboard.single) {
        pasteItem.addEventListener('click', function() {
            pasteDateTime(input);
            menu.remove();
        });
    }
    
    // Close menu khi click outside
    setTimeout(function() {
        document.addEventListener('click', function closeMenu() {
            menu.remove();
            document.removeEventListener('click', closeMenu);
        });
    }, 100);
}

/**
 * Copy giá trị datetime
 */
function copyDateTime(input) {
    DateTimeClipboard.single = input.value;
    showFlash('Đã copy!', 'success');
}

/**
 * Paste giá trị datetime
 */
function pasteDateTime(input) {
    if (!DateTimeClipboard.single) {
        showFlash('Chưa có dữ liệu để paste!', 'error');
        return;
    }
    
    input.value = DateTimeClipboard.single;
    const wrapper = input.closest('.datetime-input-wrapper');
    const note = wrapper?.querySelector('.datetime-reference-note');
    if (note && window.DateTimePicker) {
        window.DateTimePicker.hideReferenceNote(note);
    }
    input.removeAttribute('data-ref-offset');
    if (window.TaskActions) {
        window.TaskActions.markRowDirty(input);
    }
    showFlash('Đã paste!', 'success');
}

/**
 * Setup column headers cho copy/paste cột
 */
function setupColumnHeaders() {
    const headers = document.querySelectorAll('.task-table thead th');
    
    headers.forEach(function(header, index) {
        // Chỉ setup cho các cột datetime (index 3-14)
        if (index >= 3 && index <= 14) {
            header.style.position = 'relative';
            
            header.addEventListener('mouseenter', function() {
                showColumnToolbar(this, index);
            });
            
            header.addEventListener('mouseleave', function() {
                setTimeout(function() {
                    const toolbar = this.querySelector('.column-toolbar');
                    if (toolbar && !toolbar.matches(':hover')) {
                        toolbar.remove();
                    }
                }.bind(this), 200);
            });
        }
    });
}

/**
 * Hiển thị toolbar trên header cột
 */
function showColumnToolbar(header, columnIndex) {
    // Remove existing toolbar
    const existingToolbar = header.querySelector('.column-toolbar');
    if (existingToolbar) return;
    
    const toolbar = document.createElement('div');
    toolbar.className = 'column-toolbar';
    toolbar.style.position = 'absolute';
    toolbar.style.top = '-30px';
    toolbar.style.right = '0';
    toolbar.style.display = 'flex';
    toolbar.style.gap = '5px';
    toolbar.style.zIndex = '10';
    
    toolbar.innerHTML = `
        <button class="btn btn-sm btn-outline-secondary" title="Copy tất cả" onclick="copyColumn(${columnIndex})">
            <i class="fas fa-copy"></i>
        </button>
        <button class="btn btn-sm btn-outline-secondary" title="Paste tất cả" onclick="pasteColumn(${columnIndex})">
            <i class="fas fa-paste"></i>
        </button>
    `;
    
    header.appendChild(toolbar);
}

/**
 * Copy toàn bộ cột
 */
function copyColumn(columnIndex) {
    const rows = document.querySelectorAll('.task-table tbody tr');
    const values = [];
    
    rows.forEach(function(row) {
        const input = row.cells[columnIndex]?.querySelector('.datetime-input');
        if (input) {
            values.push(input.value || '');
        }
    });
    
    DateTimeClipboard.column = values;
    DateTimeClipboard.columnName = columnIndex;
    showFlash(`Đã copy ${values.length} giá trị!`, 'success');
}

/**
 * Paste toàn bộ cột
 */
function pasteColumn(columnIndex) {
    if (!DateTimeClipboard.column) {
        showFlash('Chưa có dữ liệu để paste!', 'error');
        return;
    }
    
    const rows = document.querySelectorAll('.task-table tbody tr');
    const values = DateTimeClipboard.column;
    
    rows.forEach(function(row, index) {
        if (index < values.length) {
            const input = row.cells[columnIndex]?.querySelector('.datetime-input');
            if (input && values[index]) {
                input.value = values[index];
                const wrapper = input.closest('.datetime-input-wrapper');
                const note = wrapper?.querySelector('.datetime-reference-note');
                if (note && window.DateTimePicker) {
                    window.DateTimePicker.hideReferenceNote(note);
                }
                input.removeAttribute('data-ref-offset');
                if (window.TaskActions) {
                    window.TaskActions.markRowDirty(input);
                }
            }
        }
    });
    
    showFlash(`Đã paste ${values.length} giá trị!`, 'success');
}

// Export functions
window.DateTimeCopyPaste = {
    initialize: initializeCopyPaste,
    copyDateTime: copyDateTime,
    pasteDateTime: pasteDateTime,
    copyColumn: copyColumn,
    pasteColumn: pasteColumn
};

// Expose clipboard để có thể truy cập từ nơi khác
window.DateTimeClipboard = DateTimeClipboard;

// Mark đã load
window.DateTimeCopyPasteModule = true;
})();