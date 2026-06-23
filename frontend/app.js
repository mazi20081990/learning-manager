/**
 * 学习管家 - 前端主应用
 * 纯原生 JavaScript SPA，无框架依赖
 */

// ========== 配置 ==========
const API_BASE = ''; // 同域部署，使用相对路径
const PAGES = ['dashboard', 'plans', 'calendar', 'profile'];

// ========== 状态 ==========
let currentUser = null;
let currentLearner = null;
let learnersCache = [];
let currentPlan = null;
let currentContent = null;
let currentPage = 'dashboard';
let plansCache = [];
let currentExam = null;

// ========== API 客户端 ==========
const api = {
  async request(url, options = {}) {
    const defaultOptions = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      credentials: 'include'
    };

    try {
      showLoading(true);
      const response = await fetch(`${API_BASE}${url}`, { ...defaultOptions, ...options });
      showLoading(false);

      if (response.status === 401) {
        // 未登录，跳转到登录页
        showPage('login-page');
        return null;
      }

      const data = await response.json().catch(() => null);

      if (!response.ok) {
        const error = data?.error || `请求失败: ${response.status}`;
        showToast(error, 'error');
        return null;
      }

      return data;
    } catch (error) {
      showLoading(false);
      showToast('网络错误，请检查连接', 'error');
      console.error('API Error:', error);
      return null;
    }
  },

  get(url) { return this.request(url, { method: 'GET' }); },
  post(url, data) { return this.request(url, { method: 'POST', body: JSON.stringify(data) }); },
  put(url, data) { return this.request(url, { method: 'PUT', body: JSON.stringify(data) }); },
  delete(url) { return this.request(url, { method: 'DELETE' }); }
};

// ========== 工具函数 ==========
function $(selector) { return document.querySelector(selector); }
function $$(selector) { return document.querySelectorAll(selector); }

function showPage(pageId) {
  $$('.page').forEach(p => p.classList.add('hidden'));
  $(`#${pageId}`)?.classList.remove('hidden');
}

function showContentPage(pageName) {
  $$('.content-page').forEach(p => p.classList.add('hidden'));
  $(`#${pageName}-page`)?.classList.remove('hidden');
  currentPage = pageName;

  // 更新导航高亮
  $$('.nav a').forEach(a => {
    a.classList.toggle('active', a.dataset.page === pageName);
  });

  // 更新底部导航
  $$('.bottom-nav-item').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.page === pageName);
  });
}

function showModal(modalId) {
  $(`#${modalId}`)?.classList.remove('hidden');
}

function hideModal(modalId) {
  $(`#${modalId}`)?.classList.add('hidden');
}

function showLoading(show) {
  let overlay = $('.loading-overlay');
  if (show) {
    if (!overlay) {
      overlay = document.createElement('div');
      overlay.className = 'loading-overlay';
      overlay.innerHTML = '<div class="spinner"></div>';
      document.body.appendChild(overlay);
    }
    overlay.classList.remove('hidden');
  } else {
    overlay?.classList.add('hidden');
  }
}

function showToast(message, type = 'info') {
  let container = $('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

function formatDate(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
}

// ========== 认证模块 ==========
async function initAuth() {
  // 检查是否已登录
  const data = await api.get('/api/auth/me');
  if (data?.user) {
    currentUser = data.user;
    // 加载学习者信息
    await loadLearners();
    showMainApp();
  } else {
    showPage('login-page');
  }
}

async function login(username, password) {
  const data = await api.post('/api/auth/login', { username, password });
  if (data?.user) {
    currentUser = data.user;
    showMainApp();
    showToast('登录成功', 'success');
  }
}

async function logout() {
  await api.post('/api/auth/logout');
  currentUser = null;
  showPage('login-page');
  showToast('已退出登录', 'info');
}

function showMainApp() {
  showPage('main-page');
  $('#user-name').textContent = currentUser.nickname || currentUser.username;
  updateLearnerDisplay();
  showContentPage('dashboard');
  loadDashboard();
}

// ========== 学习者管理 ==========
async function loadLearners() {
  const data = await api.get('/api/learners');
  if (data?.learners) {
    learnersCache = data.learners;
    // 获取当前选中的学习者
    const currentData = await api.get('/api/learners/current');
    if (currentData?.learner) {
      currentLearner = currentData.learner;
    } else if (learnersCache.length > 0) {
      currentLearner = learnersCache[0];
    }
    updateLearnerDisplay();
    updateLearnerSelects();
  }
}

function updateLearnerDisplay() {
  const nameEl = $('#current-learner-name');
  if (currentLearner) {
    nameEl.textContent = `👤 ${currentLearner.name}`;
    nameEl.title = `当前学习者：${currentLearner.name}`;
  } else {
    nameEl.textContent = '👤';
    nameEl.title = '点击选择学习者';
  }
}

function updateLearnerSelects() {
  // 更新顶部切换下拉框
  const select = $('#learner-select');
  select.innerHTML = learnersCache.map(l =>
    `<option value="${l.id}" ${l.id === currentLearner?.id ? 'selected' : ''}>${l.name}</option>`
  ).join('');

  // 更新创建计划弹窗中的学习者选择
  const planLearner = $('#plan-learner');
  if (planLearner) {
    planLearner.innerHTML = '<option value="">-- 选择学习者 --</option>' +
      learnersCache.map(l =>
        `<option value="${l.id}" ${l.id === currentLearner?.id ? 'selected' : ''}>${l.name}</option>`
      ).join('');
  }
}

async function switchLearner(learnerId) {
  const data = await api.post(`/api/learners/switch/${learnerId}`);
  if (data?.learner) {
    currentLearner = data.learner;
    updateLearnerDisplay();
    updateLearnerSelects();
    showToast(`已切换到：${currentLearner.name}`, 'success');
    // 刷新当前页面数据
    if (currentPage === 'plans') loadPlans();
    if (currentPage === 'dashboard') loadDashboard();
  }
}

async function renderLearnersList() {
  const container = $('#learners-list');
  if (!container) return;

  if (learnersCache.length === 0) {
    container.innerHTML = '<p class="empty-text">暂无学习者，请添加</p>';
    return;
  }

  container.innerHTML = learnersCache.map(learner => `
    <div class="learner-card ${learner.id === currentLearner?.id ? 'active' : ''}" data-id="${learner.id}">
      <div class="learner-avatar">${learner.avatar || '👤'}</div>
      <div class="learner-info">
        <div class="learner-name">${escapeHtml(learner.name)}
          ${learner.is_default ? '<span class="default-badge">默认</span>' : ''}
        </div>
        <div class="learner-meta">
          ${learner.age ? `${learner.age}岁 · ` : ''}
          ${learner.grade ? escapeHtml(learner.grade) : ''}
          ${learner.relation ? ` · ${getRelationText(learner.relation)}` : ''}
        </div>
      </div>
      <div class="learner-actions">
        ${learner.id !== currentLearner?.id ?
          `<button class="btn btn-sm" onclick="switchLearner(${learner.id})">切换</button>` :
          '<span class="current-badge">当前</span>'
        }
        ${!learner.is_default ?
          `<button class="btn btn-sm btn-secondary" onclick="setDefaultLearner(${learner.id})">设为默认</button>` : ''
        }
        <button class="btn btn-sm btn-danger" onclick="deleteLearner(${learner.id})">删除</button>
      </div>
    </div>
  `).join('');
}

function getRelationText(relation) {
  const map = {
    'self': '自己',
    'child': '孩子',
    'spouse': '配偶',
    'parent': '父母',
    'other': '其他'
  };
  return map[relation] || relation;
}

async function addLearner(e) {
  e.preventDefault();
  const data = {
    name: $('#learner-name').value.trim(),
    age: parseInt($('#learner-age').value) || null,
    grade: $('#learner-grade').value.trim() || null,
    relation: $('#learner-relation').value,
    learning_style: $('#learner-style').value
  };

  if (!data.name) {
    showToast('请输入姓名', 'warning');
    return;
  }

  const result = await api.post('/api/learners', data);
  if (result?.learner) {
    hideModal('add-learner-modal');
    $('#add-learner-form').reset();
    showToast('学习者添加成功', 'success');
    await loadLearners();
    renderLearnersList();
  }
}

async function setDefaultLearner(learnerId) {
  const data = await api.post(`/api/learners/${learnerId}/default`);
  if (data) {
    showToast('默认学习者已更新', 'success');
    await loadLearners();
    renderLearnersList();
  }
}

async function deleteLearner(learnerId) {
  if (!confirm('确定要删除这个学习者吗？相关的学习计划将保留但不再关联。')) return;
  const data = await api.delete(`/api/learners/${learnerId}`);
  if (data) {
    showToast('学习者已删除', 'success');
    await loadLearners();
    renderLearnersList();
  }
}

// ========== 仪表盘 ==========
async function loadDashboard() {
  const data = await api.get('/api/plans');
  if (!data) return;

  plansCache = data.plans || [];

  const active = plansCache.filter(p => p.status === 'active');
  const completed = plansCache.filter(p => p.status === 'completed');

  $('#active-plans-count').textContent = active.length;
  $('#completed-plans-count').textContent = completed.length;
  $('#today-learning').textContent = active.length > 0 ? '1' : '0';
  $('#streak-days').textContent = '0'; // TODO: 从后端获取

  // 最近计划
  const recentList = $('#recent-plans-list');
  if (plansCache.length === 0) {
    recentList.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">📚</div>
        <p>还没有学习计划</p>
        <button class="btn btn-primary" onclick="showModal('create-plan-modal')">创建第一个计划</button>
      </div>
    `;
  } else {
    recentList.innerHTML = plansCache.slice(0, 3).map(plan => renderPlanCard(plan)).join('');
  }
}

// ========== 计划管理 ==========
function renderPlanCard(plan) {
  const statusMap = {
    active: { text: '进行中', class: 'active' },
    paused: { text: '已暂停', class: 'paused' },
    completed: { text: '已完成', class: 'completed' },
    archived: { text: '已归档', class: 'archived' }
  };
  const s = statusMap[plan.status] || statusMap.active;

  return `
    <div class="plan-card" onclick="viewPlan(${plan.id})">
      <div class="plan-card-header">
        <div>
          <div class="plan-card-title">${escapeHtml(plan.title)}</div>
          <div class="plan-card-topic">${escapeHtml(plan.topic || '')}</div>
        </div>
        <span class="plan-status ${s.class}">${s.text}</span>
      </div>
      <div class="plan-progress">
        <div class="plan-progress-bar">
          <div class="plan-progress-fill" style="width: ${plan.progress || 0}%"></div>
        </div>
        <div class="plan-progress-text">进度: ${Math.round(plan.progress || 0)}%</div>
      </div>
    </div>
  `;
}

async function loadPlans() {
  // 如果有当前学习者，只显示该学习者的计划
  const url = currentLearner ? `/api/plans?learner_id=${currentLearner.id}` : '/api/plans';
  const data = await api.get(url);
  if (!data) return;

  plansCache = data.plans || [];
  const list = $('#plans-list');
  if (!list) return; // 页面可能不在plans页面

  if (plansCache.length === 0) {
    list.innerHTML = `
      <div class="empty-state">
        <div class="empty-state-icon">📚</div>
        <p>${currentLearner ? `${currentLearner.name}还没有学习计划` : '还没有学习计划'}</p>
        <button class="btn btn-primary" onclick="showModal('create-plan-modal')">创建计划</button>
      </div>
    `;
  } else {
    list.innerHTML = plansCache.map(plan => renderPlanCard(plan)).join('');
  }
}

async function createPlan(e) {
  e.preventDefault();
  const topic = $('#plan-topic').value.trim();
  const daysInput = $('#plan-days').value.trim();
  const days = parseInt(daysInput);
  const mode = $('#plan-mode').value;
  const description = $('#plan-description').value.trim();
  const learnerId = $('#plan-learner').value;

  if (!topic) {
    showToast('请填写学习主题', 'warning');
    return;
  }

  if (!daysInput || isNaN(days) || days < 1) {
    showToast('请填写有效的学习天数（至少1天）', 'warning');
    return;
  }

  if (days > 365) {
    showToast('学习天数不能超过365天', 'warning');
    return;
  }

  const payload = { topic, days, mode, description };
  if (learnerId) {
    payload.learner_id = parseInt(learnerId);
  }

  const data = await api.post('/api/plans', payload);
  if (data?.plan) {
    hideModal('create-plan-modal');
    $('#create-plan-form').reset();
    showToast('计划创建成功！正在预生成所有学习内容...', 'success');
    showContentPage('plans');
    loadPlans();
  }
}

async function viewPlan(planId) {
  const data = await api.get(`/api/plans/${planId}`);
  if (!data) return;

  currentPlan = data;

  // 构建计划详情视图
  const plan = data.plan;
  const items = data.items || [];

  let html = `
    <div class="plan-detail-header">
      <h2>${escapeHtml(plan.title)}</h2>
      <div class="plan-detail-meta">
        <span>主题: ${escapeHtml(plan.topic || '')}</span>
        <span>天数: ${plan.total_days}天</span>
        <span>模式: ${plan.mode === 'student' ? '学生模式' : '工作模式'}</span>
        <span>进度: ${Math.round(plan.progress || 0)}%</span>
      </div>
      <div class="plan-card-actions">
        <button class="btn btn-primary btn-sm" onclick="showModal('create-plan-modal')">编辑</button>
        ${plan.status === 'active'
          ? `<button class="btn btn-secondary btn-sm" onclick="pausePlan(${plan.id})">暂停</button>`
          : `<button class="btn btn-success btn-sm" onclick="resumePlan(${plan.id})">恢复</button>`
        }
        <button class="btn btn-danger btn-sm" onclick="deletePlan(${plan.id})">删除</button>
      </div>
    </div>
    <div class="plan-items-list">
  `;

  items.forEach((item, idx) => {
    const isCompleted = item.status === 'completed';
    const isCurrent = !isCompleted && (idx === 0 || items[idx-1]?.status === 'completed');
    html += `
      <div class="plan-item ${isCompleted ? 'completed' : ''} ${isCurrent ? 'current' : ''}">
        <div class="plan-item-left" onclick="viewItemContent(${plan.id}, ${item.id})">
          <div class="plan-item-number">${isCompleted ? '✓' : item.day_number}</div>
          <div class="plan-item-info">
            <div class="plan-item-title">${escapeHtml(item.title)}</div>
            <div class="plan-item-desc">${escapeHtml(item.description || '')}</div>
          </div>
          <span class="plan-item-status ${item.status}">
            ${isCompleted ? '已完成' : '待学习'}
          </span>
        </div>
        <div class="plan-item-actions">
          <button class="btn btn-sm btn-primary" onclick="event.stopPropagation(); startExam(${plan.id}, ${item.id})">考试</button>
        </div>
      </div>
    `;
  });

  html += '</div>';

  // 替换plans页面内容
  $('#plans-page').innerHTML = `
    <div class="plans-container">
      <div class="plans-header">
        <button class="btn btn-secondary btn-sm" onclick="backToPlans()">← 返回列表</button>
      </div>
      ${html}
    </div>
  `;
}

function backToPlans() {
  $('#plans-page').innerHTML = `
    <div class="plans-container">
      <div class="plans-header">
        <h2>学习计划</h2>
        <button id="new-plan-btn" class="btn btn-primary">新建计划</button>
      </div>
      <div id="plans-list" class="plans-grid"></div>
    </div>
  `;
  $('#new-plan-btn').addEventListener('click', () => showModal('create-plan-modal'));
  loadPlans();
}

async function pausePlan(planId) {
  const data = await api.post(`/api/plans/${planId}/pause`);
  if (data) {
    showToast('计划已暂停', 'info');
    viewPlan(planId);
  }
}

async function resumePlan(planId) {
  const data = await api.post(`/api/plans/${planId}/resume`);
  if (data) {
    showToast('计划已恢复', 'success');
    viewPlan(planId);
  }
}

async function deletePlan(planId) {
  if (!confirm('确定要删除这个学习计划吗？此操作不可恢复。')) return;
  const data = await api.delete(`/api/plans/${planId}`);
  if (data) {
    showToast('计划已删除', 'success');
    backToPlans();
    loadDashboard();
  }
}

// ========== 学习内容 ==========
async function viewItemContent(planId, itemId) {
  // 先检查是否已有内容
  let data = await api.get(`/api/content/item/${itemId}`);

  // 如果没有内容，先生成
  if (!data?.content) {
    showToast('正在生成学习内容，请稍候...', 'info');
    data = await api.post('/api/content/generate', { plan_id: planId, item_id: itemId });
    if (!data?.content) {
      showToast('内容生成失败，请重试', 'error');
      return;
    }
  }

  currentContent = data.content;
  renderLearningPage(data.content, itemId);
}

function renderLearningPage(content, itemId) {
  $('#learning-title').textContent = content.title || '学习内容';
  $('#content-html').innerHTML = content.content_html || '<p>内容加载中...</p>';

  // 解析标签/要点
  let keyPoints = [];
  try {
    keyPoints = JSON.parse(content.tags || '[]');
  } catch (e) { keyPoints = []; }

  // 添加要点
  if (keyPoints.length > 0) {
    const kpHtml = `
      <div class="key-points">
        <h3>核心要点</h3>
        <ul>${keyPoints.map(p => `<li>${escapeHtml(p)}</li>`).join('')}</ul>
      </div>
    `;
    $('#content-html').insertAdjacentHTML('beforeend', kpHtml);
  }

  // 解析图片
  let images = [];
  try {
    images = JSON.parse(content.images || '[]');
  } catch (e) { images = []; }

  // 添加图片
  if (images.length > 0) {
    const imgHtml = `
      <div class="content-images">
        ${images.map(img => `<img src="${img}" alt="" loading="lazy">`).join('')}
      </div>
    `;
    $('#content-html').insertAdjacentHTML('beforeend', imgHtml);
  }

  // 解析参考资料
  let references = [];
  try {
    references = JSON.parse(content.references || content.refs || '[]');
  } catch (e) { references = []; }

  // 添加参考资料
  if (references.length > 0) {
    const refHtml = `
      <div class="references-section">
        <h3>参考资料</h3>
        ${references.map(r => `
          <div class="reference-item">
            <span>📎</span>
            <a href="${r.url || r.link || '#' }" target="_blank">${escapeHtml(r.title || r.name || '参考链接')}</a>
          </div>
        `).join('')}
      </div>
    `;
    $('#content-html').insertAdjacentHTML('beforeend', refHtml);
  }

  // 清空问答历史
  $('#question-history').innerHTML = '';

  // 绑定按钮事件
  $('#master-btn').onclick = () => completeItem(itemId);
  $('#retry-btn').onclick = () => regenerateContent(content.id);

  // 更新 URL hash
  window.location.hash = `#/learning/${itemId}`;

  showPage('learning-page');
}

async function completeItem(itemId) {
  const mastery = confirm('您是否已掌握此内容？\n\n点击"确定"表示已掌握，将继续下一个主题。\n点击"取消"表示未掌握，将重新生成内容。')
    ? 3 : 0;

  const data = await api.post(`/api/plans/items/${itemId}/complete`, { mastery_level: mastery });
  if (data) {
    if (mastery > 0) {
      showToast('恭喜！已掌握此内容', 'success');
      if (currentPlan?.plan?.id) {
        window.location.hash = `#/plan/${currentPlan.plan.id}`;
      } else {
        window.location.hash = '#/plans';
      }
    } else {
      showToast('将重新生成学习内容', 'info');
      regenerateContent(currentContent?.id);
    }
  }
}

async function regenerateContent(contentId) {
  showToast('正在重新生成内容...', 'info');
  const data = await api.post(`/api/content/${contentId}/regenerate`);
  if (data?.content) {
    currentContent = data.content;
    renderLearningPage(data.content, data.content.item_id);
    showToast('内容已重新生成', 'success');
  }
}

async function askQuestion() {
  const question = $('#question-input').value.trim();
  if (!question) {
    showToast('请输入问题', 'warning');
    return;
  }

  if (!currentContent?.id) {
    showToast('请先加载学习内容', 'warning');
    return;
  }

  // 添加用户问题到历史
  const history = $('#question-history');
  const qaItem = document.createElement('div');
  qaItem.className = 'qa-item';
  qaItem.innerHTML = `
    <div class="qa-question">Q: ${escapeHtml(question)}</div>
    <div class="qa-answer">思考中...</div>
  `;
  history.appendChild(qaItem);
  history.scrollTop = history.scrollHeight;

  $('#question-input').value = '';

  const data = await api.post(`/api/content/${currentContent.id}/question`, { question });
  if (data?.answer) {
    qaItem.querySelector('.qa-answer').innerHTML = `A: ${escapeHtml(data.answer)}`;
    history.scrollTop = history.scrollHeight;
  } else {
    qaItem.querySelector('.qa-answer').textContent = 'A: 抱歉，无法回答此问题';
  }
}

// ========== 日历 ==========
let currentCalendarDate = new Date();

function loadCalendar() {
  const year = currentCalendarDate.getFullYear();
  const month = currentCalendarDate.getMonth();

  $('#current-month').textContent = `${year}年${month + 1}月`;

  const firstDay = new Date(year, month, 1);
  const lastDay = new Date(year, month + 1, 0);
  const startDayOfWeek = firstDay.getDay();
  const daysInMonth = lastDay.getDate();

  // 上月天数
  const prevMonthLastDay = new Date(year, month, 0).getDate();

  let html = '';

  // 上月日期
  for (let i = startDayOfWeek - 1; i >= 0; i--) {
    html += `<div class="calendar-day other-month">${prevMonthLastDay - i}</div>`;
  }

  // 当月日期
  const today = new Date();
  for (let d = 1; d <= daysInMonth; d++) {
    const isToday = year === today.getFullYear() && month === today.getMonth() && d === today.getDate();
    // TODO: 检查是否有学习内容
    const hasContent = false;
    html += `<div class="calendar-day ${isToday ? 'today' : ''} ${hasContent ? 'has-content' : ''}">${d}</div>`;
  }

  // 下月日期
  const remainingCells = 42 - (startDayOfWeek + daysInMonth);
  for (let d = 1; d <= remainingCells; d++) {
    html += `<div class="calendar-day other-month">${d}</div>`;
  }

  // 保留星期标题，替换日期
  const grid = $('.calendar-grid');
  const weekdays = grid.querySelectorAll('.weekday');
  grid.innerHTML = '';
  weekdays.forEach(w => grid.appendChild(w));
  grid.insertAdjacentHTML('beforeend', html);
}

// ========== 个人中心 ==========
async function loadProfile() {
  if (!currentUser) return;

  $('#profile-username').value = currentUser.username || '';
  $('#profile-nickname').value = currentUser.nickname || '';
  $('#profile-real-name').value = currentUser.real_name || '';
  $('#profile-age').value = currentUser.age || '';
  $('#profile-occupation').value = currentUser.occupation || '';
  $('#profile-learning-goal').value = currentUser.learning_goal || '';
}

async function saveProfile() {
  const data = {
    nickname: $('#profile-nickname').value.trim(),
    real_name: $('#profile-real-name').value.trim(),
    age: parseInt($('#profile-age').value) || null,
    occupation: $('#profile-occupation').value.trim(),
    learning_goal: $('#profile-learning-goal').value.trim()
  };

  const result = await api.put(`/api/users/${currentUser.id}`, data);
  if (result) {
    currentUser = { ...currentUser, ...data };
    $('#user-name').textContent = currentUser.nickname || currentUser.username;
    showToast('个人信息已保存', 'success');
  }
}

// ========== 工具函数 ==========
function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// ========== 考试模块 ==========
async function startExam(planId, itemId) {
  showToast('正在生成考试题目，请稍候...', 'info');
  const data = await api.post('/api/exams/generate', {
    plan_id: planId,
    item_id: itemId,
    num_questions: 10
  });
  if (data?.exam) {
    showToast('考试题目已生成', 'success');
    // 获取考试详情（不含答案）
    const examData = await api.get(`/api/exams/${data.exam.id}`);
    if (examData) {
      currentExam = examData.exam;
      renderExamPage(examData);
    }
  }
}

function renderExamPage(data) {
  const exam = data.exam;
  const questions = data.questions || [];
  currentExam = exam;

  $('#exam-title').textContent = exam.title;
  $('#submit-exam-btn').classList.remove('hidden');
  $('#export-exam-btn').classList.remove('hidden');

  // 按题型分组
  const typeGroups = {};
  const typeNames = {
    'single_choice': '单选题',
    'multiple_choice': '多选题',
    'true_false': '判断题',
    'fill_blank': '填空题',
    'short_answer': '简答题'
  };

  questions.forEach(q => {
    const typeName = typeNames[q.question_type] || '其他';
    if (!typeGroups[typeName]) {
      typeGroups[typeName] = [];
    }
    typeGroups[typeName].push(q);
  });

  let html = '<div class="exam-info">';
  html += `<p>共 ${exam.total_questions} 题，满分 100 分，及格线 ${exam.passing_score} 分</p>`;
  html += '</div>';

  let questionNum = 0;
  for (const [typeName, groupQuestions] of Object.entries(typeGroups)) {
    html += `<div class="exam-section">`;
    html += `<h3 class="exam-section-title">${typeName}（共 ${groupQuestions.length} 题）</h3>`;

    groupQuestions.forEach(q => {
      questionNum++;
      html += `<div class="exam-question" data-question-id="${q.id}">`;
      html += `<div class="exam-question-text">${questionNum}. ${escapeHtml(q.question)}</div>`;

      if (q.question_type === 'single_choice' && q.options && q.options.length > 0) {
        html += '<div class="exam-options">';
        const labels = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'];
        q.options.forEach((opt, i) => {
          html += `
            <label class="exam-option">
              <input type="radio" name="q_${q.id}" value="${labels[i]}">
              <span class="option-label">${labels[i]}</span>
              <span class="option-text">${escapeHtml(opt)}</span>
            </label>
          `;
        });
        html += '</div>';
      } else if (q.question_type === 'multiple_choice' && q.options && q.options.length > 0) {
        html += '<div class="exam-options">';
        const labels = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'];
        q.options.forEach((opt, i) => {
          html += `
            <label class="exam-option">
              <input type="checkbox" name="q_${q.id}" value="${labels[i]}">
              <span class="option-label">${labels[i]}</span>
              <span class="option-text">${escapeHtml(opt)}</span>
            </label>
          `;
        });
        html += '<div class="exam-hint">（多选题，可选择多个答案）</div>';
        html += '</div>';
      } else if (q.question_type === 'true_false') {
        html += '<div class="exam-options">';
        html += `
          <label class="exam-option">
            <input type="radio" name="q_${q.id}" value="正确">
            <span class="option-label">A</span>
            <span class="option-text">正确</span>
          </label>
          <label class="exam-option">
            <input type="radio" name="q_${q.id}" value="错误">
            <span class="option-label">B</span>
            <span class="option-text">错误</span>
          </label>
        `;
        html += '</div>';
      } else if (q.question_type === 'fill_blank') {
        html += `
          <div class="exam-fill-input">
            <input type="text" class="fill-blank-input" data-question-id="${q.id}" placeholder="请输入答案">
          </div>
        `;
      } else if (q.question_type === 'short_answer') {
        html += `
          <div class="exam-short-input">
            <textarea class="short-answer-input" data-question-id="${q.id}" placeholder="请输入你的答案..." rows="4"></textarea>
          </div>
        `;
      }

      html += '</div>';
    });

    html += '</div>';
  }

  $('#exam-content').innerHTML = html;
  showPage('exam-page');
}

async function submitExam(examId) {
  if (!currentExam) return;

  // 收集答案
  const answers = {};
  const questionEls = $$('.exam-question');

  let allAnswered = true;
  questionEls.forEach(el => {
    const qId = el.dataset.questionId;
    const radio = el.querySelector('input[type="radio"]:checked');
    const checkboxes = el.querySelectorAll('input[type="checkbox"]:checked');
    const fillInput = el.querySelector('.fill-blank-input');
    const shortInput = el.querySelector('.short-answer-input');

    if (radio) {
      answers[qId] = radio.value;
    } else if (checkboxes.length > 0) {
      answers[qId] = Array.from(checkboxes).map(cb => cb.value).join(',');
    } else if (fillInput && fillInput.value.trim()) {
      answers[qId] = fillInput.value.trim();
    } else if (shortInput && shortInput.value.trim()) {
      answers[qId] = shortInput.value.trim();
    } else {
      allAnswered = false;
    }
  });

  if (Object.keys(answers).length === 0) {
    showToast('请至少回答一道题目', 'warning');
    return;
  }

  if (!allAnswered) {
    if (!confirm('还有题目未作答，确定要提交吗？')) return;
  }

  const data = await api.post(`/api/exams/${examId}/submit`, { answers });
  if (data?.result) {
    renderExamResult(data);
  }
}

function renderExamResult(data) {
  const result = data.result;
  const details = data.details || [];

  // 隐藏提交和导出按钮
  $('#submit-exam-btn').classList.add('hidden');
  $('#export-exam-btn').classList.add('hidden');

  let html = `
    <div class="exam-result-summary ${result.passed ? 'passed' : 'failed'}">
      <div class="result-score">${result.score}</div>
      <div class="result-label">得分</div>
      <div class="result-detail">
        答对 ${result.correct_count}/${result.total_count} 题
        ${result.passed ? ' - 已及格' : ' - 未及格'}
        （及格线 ${result.passing_score} 分）
      </div>
    </div>
  `;

  // 按题型分组显示结果
  const typeNames = {
    'single_choice': '单选题',
    'multiple_choice': '多选题',
    'true_false': '判断题',
    'fill_blank': '填空题',
    'short_answer': '简答题'
  };

  const typeGroups = {};
  details.forEach(d => {
    const typeName = typeNames[d.question_type] || '其他';
    if (!typeGroups[typeName]) typeGroups[typeName] = [];
    typeGroups[typeName].push(d);
  });

  let questionNum = 0;
  for (const [typeName, groupDetails] of Object.entries(typeGroups)) {
    html += `<div class="exam-section">`;
    html += `<h3 class="exam-section-title">${typeName}</h3>`;

    groupDetails.forEach(d => {
      questionNum++;
      const correctClass = d.is_correct ? 'correct' : 'incorrect';
      const icon = d.is_correct ? '&#10003;' : '&#10007;';

      html += `
        <div class="exam-result-question ${correctClass}">
          <div class="result-question-header">
            <span class="result-icon ${correctClass}">${icon}</span>
            <span class="result-question-num">${questionNum}.</span>
            <span class="result-question-text">${escapeHtml(d.question)}</span>
          </div>
      `;

      // 显示选项（如果有）
      if (d.options && d.options.length > 0) {
        html += '<div class="result-options">';
        const labels = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'];
        d.options.forEach((opt, i) => {
          let optClass = '';
          if (labels[i] === d.correct_answer) optClass = 'correct-option';
          if (labels[i] === d.user_answer && !d.is_correct) optClass = 'wrong-option';
          html += `<div class="result-option ${optClass}">${labels[i]}. ${escapeHtml(opt)}</div>`;
        });
        html += '</div>';
      }

      html += `
          <div class="result-answers">
            <div class="result-your-answer">你的答案：${escapeHtml(d.user_answer || '未作答')}</div>
            ${!d.is_correct ? `<div class="result-correct-answer">正确答案：${escapeHtml(d.correct_answer)}</div>` : ''}
          </div>
      `;

      if (d.explanation) {
        html += `
          <div class="result-explanation">
            <strong>解析：</strong>${escapeHtml(d.explanation)}
          </div>
        `;
      }

      html += '</div>';
    });

    html += '</div>';
  }

  // 添加返回按钮
  html += `
    <div class="exam-result-actions">
      <button class="btn btn-primary" onclick="backFromExam()">返回计划</button>
      <button class="btn btn-secondary" onclick="exportExam(${currentExam.id})">导出试卷</button>
    </div>
  `;

  $('#exam-content').innerHTML = html;
}

async function exportExam(examId) {
  const data = await api.get(`/api/exams/${examId}/export`);
  if (data?.html) {
    const newWindow = window.open('', '_blank');
    newWindow.document.write(data.html);
    newWindow.document.close();
  }
}

function backFromExam() {
  showPage('main-page');
  showContentPage('plans');
  if (currentPlan) {
    viewPlan(currentPlan.plan.id);
  } else {
    loadPlans();
  }
}

// ========== 事件绑定 ==========
function bindEvents() {
  // 登录表单
  $('#login-form')?.addEventListener('submit', (e) => {
    e.preventDefault();
    login($('#username').value.trim(), $('#password').value);
  });

  // 登出
  $('#logout-btn')?.addEventListener('click', logout);

  // 导航
  $$('.nav a').forEach(a => {
    a.addEventListener('click', (e) => {
      e.preventDefault();
      const page = a.dataset.page;
      showContentPage(page);
      if (page === 'plans') loadPlans();
      if (page === 'calendar') loadCalendar();
      if (page === 'profile') {
        loadProfile();
        renderLearnersList();
      }
      if (page === 'dashboard') loadDashboard();
    });
  });

  // 底部导航
  $$('.bottom-nav-item').forEach(btn => {
    btn.addEventListener('click', () => {
      const page = btn.dataset.page;
      showContentPage(page);
      if (page === 'plans') loadPlans();
      if (page === 'calendar') loadCalendar();
      if (page === 'profile') loadProfile();
      if (page === 'dashboard') loadDashboard();
    });
  });

  // 快速操作
  $('#create-plan-btn')?.addEventListener('click', () => showModal('create-plan-modal'));
  $('#view-plans-btn')?.addEventListener('click', () => {
    showContentPage('plans');
    loadPlans();
  });

  // 创建计划
  $('#create-plan-form')?.addEventListener('submit', createPlan);
  $('#cancel-create')?.addEventListener('click', () => hideModal('create-plan-modal'));
  // 只为创建计划弹窗的关闭按钮绑定事件
  $('#create-plan-modal .close-btn')?.addEventListener('click', (e) => {
    e.preventDefault();
    e.stopPropagation();
    hideModal('create-plan-modal');
  });

  // 自动推荐天数
  $('#plan-topic')?.addEventListener('input', debounce(async (e) => {
    const topic = e.target.value.trim();
    if (topic.length >= 2) {
      const data = await api.post('/api/plans/recommend-days', { topic });
      if (data?.days) {
        $('#plan-days').value = data.days;
      }
    }
  }, 500));

  // 新建计划按钮
  $('#new-plan-btn')?.addEventListener('click', () => showModal('create-plan-modal'));

  // 日历导航
  $('#prev-month')?.addEventListener('click', () => {
    currentCalendarDate.setMonth(currentCalendarDate.getMonth() - 1);
    loadCalendar();
  });
  $('#next-month')?.addEventListener('click', () => {
    currentCalendarDate.setMonth(currentCalendarDate.getMonth() + 1);
    loadCalendar();
  });

  // 个人中心
  $('#save-profile-btn')?.addEventListener('click', saveProfile);

  // 学习者管理
  $('#add-learner-btn')?.addEventListener('click', () => showModal('add-learner-modal'));
  $('#add-learner-form')?.addEventListener('submit', addLearner);

  // 学习者切换下拉框
  $('#learner-select')?.addEventListener('change', (e) => {
    if (e.target.value) {
      switchLearner(parseInt(e.target.value));
    }
  });

  // 点击学习者名称显示下拉框
  $('#learner-switch')?.addEventListener('click', (e) => {
    if (e.target.id === 'current-learner-name' || e.target.closest('#learner-switch')) {
      const select = $('#learner-select');
      select.classList.toggle('hidden');
      if (!select.classList.contains('hidden')) {
        select.focus();
      }
    }
  });

  // 学习页面
  $('#back-btn')?.addEventListener('click', () => {
    // 返回计划详情页或计划列表
    if (currentPlan?.plan?.id) {
      window.location.hash = `#/plan/${currentPlan.plan.id}`;
    } else {
      window.location.hash = '#/plans';
    }
  });
  $('#ask-btn')?.addEventListener('click', askQuestion);
  $('#question-input')?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      askQuestion();
    }
  });

  // 考试页面
  $('#exam-back-btn')?.addEventListener('click', backFromExam);
  $('#submit-exam-btn')?.addEventListener('click', () => {
    if (currentExam) submitExam(currentExam.id);
  });
  $('#export-exam-btn')?.addEventListener('click', () => {
    if (currentExam) exportExam(currentExam.id);
  });

  // 移动端菜单
  const menuToggle = document.createElement('button');
  menuToggle.className = 'menu-toggle';
  menuToggle.innerHTML = '☰';
  menuToggle.addEventListener('click', () => {
    $('.nav').classList.toggle('open');
  });
  $('.header').insertBefore(menuToggle, $('.nav'));

  // 点击外部关闭菜单
  document.addEventListener('click', (e) => {
    if (!e.target.closest('.header')) {
      $('.nav')?.classList.remove('open');
    }
  });

  // 弹窗点击外部关闭
  $$('.modal').forEach(modal => {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) hideModal(modal.id);
    });
  });
}

// ========== 路由处理 ==========
function handleRoute() {
  const hash = window.location.hash;

  // 学习页面路由: #/learning/:itemId
  if (hash.startsWith('#/learning/')) {
    const itemId = parseInt(hash.split('/')[2]);
    if (itemId) {
      // 需要先加载计划列表找到对应的 plan_id
      loadPlanForItem(itemId);
    }
    return;
  }

  // 计划详情路由: #/plan/:planId
  if (hash.startsWith('#/plan/')) {
    const planId = parseInt(hash.split('/')[2]);
    if (planId) {
      showPage('main-page');
      showContentPage('plans');
      viewPlan(planId);
    }
    return;
  }

  // 默认页面路由
  const pageMap = {
    '#/plans': 'plans',
    '#/calendar': 'calendar',
    '#/profile': 'profile',
    '#/dashboard': 'dashboard'
  };

  const page = pageMap[hash];
  if (page && currentUser) {
    showPage('main-page');
    showContentPage(page);
    if (page === 'plans') loadPlans();
    if (page === 'calendar') loadCalendar();
    if (page === 'profile') {
      loadProfile();
      renderLearnersList();
    }
    if (page === 'dashboard') loadDashboard();
  }
}

async function loadPlanForItem(itemId) {
  // 尝试从当前计划中找到 item
  if (currentPlan?.items) {
    const item = currentPlan.items.find(i => i.id === itemId);
    if (item) {
      viewItemContent(currentPlan.plan.id, itemId);
      return;
    }
  }
  // 否则先加载所有计划
  const data = await api.get('/api/plans');
  if (data?.plans) {
    for (const plan of data.plans) {
      const planData = await api.get(`/api/plans/${plan.id}`);
      if (planData?.items) {
        const item = planData.items.find(i => i.id === itemId);
        if (item) {
          currentPlan = planData;
          viewItemContent(plan.id, itemId);
          return;
        }
      }
    }
  }
  showToast('未找到对应的学习内容', 'error');
}

// ========== 工具函数 ==========
function debounce(fn, delay) {
  let timer = null;
  return function(...args) {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delay);
  };
}

// ========== 初始化 ==========
document.addEventListener('DOMContentLoaded', () => {
  bindEvents();
  initAuth();
  window.addEventListener('hashchange', handleRoute);
});
