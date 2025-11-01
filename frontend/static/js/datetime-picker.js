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
    const datetimeInputs = document.querySelectorAll('.datetime-input');
    
    datetimeInputs.forEach(function(input) {
        // Tạo popup nếu chưa có
        if (!input.closest('.datetime-input-wrapper')?.querySelector('.datetime-popup')) {
            createPopupForInput(input);
        }
        
        // Setup event listeners
        setupInputEvents(input);
    });
}

/**
 * Setup event listeners cho input
 */
function setupInputEvents(input) {
    // Click vào input → Tự động set Now (nếu rỗng) → Mở popup
    input.addEventListener('click', function(e) {
        e.preventDefault();
        handleInputClick(this);
    });
    
    // Focus → Tự động set Now (nếu rỗng) → Mở popup
    input.addEventListener('focus', function(e) {
        e.preventDefault();
        handleInputClick(this);
    });
}

/**
 * Xử lý khi click vào input
 */
function handleInputClick(input) {
    // Nếu input chưa có giá trị → Tự động set = Now
    if (!input.value || input.value.trim() === '') {
        const now = new Date();
        const nowStr = formatLocalDateTime(now); // Dùng formatLocalDateTime thay vì toISOString
        input.value = nowStr;
    }
    
    openPopup(input);
}

/**
 * Tạo popup cho input
 */
function createPopupForInput(input) {
    const wrapper = input.closest('.datetime-input-wrapper');
    if (!wrapper) {
        // Nếu chưa có wrapper, tạo mới
        const newWrapper = document.createElement('div');
        newWrapper.className = 'datetime-input-wrapper';
        input.parentNode.insertBefore(newWrapper, input);
        newWrapper.appendChild(input);
        return createPopupForInput(input);
    }
    
    // Kiểm tra xem đã có popup chưa
    if (wrapper.querySelector('.datetime-popup')) {
        return;
    }
    
    // Tạo note BÊN NGOÀI (nếu chưa có)
    let note = wrapper.querySelector('.datetime-reference-note');
    if (!note) {
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
                <button class="quick-btn" data-offset="+1M" type="button">+1M</button>
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
    
    // Setup events cho popup
    setupPopupEvents(input, popup, note);
}

/**
 * Setup events cho popup
 */
function setupPopupEvents(input, popup, note) {
    const popupInput = popup.querySelector('.datetime-popup-input');
    const btnClose = popup.querySelector('.btn-close-popup');
    const quickBtns = popup.querySelectorAll('.quick-btn');
    const btnApplyCustom = popup.querySelector('.btn-apply-custom');
    const refOffset = note.querySelector('.ref-offset');
    
    // Popup input change → KHÔNG đóng popup ngay, chỉ sync giá trị
    popupInput.addEventListener('input', function() {
        // Sync giá trị khi đang nhập (không đóng popup)
        input.value = this.value;
    });
    
    // Popup input blur hoặc Enter → Đóng popup và xử lý offset
    popupInput.addEventListener('blur', function() {
        handlePopupInputChange(popupInput, input, note);
    });
    
    popupInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            handlePopupInputChange(popupInput, input, note);
            closePopup(popup);
            markRowDirty(input);
        } else if (e.key === 'Escape') {
            e.preventDefault();
            closePopup(popup);
        }
    });
    
    // Helper function để xử lý khi popup input thay đổi
    function handlePopupInputChange(popupInput, input, note) {
        console.log('🔍 DEBUG popupInput change:');
        console.log('  - New value:', popupInput.value);
        console.log('  - Current data-ref-offset:', input.getAttribute('data-ref-offset'));
        
        input.value = popupInput.value;
        
        // Kiểm tra xem có phải user thay đổi thủ công không
        const currentOffset = input.getAttribute('data-ref-offset');
        if (currentOffset) {
            // Tính lại giá trị từ offset để so sánh
            const previousInput = getPreviousColumnInput(input);
            if (previousInput && previousInput.value) {
                const calculatedValue = calculateOffset(previousInput.value, currentOffset);
                console.log('  - Calculated value from offset:', calculatedValue);
                console.log('  - User value:', popupInput.value);
                
                if (popupInput.value !== calculatedValue) {
                    console.log('  ⚠️ User changed value manually, removing offset');
                    hideReferenceNote(note);
                    input.removeAttribute('data-ref-offset');
                } else {
                    console.log('  ✓ Value matches offset, keeping note');
                }
            }
        } else {
            console.log('  - No offset, hiding note');
            hideReferenceNote(note);
        }
    }
    
    // Quick buttons
    quickBtns.forEach(function(btn) {
        btn.addEventListener('click', function() {
            const offset = this.getAttribute('data-offset');
            applyQuickAction(input, popupInput, offset, note, refOffset);
        });
    });
    
    // Custom apply
    btnApplyCustom.addEventListener('click', function() {
        const amount = popup.querySelector('.custom-amount').value;
        const unit = popup.querySelector('.custom-unit').value;
        if (amount && amount > 0) {
            const offset = `+${amount}${unit}`;
            applyQuickAction(input, popupInput, offset, note, refOffset);
        }
    });
    
    // Close button
    btnClose.addEventListener('click', function() {
        closePopup(popup);
    });
}

/**
 * Mở popup
 */
function openPopup(input) {
    const popup = input.closest('.datetime-input-wrapper')?.querySelector('.datetime-popup');
    if (!popup) return;
    
    // Close other popups
    document.querySelectorAll('.datetime-popup').forEach(function(p) {
        if (p !== popup) p.style.display = 'none';
    });
    
    // Tính toán vị trí popup dựa trên input position
    const inputRect = input.getBoundingClientRect();
    const viewportHeight = window.innerHeight;
    const popupHeight = 400; // Estimated popup height
    
    // Kiểm tra nếu popup sẽ bị che dưới màn hình
    let top = inputRect.bottom + 8;
    if (top + popupHeight > viewportHeight) {
        // Hiển thị phía trên input nếu không đủ chỗ dưới
        top = inputRect.top - popupHeight - 8;
        if (top < 0) {
            // Nếu vẫn không đủ chỗ, hiển thị ở giữa màn hình
            top = (viewportHeight - popupHeight) / 2;
        }
    }
    
    // Set position
    popup.style.position = 'fixed';
    popup.style.top = top + 'px';
    popup.style.left = inputRect.left + 'px';
    popup.style.zIndex = '99999';
    popup.style.display = 'block';
    
    // Sync popup input với main input
    const popupInput = popup.querySelector('.datetime-popup-input');
    if (!input.value || input.value.trim() === '') {
        const now = new Date();
        const nowStr = formatLocalDateTime(now); // Dùng formatLocalDateTime
        input.value = nowStr;
        popupInput.value = nowStr;
    } else {
        popupInput.value = input.value || '';
    }
    
    // Create backdrop
    if (!document.querySelector('.datetime-popup-backdrop')) {
        const backdrop = document.createElement('div');
        backdrop.className = 'datetime-popup-backdrop';
        backdrop.style.zIndex = '99998';
        backdrop.addEventListener('click', function(e) {
            // CHỈ đóng popup nếu click vào backdrop, không phải popup
            if (e.target === backdrop) {
                closePopup(popup);
            }
        });
        document.body.appendChild(backdrop);
    }
    
    // Prevent popup click từ đóng popup
    popup.addEventListener('click', function(e) {
        e.stopPropagation(); // Ngăn event propagate lên backdrop
    });
}

/**
 * Đóng popup
 */
function closePopup(popup) {
    popup.style.display = 'none';
    const backdrop = document.querySelector('.datetime-popup-backdrop');
    if (backdrop) backdrop.remove();
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
 */
function showReferenceNote(note, refOffset, offset) {
    console.log('🔍 DEBUG showReferenceNote:');
    console.log('  - Note element:', note);
    console.log('  - refOffset element:', refOffset);
    console.log('  - Offset:', offset);
    
    if (!note) {
        console.error('  ❌ Note element is null!');
        return;
    }
    
    if (!refOffset) {
        console.error('  ❌ refOffset element is null!');
        return;
    }
    
    const offsetText = formatOffset(offset);
    console.log('  - Formatted offset text:', offsetText);
    
    refOffset.textContent = offsetText;
    note.style.display = 'block';
    
    // Verify
    setTimeout(function() {
        const actualDisplay = getComputedStyle(note).display;
        const actualText = refOffset.textContent;
        console.log('  - Verification:', {
            display: actualDisplay,
            text: actualText,
            matches: actualDisplay === 'block' && actualText === offsetText
        });
    }, 10);
    
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
if (typeof window !== 'undefined') {
    window.DateTimePicker = {
        initialize: initializeDateTimePickers,
        createPopupForInput: createPopupForInput,
        setupInputEvents: setupInputEvents,
        hideReferenceNote: hideReferenceNote,
        showReferenceNote: showReferenceNote,  // ✅ THÊM DÒNG NÀY
        formatOffset: formatOffset,
        formatLocalDateTime: formatLocalDateTime,
        parseLocalDateTime: parseLocalDateTime
    };
}
// Mark đã load
window.DateTimePickerModule = true;
})();