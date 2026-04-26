/* ============================================================
   CampusConnect — main.js
   Shared utilities: sidebar, toasts, leaderboard poll, helpers
   ============================================================ */

/* ── Sidebar mobile toggle ─────────────────────────────────── */
(function () {
  const sidebar     = document.getElementById('sidebar');
  const toggle      = document.getElementById('sidebarToggle');
  const mainContent = document.getElementById('mainContent');

  if (!toggle || !sidebar) return;

  toggle.addEventListener('click', () => {
    // Desktop: collapse/expand
    if (window.innerWidth > 768) {
      sidebar.classList.toggle('collapsed');
      mainContent && mainContent.classList.toggle('expanded');
    } else {
      // Mobile: slide in/out
      sidebar.classList.toggle('mobile-open');
    }
  });

  // Close sidebar on outside click (mobile)
  document.addEventListener('click', (e) => {
    if (window.innerWidth <= 768 &&
        sidebar.classList.contains('mobile-open') &&
        !sidebar.contains(e.target) &&
        !toggle.contains(e.target)) {
      sidebar.classList.remove('mobile-open');
    }
  });
})();

/* ── Toast helper ──────────────────────────────────────────── */
function showToast(message, type = 'success') {
  const container = document.querySelector('.toast-container') ||
    (() => {
      const c = document.createElement('div');
      c.className = 'toast-container position-fixed top-0 end-0 p-3';
      c.style.zIndex = '9999';
      document.body.appendChild(c);
      return c;
    })();

  const colorMap = { success: 'success', danger: 'danger', warning: 'warning', info: 'info' };
  const bg = colorMap[type] || 'info';

  const el = document.createElement('div');
  el.className = `toast align-items-center text-bg-${bg} border-0 show`;
  el.setAttribute('role', 'alert');
  el.innerHTML = `
    <div class="d-flex">
      <div class="toast-body">${message}</div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
    </div>`;
  container.appendChild(el);

  const t = new bootstrap.Toast(el, { delay: 4000 });
  t.show();
  el.addEventListener('hidden.bs.toast', () => el.remove());
}

/* ── Leaderboard live poll (admin dashboard) ───────────────── */
(function () {
  const list = document.getElementById('leaderboardList');
  if (!list) return;

  async function refreshLeaderboard() {
    try {
      const res = await axios.get('/admin/api/leaderboard');
      const data = res.data;
      if (!Array.isArray(data) || !data.length) return;

      list.innerHTML = data.map((a, i) => `
        <div class="lb-row" id="lb-${i}">
          <span class="lb-rank ${i < 3 ? 'top-' + (i + 1) : ''}">#${i + 1}</span>
          <div class="lb-avatar">${a.name[0]}</div>
          <div class="lb-info">
            <span class="lb-name">${a.name}</span>
            <span class="lb-college">${a.college}</span>
          </div>
          <span class="lb-pts">${a.points}</span>
        </div>`).join('');
    } catch (_) { /* silent fail */ }
  }

  // Poll every 30 seconds
  setInterval(refreshLeaderboard, 30000);
})();

/* ── Animate number counters ───────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('[data-count]').forEach(el => {
    const target   = +el.dataset.count;
    const isPercent = el.closest('.kpi-card')
      ?.querySelector('.kpi-label')
      ?.textContent.includes('%');
    let curr = 0;
    const step = Math.max(1, Math.ceil(target / 40));

    const iv = setInterval(() => {
      curr = Math.min(curr + step, target);
      el.textContent = curr + (isPercent ? '%' : '');
      if (curr >= target) clearInterval(iv);
    }, 30);
  });
});
