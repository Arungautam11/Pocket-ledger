(() => {
  if (!window.Chart) return

  const readJson = (id) => JSON.parse(document.getElementById(id).textContent)
  const labels = readJson('daily-labels')
  const expenses = readJson('daily-expenses')
  const income = readJson('daily-income')
  const categories = readJson('category-labels')
  const categoryValues = readJson('category-values')
  const colors = ['#287d62', '#e49069', '#d1a543', '#8473b0', '#5896a1', '#bf7185', '#809b57', '#537397']

  const chartTheme = () => ({
    grid: document.documentElement.dataset.theme === 'dark' ? 'rgba(255,255,255,.08)' : 'rgba(28,45,38,.07)',
    ink: document.documentElement.dataset.theme === 'dark' ? '#a8b4ad' : '#84918a',
  })
  const axes = chartTheme()
  const trendChart = new Chart(document.getElementById('spending-chart'), {
    type: 'line',
    data: { labels, datasets: [
      { label: 'Income', data: income, borderColor: '#287d62', backgroundColor: 'rgba(40,125,98,.08)', tension: .35, pointRadius: 2, borderWidth: 2 },
      { label: 'Expenses', data: expenses, borderColor: '#e49069', backgroundColor: 'rgba(228,144,105,.07)', tension: .35, pointRadius: 2, borderWidth: 2 },
    ] },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { labels: { color: axes.ink, usePointStyle: true, boxWidth: 7, font: { size: 10 } } } },
      scales: { x: { grid: { display: false }, ticks: { color: axes.ink } }, y: { beginAtZero: true, grid: { color: axes.grid }, ticks: { color: axes.ink } } } },
  })
  const categoryChart = new Chart(document.getElementById('category-chart'), {
    type: 'doughnut',
    data: { labels: categories, datasets: [{ data: categoryValues, backgroundColor: colors, borderWidth: 0, hoverOffset: 5 }] },
    options: { cutout: '76%', plugins: { legend: { display: false } }, maintainAspectRatio: false },
  })
  window.ledgerCharts = [trendChart, categoryChart]

  const legend = document.getElementById('category-legend')
  if (!categories.length) {
    legend.textContent = 'Add an expense to see category totals.'
    legend.classList.add('muted-note')
    return
  }
  categories.forEach((name, index) => {
    const row = document.createElement('div')
    row.className = 'legend-item'
    const dot = document.createElement('i')
    dot.style.backgroundColor = colors[index % colors.length]
    const label = document.createElement('span')
    label.textContent = name
    const amount = document.createElement('strong')
    const currency = document.documentElement.dataset.currency || 'INR'
    amount.textContent = new Intl.NumberFormat('en-IN', { style: 'currency', currency }).format(Number(categoryValues[index]))
    row.append(dot, label, amount)
    legend.append(row)
  })
  window.addEventListener('ledger-theme-change', () => {
    const theme = chartTheme()
    trendChart.options.scales.x.ticks.color = theme.ink
    trendChart.options.scales.y.ticks.color = theme.ink
    trendChart.options.scales.y.grid.color = theme.grid
    trendChart.options.plugins.legend.labels.color = theme.ink
    trendChart.update()
  })
})()
