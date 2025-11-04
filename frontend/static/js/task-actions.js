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
    // Tìm table wrapper (có thể là .task-table-wrapper hoặc .table-responsive)
    const tableWrapper = document.querySelector('.task-table-wrapper') || 
                         document.querySelector('.table-responsive');
    if (!tableWrapper) {
        console.error('Không tìm thấy table wrapper');
        return;
    }
    
    // Kiểm tra xem đã có button chưa
    let fab = document.querySelector('.save-all-fab');
    if (fab) return;
    
    // Tạo button
    fab = document.createElement('button');
    fab.className = 'save-all-fab btn btn-primary';
    fab.style.cssText = 'display: none; margin: 15px auto; padding: 10px 24px;';
    fab.innerHTML = `
        <i class="fas fa-save"></i> 
        Lưu tất cả (<span class="save-count">0</span>)
    `;
    
    fab.addEventListener('click', function() {
        saveAllRows();
    });
    
    // Chèn vào sau table wrapper hoặc vào save-all-wrapper
    const saveAllWrapper = document.querySelector('#saveAllWrapper') || 
                          document.querySelector('.save-all-wrapper');
    if (saveAllWrapper) {
        saveAllWrapper.appendChild(fab);
    } else {
        // Fallback: chèn vào sau table wrapper
        tableWrapper.parentNode.insertBefore(fab, tableWrapper.nextSibling);
    }
}

/**
 * Lưu tất cả rows dirty
 */
function saveAllRows() {
    const saveBtn = document.querySelector('.save-all-fab');
    if (!saveBtn) return;
    
    const dirtyRows = document.querySelectorAll('[data-dirty="true"]');
    if (dirtyRows.length === 0) {
        console.log('✓ No dirty rows to save');
        return;
    }
    
    // Show spinner
    const originalHTML = saveBtn.innerHTML;
    saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Đang lưu...';
    saveBtn.disabled = true;
    
    // ✅ FIX: Tìm button trong mỗi row thay vì truyền row trực tiếp
    const promises = Array.from(dirtyRows).map(function(row) {
        // Tìm button "Lưu" trong row (button đầu tiên trong actions column)
        const actionsCell = row.cells[row.cells.length - 1]; // Cột cuối cùng
        const saveBtnInRow = actionsCell.querySelector('button[onclick*="saveRow"]');
        
        if (!saveBtnInRow) {
            // Nếu không tìm thấy, tạo một button tạm để pass vào getRowData
            const tempBtn = document.createElement('button');
            tempBtn.style.display = 'none';
            row.appendChild(tempBtn);
            return saveRowPromise(tempBtn);
        }
        
        return saveRowPromise(saveBtnInRow);
    });
    
    Promise.all(promises)
        .then(results => {
            const successCount = results.filter(r => r && r.status === 'success').length;
            const failCount = results.length - successCount;
            
            if (failCount === 0) {
                alert(`✓ Đã lưu thành công ${successCount} tác vụ!`);
            } else {
                alert(`⚠️ Lưu ${successCount} thành công, ${failCount} thất bại.`);
            }
            
            updateSaveAllButton();
        })
        .catch(error => {
            console.error('❌ Error saving all:', error);
            alert('Lỗi khi lưu: ' + error.message);
        })
        .finally(() => {
            // RESTORE BUTTON
            saveBtn.innerHTML = originalHTML;
            saveBtn.disabled = false;
        });
}

/**
 * Promise wrapper cho saveRow
 */
function saveRowPromise(btn) {
    return new Promise(function(resolve, reject) {
        const data = getRowData(btn);
        // ✅ FIX: Kiểm tra cả "NEW" và empty string
        const isNew = !data.task_id || data.task_id === 'NEW' || data.task_id === '';
        const url = isNew ? '/api/task' : `/api/task/${data.task_id}`;
        
        console.log('🔍 DEBUG saveRowPromise:', {
            task_id: data.task_id,
            isNew: isNew,
            url: url
        });

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
            offsets: offsets
        };
        
        fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        .then(r => r.json())
        .then(res => {
            console.log('🔍 DEBUG saveRowPromise response:', res);
            if (res.status === 'success') {
                if (isNew && res.task_id) {
                    data.tr.setAttribute('data-task-id', res.task_id);
                    console.log('  - Updated task_id:', res.task_id);
                }
                resolve(res);
            } else {
                reject(new Error(res.message || 'Lưu không thành công'));
            }
        })
        .catch(error => {
            console.error('❌ Error in saveRowPromise:', error);
            reject(error);
        });
    });
}

/**
 * Nhân bản Task
 */
function duplicateRow(btn) {
    console.log('🔍 DEBUG duplicateRow: START');
    const row = btn.closest('tr');
    const tbody = row.parentElement;
    
    // ✅ FIX: Xóa tất cả popups trong row trước khi clone
    const oldPopups = row.querySelectorAll('.datetime-popup');
    oldPopups.forEach(function(popup) {
        popup.remove();
    });
    
    // Tạo row mới
    const newRow = row.cloneNode(true);
    console.log('  - New row cloned:', newRow);
    
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
    
    // ✅ FIX: Xóa popups đã được clone (sẽ tạo lại sau)
    const clonedPopups = newRow.querySelectorAll('.datetime-popup');
    clonedPopups.forEach(function(popup) {
        console.log('  - Removing cloned popup:', popup);
        popup.remove();
    });
    
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
    console.log('  - New row inserted');
    
    // ✅ FIX: Re-initialize datetime pickers cho row mới (sau khi insert vào DOM)
    setTimeout(function() {
        const newInputs = newRow.querySelectorAll('.datetime-input');
        console.log(`  - Found ${newInputs.length} datetime inputs in new row`);
        
        newInputs.forEach(function(input, index) {
            console.log(`  - Processing input ${index + 1}:`, input);
            
            // Đảm bảo có wrapper
            let wrapper = input.closest('.datetime-input-wrapper');
            if (!wrapper) {
                console.log(`    - Creating wrapper for input ${index + 1}`);
                wrapper = document.createElement('div');
                wrapper.className = 'datetime-input-wrapper';
                input.parentNode.insertBefore(wrapper, input);
                wrapper.appendChild(input);
            }
            
            // ✅ FIX: Xóa popup cũ nếu có (từ clone)
            const oldPopup = wrapper.querySelector('.datetime-popup');
            if (oldPopup) {
                console.log(`    - Removing old popup from input ${index + 1}`);
                oldPopup.remove();
            }
            
            // ✅ FIX: Tạo popup mới và setup events
            if (window.DateTimePicker) {
                console.log(`    - Creating popup for input ${index + 1}`);
                window.DateTimePicker.createPopupForInput(input);
                
                console.log(`    - Setting up events for input ${index + 1}`);
                window.DateTimePicker.setupInputEvents(input);
            } else {
                console.error('    ❌ DateTimePicker not available!');
            }
        });
        
        // ✅ FIX: Initialize copy/paste cho row mới
        if (window.DateTimeCopyPaste && window.DateTimeCopyPaste.initializeCopyPaste) {
            console.log('  - Initializing copy/paste for new row');
            window.DateTimeCopyPaste.initializeCopyPaste();
        }
        
        console.log('🔍 DEBUG duplicateRow: COMPLETE');
    }, 100);
    
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