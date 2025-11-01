/**
 * TASK ACTIONS MODULE
 * 
 * Chức năng:
 * - Nút "Lưu tất cả" (FAB)
 * - Nhân bản Task
 * - Track dirty rows
 */

/**
 * Mark row là dirty (đã thay đổi)
 */
function markRowDirty(input) {
    const row = input.closest('tr');
    if (row) {
        row.setAttribute('data-dirty', 'true');
        updateSaveAllButton();
    }
}

/**
 * Update nút "Lưu tất cả"
 */
function updateSaveAllButton() {
    const dirtyRows = document.querySelectorAll('tr[data-dirty="true"]');
    let saveAllBtn = document.querySelector('.save-all-fab');
    
    if (dirtyRows.length > 0) {
        if (!saveAllBtn) {
            createSaveAllButton();
            saveAllBtn = document.querySelector('.save-all-fab');
        }
        if (saveAllBtn) {
            saveAllBtn.style.display = 'flex';
            const countSpan = saveAllBtn.querySelector('.save-count');
            if (countSpan) {
                countSpan.textContent = dirtyRows.length;
            }
        }
    } else {
        if (saveAllBtn) {
            saveAllBtn.style.display = 'none';
        }
    }
}

/**
 * Tạo nút "Lưu tất cả" ở cuối bảng
 */
function createSaveAllButton() {
    // Tìm table wrapper
    const tableWrapper = document.querySelector('.task-table-wrapper');
    if (!tableWrapper) {
        console.error('Không tìm thấy .task-table-wrapper');
        return;
    }
    
    // Kiểm tra xem đã có button chưa
    let fab = tableWrapper.querySelector('.save-all-fab');
    if (fab) return;
    
    // Tạo button
    fab = document.createElement('button');
    fab.className = 'save-all-fab';
    fab.innerHTML = `
        <i class="fas fa-save"></i> 
        Lưu tất cả (<span class="save-count">0</span>)
    `;
    
    fab.addEventListener('click', function() {
        saveAllRows();
    });
    
    // Chèn vào SAU table wrapper, không phải trong table
    const table = tableWrapper.querySelector('.task-table');
    if (table) {
        // Tìm parent của tableWrapper để chèn button vào đó
        const parent = tableWrapper.parentNode;
        if (parent) {
            // Tạo wrapper cho button để căn giữa
            const buttonWrapper = document.createElement('div');
            buttonWrapper.style.textAlign = 'center';
            buttonWrapper.style.marginTop = '15px';
            buttonWrapper.appendChild(fab);
            parent.insertBefore(buttonWrapper, tableWrapper.nextSibling);
        } else {
            // Fallback: chèn vào sau table
            table.parentNode.insertBefore(fab, table.nextSibling);
        }
    } else {
        tableWrapper.appendChild(fab);
    }
}

/**
 * Lưu tất cả rows dirty
 */
async function saveAllRows() {
    const dirtyRows = document.querySelectorAll('tr[data-dirty="true"]');
    if (dirtyRows.length === 0) {
        showFlash('Không có thay đổi nào để lưu!', 'error');
        return;
    }
    
    const total = dirtyRows.length;
    let successCount = 0;
    let failCount = 0;
    
    // Disable button trong lúc save
    const saveAllBtn = document.querySelector('.save-all-fab');
    if (saveAllBtn) {
        saveAllBtn.disabled = true;
        saveAllBtn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Đang lưu...`;
    }
    
    // Lưu từng row
    for (let i = 0; i < dirtyRows.length; i++) {
        const row = dirtyRows[i];
        const saveBtn = row.querySelector('button[onclick*="saveRow"]');
        
        if (saveBtn) {
            try {
                await saveRowPromise(saveBtn);
                successCount++;
                row.removeAttribute('data-dirty');
            } catch (error) {
                failCount++;
            }
        }
        
        // Update progress
        if (saveAllBtn) {
            saveAllBtn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Đang lưu... (${i + 1}/${total})`;
        }
    }
    
    // Re-enable button
    if (saveAllBtn) {
        saveAllBtn.disabled = false;
    }
    
    // Update button
    updateSaveAllButton();
    
    // Show result
    if (failCount === 0) {
        showFlash(`Đã lưu ${successCount} tác vụ thành công!`, 'success');
    } else {
        showFlash(`Đã lưu ${successCount}/${total} tác vụ. ${failCount} tác vụ lỗi.`, 'error');
    }
}

/**
 * Promise wrapper cho saveRow
 */
function saveRowPromise(btn) {
    return new Promise(function(resolve, reject) {
        const data = getRowData(btn);
        const isNew = !data.task_id;
        const url = isNew ? '/api/task' : `/api/task/${data.task_id}`;

        // Thu thập offsets
        const allInputs = data.tr.querySelectorAll('.datetime-input');
        const offsets = {};
        allInputs.forEach(function(input) {
            const column = input.getAttribute('data-column');
            const offset = input.getAttribute('data-ref-offset');
            if (offset) {
                offsets[column] = offset;
            }
        });
        
        const payload = {
            title: data.title,
            description: data.description,
            start_date: data.start_date,
            end_date: data.end_date,
            deadline: data.deadline,
            notification_time: data.notification_time,
            notif1: data.notif1,
            notif2: data.notif2,
            notif3: data.notif3,
            notif4: data.notif4,
            notif5: data.notif5,
            notif6: data.notif6,
            notif7: data.notif7,
            notif8: data.notif8,
            status: data.status,
            offsets: offsets // THÊM offsets
        };
        
        fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        .then(r => r.json())
        .then(res => {
            if (res.status === 'success') {
                if (isNew && res.task_id) {
                    data.tr.setAttribute('data-task-id', res.task_id);
                }
                resolve(res);
            } else {
                reject(new Error(res.message || 'Lưu không thành công'));
            }
        })
        .catch(error => reject(error));
    });
}

/**
 * Nhân bản Task
 */
function duplicateRow(btn) {
    const row = btn.closest('tr');
    const tbody = row.parentElement;
    
    // Tạo row mới
    const newRow = row.cloneNode(true);
    
    // Xóa task_id (để tạo task mới)
    newRow.removeAttribute('data-task-id');
    newRow.removeAttribute('data-dirty');
    
    // Cập nhật STT
    const rowIndex = Array.from(tbody.rows).indexOf(row);
    const newRowIndex = rowIndex + 1;
    newRow.cells[0].textContent = newRowIndex;
    
    // Cập nhật các STT sau đó
    for (let i = newRowIndex; i < tbody.rows.length; i++) {
        tbody.rows[i].cells[0].textContent = i + 1;
    }
    
    // Xóa ghi chú tham chiếu (nếu có)
    const datetimeWrappers = newRow.querySelectorAll('.datetime-input-wrapper');
    datetimeWrappers.forEach(function(wrapper) {
        const note = wrapper.querySelector('.datetime-reference-note');
        if (note) {
            note.style.display = 'none';
            const input = wrapper.querySelector('.datetime-input');
            if (input) {
                input.removeAttribute('data-ref-offset');
            }
        }
    });
    
    // Thêm "- Copy" vào title
    const titleCell = newRow.cells[1];
    if (titleCell && titleCell.textContent.trim()) {
        titleCell.textContent = titleCell.textContent.trim() + ' - Copy';
    }
    
    // Đổi màu nền
    if (row.style.backgroundColor === 'rgb(227, 242, 253)' || row.style.backgroundColor === '#e3f2fd') {
        newRow.style.backgroundColor = '#ffffff';
    } else {
        newRow.style.backgroundColor = '#e3f2fd';
    }
    
    // Chèn row mới ngay sau row hiện tại
    tbody.insertBefore(newRow, row.nextSibling);
    
    // Re-initialize datetime pickers cho row mới
    const newInputs = newRow.querySelectorAll('.datetime-input');
    newInputs.forEach(function(input) {
        // Đảm bảo có wrapper
        if (!input.closest('.datetime-input-wrapper')) {
            const wrapper = document.createElement('div');
            wrapper.className = 'datetime-input-wrapper';
            input.parentNode.insertBefore(wrapper, input);
            wrapper.appendChild(input);
        }
        
        // Tạo popup nếu chưa có
        if (window.DateTimePicker) {
            window.DateTimePicker.createPopupForInput(input);
            window.DateTimePicker.setupInputEvents(input);
        }
    });
    
    // Mark row mới là dirty
    newRow.setAttribute('data-dirty', 'true');
    updateSaveAllButton();
    
    // Scroll đến row mới
    newRow.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    
    // Highlight row mới
    const originalBg = newRow.style.backgroundColor;
    newRow.style.transition = 'background-color 0.3s';
    newRow.style.backgroundColor = '#fff3cd';
    setTimeout(function() {
        newRow.style.backgroundColor = originalBg;
    }, 1000);
    
    showFlash('Đã nhân bản task! Vui lòng sửa và lưu.', 'success');
}

// Export functions
if (typeof window !== 'undefined') {
    window.TaskActions = {
        markRowDirty: markRowDirty,
        updateSaveAllButton: updateSaveAllButton,
        duplicateRow: duplicateRow
    };
}