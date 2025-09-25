// 主要的JavaScript功能

// 全局变量
let classroomTimer = null;
let classroomStartTime = null;
let pptCanvas = null;
let pptCtx = null;
let isDrawing = false;
let currentTool = 'pen';
let currentSlideImage = null;

// 初始化页面
document.addEventListener('DOMContentLoaded', function() {
    console.log('课堂演示系统已加载');
    
    // 初始化PPT画板
    initializePPTCanvas();
    
    // 如果有课堂数据，初始化界面
    if (typeof classroomData !== 'undefined') {
        initializeClassroom();
    }
});

// 初始化PPT画板
function initializePPTCanvas() {
    pptCanvas = document.getElementById('pptCanvas');
    if (!pptCanvas) return;
    
    pptCtx = pptCanvas.getContext('2d');
    
    // 设置默认样式
    pptCtx.lineWidth = 3;
    pptCtx.lineCap = 'round';
    pptCtx.lineJoin = 'round';
    pptCtx.strokeStyle = '#000000';
    
    // 添加绘图事件
    pptCanvas.addEventListener('mousedown', startDrawing);
    pptCanvas.addEventListener('mousemove', draw);
    pptCanvas.addEventListener('mouseup', stopDrawing);
    pptCanvas.addEventListener('mouseout', stopDrawing);
    
    // 添加触摸事件支持
    pptCanvas.addEventListener('touchstart', handleTouchStart, {passive: false});
    pptCanvas.addEventListener('touchmove', handleTouchMove, {passive: false});
    pptCanvas.addEventListener('touchend', handleTouchEnd, {passive: false});
}

// 开始绘图
function startDrawing(e) {
    isDrawing = true;
    const rect = pptCanvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    pptCtx.beginPath();
    pptCtx.moveTo(x, y);
    draw(e);
}

// 绘图
function draw(e) {
    if (!isDrawing) return;
    
    const rect = pptCanvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    pptCtx.globalCompositeOperation = currentTool === 'eraser' ? 'destination-out' : 'source-over';
    pptCtx.strokeStyle = currentTool === 'eraser' ? 'transparent' : document.getElementById('colorPicker')?.value || '#000000';
    
    pptCtx.lineTo(x, y);
    pptCtx.stroke();
    pptCtx.beginPath();
    pptCtx.moveTo(x, y);
}

// 停止绘图
function stopDrawing() {
    if (isDrawing) {
        isDrawing = false;
        pptCtx.beginPath();
    }
}

// 处理触摸事件
function handleTouchStart(e) {
    e.preventDefault();
    const touch = e.touches[0];
    const mouseEvent = new MouseEvent('mousedown', {
        clientX: touch.clientX,
        clientY: touch.clientY
    });
    pptCanvas.dispatchEvent(mouseEvent);
}

function handleTouchMove(e) {
    e.preventDefault();
    const touch = e.touches[0];
    const mouseEvent = new MouseEvent('mousemove', {
        clientX: touch.clientX,
        clientY: touch.clientY
    });
    pptCanvas.dispatchEvent(mouseEvent);
}

function handleTouchEnd(e) {
    e.preventDefault();
    const mouseEvent = new MouseEvent('mouseup', {});
    pptCanvas.dispatchEvent(mouseEvent);
}

// 切换工具
function changeTool(tool) {
    currentTool = tool;
    
    if (tool === 'pen') {
        pptCanvas.style.cursor = 'crosshair';
    } else if (tool === 'eraser') {
        pptCanvas.style.cursor = 'grab';
    }
}

// 清除PPT画板
function clearPPTCanvas() {
    if (confirm('确定要清除所有绘图内容吗？')) {
        pptCtx.clearRect(0, 0, pptCanvas.width, pptCanvas.height);
        // 重新绘制当前幻灯片
        if (currentSlideImage) {
            loadSlideImage(currentSlideImage);
        }
        showNotification('画板已清除', 'success');
    }
}

// 加载幻灯片图片到画板
function loadSlideImage(img) {
    if (!pptCanvas || !pptCtx) return;
    
    currentSlideImage = img;
    
    // 清除画布
    pptCtx.clearRect(0, 0, pptCanvas.width, pptCanvas.height);
    
    // 计算缩放比例以适应画布
    const scaleX = pptCanvas.width / img.width;
    const scaleY = pptCanvas.height / img.height;
    const scale = Math.min(scaleX, scaleY);
    
    const scaledWidth = img.width * scale;
    const scaledHeight = img.height * scale;
    const x = (pptCanvas.width - scaledWidth) / 2;
    const y = (pptCanvas.height - scaledHeight) / 2;
    
    // 绘制图片
    pptCtx.drawImage(img, x, y, scaledWidth, scaledHeight);
}

// 初始化课堂
function initializeClassroom() {
    // 设置问题文本动画
    const questionElement = document.getElementById('questionText');
    if (questionElement) {
        questionElement.style.animation = 'slideInDown 0.8s ease-out';
    }
    
    // 初始化白板
    initializeWhiteboard();
    
    // 初始化学生管理
    initializeStudentManagement();
}

// 初始化白板
function initializeWhiteboard() {
    const canvas = document.getElementById('whiteboard');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    // 设置默认样式
    ctx.lineWidth = 2;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    
    // 添加触摸事件支持（移动端）
    canvas.addEventListener('touchstart', handleTouchStart, {passive: false});
    canvas.addEventListener('touchmove', handleTouchMove, {passive: false});
    canvas.addEventListener('touchend', handleTouchEnd, {passive: false});
    
    // 添加键盘快捷键
    document.addEventListener('keydown', handleKeyboardShortcuts);
}

// 处理触摸事件
function handleTouchStart(e) {
    e.preventDefault();
    const touch = e.touches[0];
    const mouseEvent = new MouseEvent('mousedown', {
        clientX: touch.clientX,
        clientY: touch.clientY
    });
    canvas.dispatchEvent(mouseEvent);
}

function handleTouchMove(e) {
    e.preventDefault();
    const touch = e.touches[0];
    const mouseEvent = new MouseEvent('mousemove', {
        clientX: touch.clientX,
        clientY: touch.clientY
    });
    canvas.dispatchEvent(mouseEvent);
}

function handleTouchEnd(e) {
    e.preventDefault();
    const mouseEvent = new MouseEvent('mouseup', {});
    canvas.dispatchEvent(mouseEvent);
}

// 键盘快捷键
function handleKeyboardShortcuts(e) {
    if (e.ctrlKey || e.metaKey) {
        switch(e.key) {
            case 's':
                e.preventDefault();
                exportData();
                break;
            case 'z':
                e.preventDefault();
                // 可以添加撤销功能
                break;
        }
    }
    
    // 工具切换快捷键
    switch(e.key) {
        case 'p':
            changeTool('pen');
            break;
        case 'e':
            changeTool('eraser');
            break;
        case 'c':
            clearCanvas();
            break;
    }
}

// 初始化学生管理
function initializeStudentManagement() {
    // 添加学生输入框回车事件
    const studentNameInput = document.getElementById('studentName');
    if (studentNameInput) {
        studentNameInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                addStudent();
            }
        });
    }
}

// 工具切换功能
function changeTool(tool) {
    currentTool = tool;
    
    // 更新按钮状态
    document.querySelectorAll('.whiteboard-tools .btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    if (tool === 'pen') {
        document.querySelector('.whiteboard-tools .btn:first-child').classList.add('active');
        canvas.style.cursor = 'crosshair';
    } else if (tool === 'eraser') {
        document.querySelector('.whiteboard-tools .btn:nth-child(2)').classList.add('active');
        canvas.style.cursor = 'grab';
    }
}

// 清除画布
function clearCanvas() {
    if (confirm('确定要清除所有内容吗？')) {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        showNotification('画布已清除', 'success');
    }
}

// 显示通知
function showNotification(message, type = 'info') {
    // 创建通知元素
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // 自动移除通知
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 3000);
}

// 开始课堂计时器
function startClassroomTimer() {
    classroomStartTime = Date.now();
    
    classroomTimer = setInterval(() => {
        const elapsed = Date.now() - classroomStartTime;
        const minutes = Math.floor(elapsed / 60000);
        const seconds = Math.floor((elapsed % 60000) / 1000);
        
        // 更新计时器显示（如果需要的话）
        const timerElement = document.getElementById('classroomTimer');
        if (timerElement) {
            timerElement.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }
    }, 1000);
}

// 停止课堂计时器
function stopClassroomTimer() {
    if (classroomTimer) {
        clearInterval(classroomTimer);
        classroomTimer = null;
    }
}

// 获取课堂数据
function getClassroomData() {
    return fetch('/get_classroom_data')
        .then(response => response.json())
        .then(data => {
            classroomData = data;
            return data;
        })
        .catch(error => {
            console.error('获取课堂数据失败:', error);
            showNotification('获取课堂数据失败', 'danger');
        });
}

// 导出数据
function exportData() {
    showNotification('正在导出数据...', 'info');
    
    fetch('/export_data')
        .then(response => response.json())
        .then(data => {
            const blob = new Blob([JSON.stringify(data, null, 2)], {type: 'application/json'});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `classroom_data_${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            showNotification('数据导出成功！', 'success');
        })
        .catch(error => {
            console.error('导出数据失败:', error);
            showNotification('导出数据失败', 'danger');
        });
}

// 添加学生验证
function validateStudentName(name) {
    if (!name || name.trim().length === 0) {
        showNotification('请输入学生姓名', 'warning');
        return false;
    }
    
    if (name.length > 20) {
        showNotification('学生姓名不能超过20个字符', 'warning');
        return false;
    }
    
    // 检查是否已存在
    if (classroomData.students && classroomData.students[name]) {
        showNotification('该学生已存在', 'warning');
        return false;
    }
    
    return true;
}

// 答案验证
function validateAnswer(answer) {
    if (!answer || answer.trim().length === 0) {
        showNotification('请输入答案', 'warning');
        return false;
    }
    
    return true;
}

// 页面卸载时的清理
window.addEventListener('beforeunload', function() {
    stopClassroomTimer();
});

// 错误处理
window.addEventListener('error', function(e) {
    console.error('页面错误:', e.error);
    showNotification('发生了一个错误，请刷新页面重试', 'danger');
});

// 网络状态检测
window.addEventListener('online', function() {
    showNotification('网络连接已恢复', 'success');
});

window.addEventListener('offline', function() {
    showNotification('网络连接已断开', 'warning');
});

