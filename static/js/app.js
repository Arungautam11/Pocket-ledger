(() => {
  const root = document.documentElement
  const themeButton = document.getElementById('theme-toggle')
  function setTheme(theme) {
    root.dataset.theme = theme
    localStorage.setItem('pocket-ledger-theme', theme)
    const icon = document.querySelector('.theme-icon')
    const label = document.querySelector('.theme-text')
    if (icon) icon.textContent = theme === 'dark' ? '☀' : '☾'
    if (label) label.textContent = theme === 'dark' ? 'Light mode' : 'Dark mode'
    window.dispatchEvent(new CustomEvent('ledger-theme-change'))
  }
  setTheme(localStorage.getItem('pocket-ledger-theme') || 'light')
  themeButton?.addEventListener('click', () => setTheme(root.dataset.theme === 'dark' ? 'light' : 'dark'))
  document.getElementById('theme-toggle-settings')?.addEventListener('click', () => setTheme(root.dataset.theme === 'dark' ? 'light' : 'dark'))
  document.getElementById('mobile-menu')?.addEventListener('click', () => document.querySelector('.sidebar')?.classList.toggle('open'))
  document.querySelectorAll('form[data-confirm]').forEach((form) => form.addEventListener('submit', (event) => {
    if (!window.confirm(form.dataset.confirm)) event.preventDefault()
  }))
  window.setTimeout(() => document.querySelectorAll('.toast').forEach((toast) => toast.classList.add('toast-hidden')), 4200)
})()
