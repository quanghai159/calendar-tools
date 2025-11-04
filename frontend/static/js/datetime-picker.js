/**
 * DATETIME PICKER MODULE
 * 
 * Chức năng:
 * - Tạo popup overlay khi click vào input datetime
 * - Tự động set Now khi click vào input rỗng
 * - Quick Actions (+1h, +3h, +1d, ...)
 * - Custom Offset với đầy đủ đơn vị
 * - Hiển thị ghi chú tham chiếu bên ngoài
 */

// Wrap trong IIFE để tránh duplicate declaration
(function() {
    'use strict';
    
    // Kiểm tra xem đã được khai báo chưa
    if (window.DateTimePickerModule) {
        return; // Đã load rồi, không load lại
    }
    
    // Mapping đơn vị offset
    const OFFSET_UNITS = {
        's': { name: 'giây', ms: 1000 },
        'm': { name: 'phút', ms: 60 * 1000 },
        'h': { name: 'giờ', ms: 60 * 60 * 1000 },
        'd': { name: 'ngày', ms: 24 * 60 * 60 * 1000 },
        'w': { name: 'tuần', ms: 7 * 24 * 60 * 60 * 1000 },
        'M': { name: 'tháng', ms: 30 * 24 * 60 * 60 * 1000 },
        'q': { name: 'quý', ms: 90 * 24 * 60 * 60 * 1000 },
        'y': { name: 'năm', ms: 365 * 24 * 60 * 60 * 1000 }
    };

// Thứ tự cột datetime trong table
const COLUMN_ORDER = [
    'start_date',      // Index 3
    'end_date',        // Index 4
    'deadline',        // Index 5
    'notification_time', // Index 6
    'notif1',          // Index 7
    'notif2',          // Index 8
    'notif3',          // Index 9
    'notif4',          // Index 10
    'notif5',          // Index 11
    'notif6',          // Index 12
    'notif7',          // Index 13
    'notif8'           // Index 14
];

/**
 * Initialize tất cả datetime inputs khi page load
 */
function initializeDateTimePickers() {
    console.log('🔍 DEBUG initializeDateTimePickers: START');
    const datetimeInputs = document.querySelectorAll('.datetime-input');
    console.log(`  - Found ${datetimeInputs.length} datetime inputs`);
    
    if (datetimeInputs.length === 0) {
        console.warn('⚠️ No datetime inputs found!');
        return;
    }
    
    datetimeInputs.forEach(function(input, index) {
        console.log(`  - Processing input ${index + 1}:`, {
            element: input,
            value: input.value,
            readonly: input.hasAttribute('readonly'),
            wrapper: input.closest('.datetime-input-wrapper'),
            hasPopup: !!input.closest('.datetime-input-wrapper')?.querySelector('.datetime-popup')
        });
        
        // Tạo popup nếu chưa có
        const wrapper = input.closest('.datetime-input-wrapper');
        if (!wrapper) {
            console.error(`  ❌ Input ${index + 1} has no wrapper!`);
            return;
        }
        
        if (!wrapper.querySelector('.datetime-popup')) {
            console.log(`  - Creating popup for input ${index + 1}...`);
            createPopupForInput(input);
        } else {
            console.log(`  - Input ${index + 1} already has popup`);
        }
        
        // Setup event listeners
        console.log(`  - Setting up events for input ${index + 1}...`);
        setupInputEvents(input);
    });
    
    console.log('🔍 DEBUG initializeDateTimePickers: COMPLETE');
}

/**
 * Setup event listeners cho input
 */
function setupInputEvents(input) {
    console.log('🔍 DEBUG setupInputEvents: START');
    console.log('  - Input:', input);
    console.log('  - Input class:', input.className);
    console.log('  - Input readonly:', input.hasAttribute('readonly'));
    console.log('  - Input type:', input.type);
    
    const wrapper = input.closest('.datetime-input-wrapper');
    if (!wrapper) {
        console.error('❌ No wrapper found for input in setupInputEvents');
        return;
    }
    
    console.log('  - Wrapper found:', wrapper);
    
    // Tạo popup nếu chưa có
    if (!wrapper.querySelector('.datetime-popup')) {
        console.log('  - Creating popup...');
        createPopupForInput(input);
    } else {
        console.log('  - Popup already exists');
    }
    
    // Remove old listeners bằng cách tạo một input mới
    console.log('  - Adding event listeners...');
    
    // Click event
    input.addEventListener('click', function(e) {
        console.log('🔍 DEBUG: Input clicked event fired');
        console.log('  - Event:', e);
        console.log('  - Target:', e.target);
        console.log('  - Current target:', e.currentTarget);
        e.preventDefault();
        e.stopPropagation();
        handleInputClick(this);
    }, true);
    
    input.addEventListener('mousedown', function(e) {
        console.log('🔍 DEBUG: Input mousedown event fired');
        e.preventDefault();
        e.stopPropagation();
        handleInputClick(this);
    }, true);
    
    // Touch events cho mobile
    input.addEventListener('touchstart', function(e) {
        console.log('🔍 DEBUG: Input touchstart event fired');
        e.preventDefault();
        e.stopPropagation();
        handleInputClick(this);
    }, true);
    
    // Focus event
    input.addEventListener('focus', function(e) {
        console.log('🔍 DEBUG: Input focus event fired');
        e.preventDefault();
        e.stopPropagation();
        handleInputClick(this);
    }, true);
    
    // Thêm double-click để test
    input.addEventListener('dblclick', function(e) {
        console.log('🔍 DEBUG: Input double-click event fired');
        e.preventDefault();
        e.stopPropagation();
        handleInputClick(this);
    }, true);
    
    console.log('🔍 DEBUG setupInputEvents: COMPLETE');
}

/**
 * Xử lý khi click vào input
 */
function handleInputClick(input) {
    console.log('🔍 DEBUG handleInputClick: START');
    console.log('  - Input:', input);
    console.log('  - Input value:', input.value);
    console.log('  - Input readonly:', input.hasAttribute('readonly'));
    console.log('  - Input disabled:', input.disabled);
    console.log('  - Input style pointer-events:', getComputedStyle(input).pointerEvents);
    console.log('  - Input parent:', input.parentElement);
    console.log('  - Input wrapper:', input.closest('.datetime-input-wrapper'));
    
    // Nếu input chưa có giá trị → Tự động set = Now
    if (!input.value || input.value.trim() === '') {
        console.log('  - Input is empty, setting to Now...');
        const now = new Date();
        const nowStr = formatLocalDateTime(now);
        input.value = nowStr;
        console.log('  - Set value to:', nowStr);
    }
    
    console.log('  - Calling openPopup...');
    openPopup(input);
    console.log('🔍 DEBUG handleInputClick: COMPLETE');
}

/**
 * Tạo popup cho input
 */
function createPopupForInput(input) {
    console.log('🔍 DEBUG createPopupForInput: START');
    console.log('  - Input:', input);
    
    const wrapper = input.closest('.datetime-input-wrapper');
    if (!wrapper) {
        console.log('  - No wrapper found, creating new wrapper...');
        const newWrapper = document.createElement('div');
        newWrapper.className = 'datetime-input-wrapper';
        input.parentNode.insertBefore(newWrapper, input);
        newWrapper.appendChild(input);
        console.log('  - Wrapper created:', newWrapper);
        return createPopupForInput(input);
    }
    
    console.log('  - Wrapper found:', wrapper);
    
    // Kiểm tra xem đã có popup chưa
    if (wrapper.querySelector('.datetime-popup')) {
        console.log('  - Popup already exists, skipping...');
        return;
    }
    
    console.log('  - Creating popup element...');
    
    // Tạo note BÊN NGOÀI (nếu chưa có)
    let note = wrapper.querySelector('.datetime-reference-note');
    if (!note) {
        console.log('  - Creating note element...');
        note = document.createElement('div');
        note.className = 'datetime-reference-note';
        note.style.display = 'none';
        note.innerHTML = `
            <small class="text-muted">
                <i class="fas fa-link"></i> 
                <span class="ref-offset"></span>
            </small>
        `;
        wrapper.appendChild(note);
        console.log('  - Note created:', note);
    } else {
        console.log('  - Note already exists:', note);
    }
    
    // Tạo popup
    const popup = document.createElement('div');
    popup.className = 'datetime-popup';
    popup.style.display = 'none';
    popup.innerHTML = `
        <div class="datetime-popup-header">
            <span class="popup-title">Chọn thời gian</span>
            <button class="btn-close-popup" type="button">
                <i class="fas fa-times"></i>
            </button>
        </div>
        <div class="datetime-popup-calendar">
            <input type="datetime-local" class="datetime-popup-input" 
                   value="${input.value || ''}">
        </div>
        <div class="datetime-popup-quick">
            <div class="quick-label">Nhanh:</div>
            <div class="quick-buttons">
                <button class="quick-btn" data-offset="+1h" type="button">+1h</button>
                <button class="quick-btn" data-offset="+3h" type="button">+3h</button>
                <button class="quick-btn" data-offset="+6h" type="button">+6h</button>
                <button class="quick-btn" data-offset="+12h" type="button">+12h</button>
                <button class="quick-btn" data-offset="+1d" type="button">+1d</button>
                <button class="quick-btn" data-offset="+2d" type="button">+2d</button>
                <button class="quick-btn" data-offset="+1w" type="button">+1w</button>
                <button class="quick-btn" data-offset="+1M" type="button">+(1M</button>
            </div>
            <div class="quick-custom">
                <input type="number" placeholder="Số" min="1" max="999" 
                       class="custom-amount">
                <select class="custom-unit">
                    <option value="s">Giây</option>
                    <option value="m">Phút</option>
                    <option value="h" selected>Giờ</option>
                    <option value="d">Ngày</option>
                    <option value="w">Tuần</option>
                    <option value="M">Tháng</option>
                    <option value="q">Quý</option>
                    <option value="y">Năm</option>
                </select>
                <button class="btn-apply-custom" type="button">Áp dụng</button>
            </div>
        </div>
    `;
    
    wrapper.appendChild(popup);
    console.log('  - Popup created and appended:', popup);
    console.log('  - Popup HTML:', popup.outerHTML.substring(0, 200) + '...');
    
    // Setup events cho popup
    console.log('  - Setting up popup events...');
    setupPopupEvents(input, popup, note);
    
    console.log('🔍 DEBUG createPopupForInput: COMPLETE');
}

/**
 * Setup events cho popup
 */
function setupPopupEvents(input, popup, note) {
    console.log('🔍 DEBUG setupPopupEvents: START');
    console.log('  - Input:', input);
    console.log('  - Popup:', popup);
    console.log('  - Note:', note);
    
    // ✅ FIX: Query từ DOM thay vì nhận từ parameters
    const popupInput = popup.querySelector('.datetime-popup-input');
    const btnClose = popup.querySelector('.btn-close-popup');
    const quickBtns = popup.querySelectorAll('.quick-btn');
    const btnApplyCustom = popup.querySelector('.btn-apply-custom');
    const refOffset = note ? note.querySelector('.ref-offset') : null;
    
    console.log('  - Elements found:', {
        popupInput: !!popupInput,
        btnClose: !!btnClose,
        quickBtns: quickBtns.length,
        btnApplyCustom: !!btnApplyCustom,
        refOffset: !!refOffset
    });
    
    // ✅ FIX: Đảm bảo popup input KHÔNG có readonly
    if (popupInput) {
        popupInput.removeAttribute('readonly');
        popupInput.setAttribute('type', 'datetime-local');
    }
    
    // ✅ FIX: Remove old event listeners bằng cách clone popup elements
    // (Hoặc dùng một cách khác để remove listeners)
    
    // ✅ FIX: Cho phép gõ đầy đủ trước khi sync
    let typingTimeout;
    if (popupInput) {
        // Remove old listeners bằng cách replace với clone
        const newPopupInput = popupInput.cloneNode(true);
        popupInput.parentNode.replaceChild(newPopupInput, popupInput);
        const actualPopupInput = newPopupInput;
        
        actualPopupInput.addEventListener('input', function(e) {
            clearTimeout(typingTimeout);
            typingTimeout = setTimeout(function() {
                if (actualPopupInput.value) {
                    input.value = actualPopupInput.value;
                    const row = input.closest('tr');
                    if (row) {
                        row.setAttribute('data-dirty', 'true');
                        if (window.TaskActions && window.TaskActions.updateSaveAllButton) {
                            window.TaskActions.updateSaveAllButton();
                        }
                    }
                }
            }, 500);
        });
        
        actualPopupInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                clearTimeout(typingTimeout);
                
                if (actualPopupInput.value) {
                    input.value = actualPopupInput.value;
                    input.removeAttribute('data-ref-offset');
                    if (note) {
                        hideReferenceNote(note);
                    }
                    
                    const row = input.closest('tr');
                    if (row) {
                        row.setAttribute('data-dirty', 'true');
                        if (window.TaskActions && window.TaskActions.updateSaveAllButton) {
                            window.TaskActions.updateSaveAllButton();
                        }
                    }
                }
                
                closePopup(popup);
            } else if (e.key === 'Escape') {
                e.preventDefault();
                closePopup(popup);
            }
        });
        
        actualPopupInput.addEventListener('blur', function(e) {
            setTimeout(function() {
                if (!popup.contains(document.activeElement)) {
                    if (actualPopupInput.value) {
                        input.value = actualPopupInput.value;
                        const row = input.closest('tr');
                        if (row) {
                            row.setAttribute('data-dirty', 'true');
                            if (window.TaskActions && window.TaskActions.updateSaveAllButton) {
                                window.TaskActions.updateSaveAllButton();
                            }
                        }
                    }
                    closePopup(popup);
                }
            }, 200);
        });
    }
    
    // ✅ FIX: Quick buttons - Remove old listeners và attach mới
    if (quickBtns && quickBtns.length > 0) {
        quickBtns.forEach(function(btn) {
            // Clone button để remove old listeners
            const newBtn = btn.cloneNode(true);
            btn.parentNode.replaceChild(newBtn, btn);
            
            newBtn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                console.log('🔍 DEBUG: Quick button clicked:', this.getAttribute('data-offset'));
                const offset = this.getAttribute('data-offset');
                const currentPopupInput = popup.querySelector('.datetime-popup-input');
                applyQuickAction(input, currentPopupInput, offset, note, refOffset);
            });
        });
    }
    
    // ✅ FIX: Custom apply - Remove old listeners và attach mới
    if (btnApplyCustom) {
        const newBtnApply = btnApplyCustom.cloneNode(true);
        btnApplyCustom.parentNode.replaceChild(newBtnApply, btnApplyCustom);
        
        newBtnApply.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('🔍 DEBUG: Custom apply clicked');
            const amount = popup.querySelector('.custom-amount').value;
            const unit = popup.querySelector('.custom-unit').value;
            if (amount && amount > 0) {
                const offset = `+${amount}${unit}`;
                const currentPopupInput = popup.querySelector('.datetime-popup-input');
                applyQuickAction(input, currentPopupInput, offset, note, refOffset);
            }
        });
    }
    
    // ✅ FIX: Close button - Remove old listeners và attach mới
    if (btnClose) {
        const newBtnClose = btnClose.cloneNode(true);
        btnClose.parentNode.replaceChild(newBtnClose, btnClose);
        
        newBtnClose.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('🔍 DEBUG: Close button clicked');
            closePopup(popup);
        });
    }
    
    // ✅ FIX: Click outside để đóng popup
    document.addEventListener('click', function closeOnOutsideClick(e) {
        if (!popup.contains(e.target) && !input.contains(e.target)) {
            console.log('🔍 DEBUG: Clicked outside popup, closing...');
            closePopup(popup);
            document.removeEventListener('click', closeOnOutsideClick);
        }
    });
    
    console.log('🔍 DEBUG setupPopupEvents: COMPLETE');
}

/**
 * Mở popup
 */
function openPopup(input) {
    console.log('🔍 DEBUG openPopup: START');
    console.log('  - Input:', input);
    console.log('  - Input tagName:', input.tagName);
    console.log('  - Input value:', input.value);
    console.log('  - Input readonly:', input.hasAttribute('readonly'));
    console.log('  - Input disabled:', input.disabled);
    console.log('  - Input computed style:', {
        display: getComputedStyle(input).display,
        visibility: getComputedStyle(input).visibility,
        pointerEvents: getComputedStyle(input).pointerEvents,
        zIndex: getComputedStyle(input).zIndex
    });
    
    const wrapper = input.closest('.datetime-input-wrapper');
    if (!wrapper) {
        console.error('❌ No wrapper found for input');
        return;
    }
    
    console.log('  - Wrapper found:', wrapper);
    
    let popup = wrapper.querySelector('.datetime-popup');
    if (!popup) {
        console.log('  - Popup not found, creating...');
        createPopupForInput(input);
        popup = wrapper.querySelector('.datetime-popup');
    }
    
    if (!popup) {
        console.error('❌ Failed to create popup');
        return;
    }
    
    console.log('  - Popup found:', popup);
    console.log('  - Popup computed style BEFORE:', {
        display: getComputedStyle(popup).display,
        visibility: getComputedStyle(popup).visibility,
        position: getComputedStyle(popup).position,
        zIndex: getComputedStyle(popup).zIndex,
        top: getComputedStyle(popup).top,
        left: getComputedStyle(popup).left
    });
    
    // ✅ FIX: Remove readonly để cho phép gõ thủ công
    input.removeAttribute('readonly');
    console.log('  - Removed readonly from input');
    
    // Set value cho popup input
    const popupInput = popup.querySelector('.datetime-popup-input');
    if (popupInput) {
        popupInput.value = input.value || '';
        popupInput.removeAttribute('readonly');
        console.log('  - Popup input ready:', popupInput);
    } else {
        console.error('❌ Popup input not found!');
    }
    
    // Tính toán vị trí popup
    const rect = input.getBoundingClientRect();
    console.log('  - Input rect:', rect);
    
    const viewportHeight = window.innerHeight;
    const viewportWidth = window.innerWidth;
    const popupHeight = 300;
    const popupWidth = 350;
    
    let top = rect.bottom + 5;
    let left = rect.left;
    
    if (top + popupHeight > viewportHeight) {
        top = rect.top - popupHeight - 5;
    }
    
    if (left + popupWidth > viewportWidth) {
        left = viewportWidth - popupWidth - 10;
    }
    
    if (left < 10) {
        left = 10;
    }
    
    popup.style.position = 'fixed';
    popup.style.top = top + 'px';
    popup.style.left = left + 'px';
    popup.style.zIndex = '99999';
    popup.style.display = 'block';
    
    console.log('  - Popup style set:', {
        position: popup.style.position,
        top: popup.style.top,
        left: popup.style.left,
        zIndex: popup.style.zIndex,
        display: popup.style.display
    });
    
    console.log('  - Popup computed style AFTER:', {
        display: getComputedStyle(popup).display,
        visibility: getComputedStyle(popup).visibility,
        position: getComputedStyle(popup).position,
        zIndex: getComputedStyle(popup).zIndex,
        top: getComputedStyle(popup).top,
        left: getComputedStyle(popup).left
    });
    
    // Focus vào popup input
    if (popupInput) {
        setTimeout(function() {
            popupInput.focus();
            popupInput.select();
            console.log('  - Popup input focused');
            console.log('  - Popup input activeElement:', document.activeElement);
        }, 100);
    }
    
    console.log('🔍 DEBUG openPopup: COMPLETE');
}

/**
 * Đóng popup
 */
function closePopup(popup) {
    console.log('🔍 DEBUG closePopup: START');
    console.log('  - Popup:', popup);
    
    if (!popup) {
        console.error('  ❌ Popup is null!');
        return;
    }
    
    console.log('  - Popup display BEFORE:', getComputedStyle(popup).display);
    
    popup.style.display = 'none';
    
    console.log('  - Popup display AFTER:', getComputedStyle(popup).display);
    
    // ✅ FIX: Restore readonly sau khi đóng popup
    const wrapper = popup.closest('.datetime-input-wrapper');
    if (wrapper) {
        const input = wrapper.querySelector('.datetime-input');
        if (input) {
            input.setAttribute('readonly', 'readonly');
            console.log('  - Restored readonly to input');
        }
    }
    
    console.log('🔍 DEBUG closePopup: COMPLETE');
}

/**
 * Apply Quick Action
 */
function applyQuickAction(input, popupInput, offset, note, refOffset) {
    // Tìm cột trước đó
    const previousInput = getPreviousColumnInput(input);
    const referenceValue = previousInput ? previousInput.value : null;
    
    // DEBUG LOGS
    console.log('🔍 DEBUG applyQuickAction:');
    console.log('  - Current column:', input.getAttribute('data-column'));
    console.log('  - Previous column:', previousInput ? previousInput.getAttribute('data-column') : 'NONE');
    console.log('  - Reference value:', referenceValue);
    console.log('  - Offset:', offset);
    console.log('  - Input element:', input);
    console.log('  - Note element:', note);
    console.log('  - refOffset element:', refOffset);
    
    if (!referenceValue) {
        alert('Cột trước đó chưa có giá trị!');
        return;
    }
    
    // Tính toán
    const newValue = calculateOffset(referenceValue, offset);
    
    // DEBUG LOGS
    console.log('  - Calculated new value:', newValue);
    console.log('  - Reference date:', new Date(referenceValue).toLocaleString('vi-VN'));
    console.log('  - New date:', new Date(newValue).toLocaleString('vi-VN'));
    
    popupInput.value = newValue;
    input.value = newValue;
    
    // Hiển thị ghi chú BÊN NGOÀI
    console.log('  - Calling showReferenceNote...');
    showReferenceNote(note, refOffset, offset);
    
    // Lưu offset vào data attribute
    console.log('  - Setting data-ref-offset:', offset);
    input.setAttribute('data-ref-offset', offset);
    
    // DEBUG: Verify attribute was set
    const verifyOffset = input.getAttribute('data-ref-offset');
    console.log('  - Verified data-ref-offset:', verifyOffset === offset ? `✓ SET (${verifyOffset})` : `✗ FAILED (expected ${offset}, got ${verifyOffset})`);
    
    // DEBUG: Verify note is visible
    setTimeout(function() {
        const noteDisplay = note ? getComputedStyle(note).display : 'NONE';
        const noteText = refOffset ? refOffset.textContent : 'NO TEXT';
        console.log('  - Note status after show:', {
            display: noteDisplay,
            text: noteText,
            elementExists: !!note
        });
    }, 50);
    
    // Đóng popup
    closePopup(input.closest('.datetime-input-wrapper').querySelector('.datetime-popup'));
    
    // Mark dirty
    markRowDirty(input);
    
    console.log('🔍 DEBUG applyQuickAction - Completed');
}

/**
 * Hiển thị ghi chú tham chiếu
 * @param {HTMLElement} inputOrNote - Input element hoặc note element
 * @param {string} offsetOrRefOffset - Offset string hoặc refOffset element
 * @param {string} offset - Offset string (optional nếu param 1 là input)
 */
function showReferenceNote(inputOrNote, offsetOrRefOffset, offset) {
    console.log('🔍 DEBUG showReferenceNote:');
    console.log('  - Param 1:', inputOrNote);
    console.log('  - Param 2:', offsetOrRefOffset);
    console.log('  - Param 3:', offset);
    
    let note, refOffset, actualOffset;
    
    // Detect calling signature
    if (arguments.length === 2) {
        // Called with (input, offset) - new signature
        const input = inputOrNote;
        actualOffset = offsetOrRefOffset;
        
        const wrapper = input.closest('.datetime-input-wrapper');
        if (!wrapper) {
            console.error('  ❌ No wrapper found for input!');
            return;
        }
        
        note = wrapper.querySelector('.datetime-reference-note');
        if (!note) {
            // Create note element
            note = document.createElement('div');
            note.className = 'datetime-reference-note';
            note.innerHTML = `
                <small class="text-muted">
                    <i class="fas fa-link"></i> 
                    <span class="ref-offset"></span>
                </small>
            `;
            wrapper.appendChild(note);
        }
        
        refOffset = note.querySelector('.ref-offset');
    } else {
        // Called with (note, refOffset, offset) - old signature
        note = inputOrNote;
        refOffset = offsetOrRefOffset;
        actualOffset = offset;
    }
    
    if (!note) {
        console.error('  ❌ Note element is null!');
        return;
    }
    
    if (!refOffset) {
        console.error('  ❌ refOffset element is null!');
        return;
    }
    
    if (!actualOffset) {
        console.error('  ❌ Offset is null or undefined!');
        return;
    }
    
    const offsetText = formatOffset(actualOffset);
    console.log('  - Formatted offset text:', offsetText);
    
    refOffset.textContent = offsetText;
    note.style.display = 'block';
    
    console.log('🔍 DEBUG showReferenceNote - Completed');
}

/**
 * Ẩn ghi chú tham chiếu
 */
function hideReferenceNote(note) {
    if (note) {
        note.style.display = 'none';
    }
}

/**
 * Format offset text (ví dụ: "+3h" → "+ 3 giờ")
 */
function formatOffset(offset) {
    const match = offset.match(/^([+-]?)(\d+)([smhdwMqy])$/);
    if (!match) return offset;
    
    const sign = match[1] === '-' ? '-' : '+';
    const amount = match[2];
    const unit = match[3];
    
    const unitInfo = OFFSET_UNITS[unit];
    if (!unitInfo) return offset;
    
    return `${sign} ${amount} ${unitInfo.name}`;
}

/**
 * Tính toán offset
 */
function calculateOffset(baseValue, offset) {
    if (!baseValue) {
        console.error('❌ calculateOffset: baseValue is empty');
        return null;
    }
    
    // Parse baseValue như local time (không phải UTC)
    // Format: "YYYY-MM-DDTHH:mm"
    const baseDate = parseLocalDateTime(baseValue);
    if (!baseDate || isNaN(baseDate.getTime())) {
        console.error('❌ calculateOffset: Invalid base date:', baseValue);
        return baseValue;
    }
    
    const match = offset.match(/^([+-]?)(\d+)([smhdwMqy])$/);
    if (!match) {
        console.error('❌ calculateOffset: Invalid offset format:', offset);
        return baseValue;
    }
    
    const sign = match[1] === '-' ? -1 : 1;
    const amount = parseInt(match[2]) * sign;
    const unit = match[3];
    
    const unitInfo = OFFSET_UNITS[unit];
    if (!unitInfo) {
        console.error('❌ calculateOffset: Unknown unit:', unit);
        return baseValue;
    }
    
    const ms = amount * unitInfo.ms;
    const newDate = new Date(baseDate.getTime() + ms);
    
    // Format về local datetime string (không dùng toISOString)
    const result = formatLocalDateTime(newDate);
    
    // DEBUG LOGS
    console.log('🔍 DEBUG calculateOffset:');
    console.log('  - Base (local):', baseValue, '→', baseDate.toLocaleString('vi-VN'));
    console.log('  - Offset:', offset, '=', amount, unitInfo.name, '=', ms, 'ms');
    console.log('  - Result (local):', result, '→', newDate.toLocaleString('vi-VN'));
    console.log('  - Calculation:', baseDate.getTime(), '+', ms, '=', newDate.getTime());
    
    return result;
}

/**
 * Parse datetime-local string thành Date object (local time)
 * Format input: "YYYY-MM-DDTHH:mm"
 */
function parseLocalDateTime(dateTimeString) {
    if (!dateTimeString) return null;
    
    // Tách date và time
    const [datePart, timePart] = dateTimeString.split('T');
    if (!datePart || !timePart) return null;
    
    const [year, month, day] = datePart.split('-').map(Number);
    const [hour, minute] = timePart.split(':').map(Number);
    
    // Tạo Date object với local time (không phải UTC)
    return new Date(year, month - 1, day, hour, minute, 0, 0);
}

/**
 * Format Date object thành datetime-local string (local time)
 * Format output: "YYYY-MM-DDTHH:mm"
 */
function formatLocalDateTime(date) {
    if (!date || isNaN(date.getTime())) return '';
    
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hour = String(date.getHours()).padStart(2, '0');
    const minute = String(date.getMinutes()).padStart(2, '0');
    
    return `${year}-${month}-${day}T${hour}:${minute}`;
}

/**
 * Lấy input của cột trước đó
 */
function getPreviousColumnInput(input) {
    const currentColumn = input.getAttribute('data-column');
    if (!currentColumn) return null;
    
    const currentIndex = COLUMN_ORDER.indexOf(currentColumn);
    if (currentIndex <= 0) return null;
    
    const previousColumn = COLUMN_ORDER[currentIndex - 1];
    const row = input.closest('tr');
    const previousInput = row.querySelector(`input[data-column="${previousColumn}"]`);
    
    return previousInput;
}

/**
 * Helper function để ẩn ghi chú (có thể gọi từ nơi khác)
 */
function hideReferenceNote(note) {
    if (note && note.style) {
        note.style.display = 'none';
    }
}

// Export functions
window.DateTimePicker = {
    initializeDateTimePickers: initializeDateTimePickers,
    setupInputEvents: setupInputEvents,
    handleInputClick: handleInputClick,
    createPopupForInput: createPopupForInput,
    openPopup: openPopup,
    closePopup: closePopup,
    applyQuickAction: applyQuickAction,
    showReferenceNote: showReferenceNote,
    hideReferenceNote: hideReferenceNote,
    formatOffset: formatOffset,
    formatLocalDateTime: formatLocalDateTime,
    parseLocalDateTime: parseLocalDateTime
};

console.log('✅ DateTimePicker module loaded');
// Mark đã load
window.DateTimePickerModule = true;
})();