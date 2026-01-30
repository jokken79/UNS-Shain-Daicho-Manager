// API Base URL
const API_BASE = '/api';

// Utility functions
function formatCurrency(value) {
  if (value === null || value === undefined) return '-';
  return '¥' + value.toLocaleString();
}

function formatDate(dateStr) {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  return date.toLocaleDateString('ja-JP');
}

function formatPercentage(value) {
  if (value === null || value === undefined) return '-';
  return value + '%';
}

// File Upload Handler
document.getElementById('uploadForm')?.addEventListener('submit', async function(e) {
  e.preventDefault();
  const fileInput = document.getElementById('fileInput');
  const statusDiv = document.getElementById('uploadStatus');

  if (!fileInput.files[0]) {
    statusDiv.textContent = 'Por favor seleccione un archivo';
    statusDiv.className = 'error';
    return;
  }

  const formData = new FormData();
  formData.append('file', fileInput.files[0]);

  try {
    statusDiv.textContent = 'Cargando archivo...';
    statusDiv.className = '';

    const response = await fetch(`${API_BASE}/excel/upload`, {
      method: 'POST',
      body: formData
    });

    const result = await response.json();

    if (response.ok) {
      statusDiv.textContent = `✅ ${result.message} - ${result.stats.total} empleados cargados (${result.stats.active} activos)`;
      statusDiv.className = 'success';
      loadDashboardData();
    } else {
      statusDiv.textContent = `❌ Error: ${result.message}`;
      statusDiv.className = 'error';
    }
  } catch (error) {
    statusDiv.textContent = `❌ Error de conexión: ${error.message}`;
    statusDiv.className = 'error';
  }
});

// Dashboard Data
async function loadDashboardData() {
  try {
    const [statsRes, nationalityRes, dispatchRes] = await Promise.all([
      fetch(`${API_BASE}/employees/stats`),
      fetch(`${API_BASE}/employees/stats/nationality`),
      fetch(`${API_BASE}/employees/stats/dispatch-companies?top=10`)
    ]);

    const stats = await statsRes.json();
    const nationality = await nationalityRes.json();
    const dispatch = await dispatchRes.json();

    // Update stats cards
    document.getElementById('totalEmployees').textContent = stats.total || 0;
    document.getElementById('activeEmployees').textContent = stats.active || 0;
    document.getElementById('inactiveEmployees').textContent = stats.inactive || 0;

    const rate = stats.total > 0 ? Math.round((stats.active / stats.total) * 100) : 0;
    document.getElementById('activeRate').textContent = rate + '%';

    // Category Chart
    if (stats.byCategory && stats.byCategory.length > 0) {
      const categoryData = [{
        values: stats.byCategory.map(c => c.active),
        labels: stats.byCategory.map(c => c.category),
        type: 'pie',
        hole: 0.4,
        marker: { colors: ['#4472C4', '#ED7D31', '#70AD47'] }
      }];
      Plotly.newPlot('categoryChart', categoryData, { margin: { t: 20, b: 20 } });
    }

    // Nationality Chart
    if (nationality && nationality.length > 0) {
      const top5 = nationality.slice(0, 5);
      const nationalityData = [{
        x: top5.map(n => n.nationality),
        y: top5.map(n => n.count),
        type: 'bar',
        marker: { color: '#4472C4' }
      }];
      Plotly.newPlot('nationalityChart', nationalityData, { margin: { t: 20, b: 60 } });
    }

    // Dispatch Companies Chart
    if (dispatch && dispatch.length > 0) {
      const dispatchData = [{
        x: dispatch.map(d => d.count),
        y: dispatch.map(d => d.company),
        type: 'bar',
        orientation: 'h',
        marker: { color: '#70AD47' }
      }];
      Plotly.newPlot('dispatchChart', dispatchData, {
        margin: { l: 200, t: 20, b: 40 },
        yaxis: { automargin: true }
      });
    }

  } catch (error) {
    console.error('Error loading dashboard data:', error);
  }
}

// Search Employees
async function searchEmployees() {
  const searchInput = document.getElementById('searchInput').value;
  const activeOnly = document.getElementById('activeOnly').checked;
  const resultsDiv = document.getElementById('searchResults');

  if (!searchInput.trim()) {
    resultsDiv.innerHTML = '<p class="placeholder-text">Ingrese un nombre para buscar empleados</p>';
    return;
  }

  try {
    const response = await fetch(
      `${API_BASE}/employees/search?name=${encodeURIComponent(searchInput)}&activeOnly=${activeOnly}`
    );
    const employees = await response.json();

    if (employees.length === 0) {
      resultsDiv.innerHTML = '<p class="placeholder-text">No se encontraron empleados</p>';
      return;
    }

    resultsDiv.innerHTML = employees.map(emp => `
      <div class="employee-card">
        <h4>${emp.name} (${emp.nameKana || '-'})</h4>
        <div class="info-row"><span>ID:</span><span>${emp.employeeId}</span></div>
        <div class="info-row"><span>Estado:</span><span>${emp.currentStatus}</span></div>
        <div class="info-row"><span>Nacionalidad:</span><span>${emp.nationality || '-'}</span></div>
        <div class="info-row"><span>Categoría:</span><span>${emp.category}</span></div>
        <div class="info-row"><span>Tarifa/Hora:</span><span>${formatCurrency(emp.hourlyRate)}</span></div>
        <div class="info-row"><span>Vencimiento Visa:</span><span>${formatDate(emp.visaExpiry)}</span></div>
        <div class="info-row"><span>Empresa:</span><span>${emp.dispatchCompany || '-'}</span></div>
      </div>
    `).join('');

  } catch (error) {
    resultsDiv.innerHTML = `<p class="placeholder-text">Error: ${error.message}</p>`;
  }
}

// Visa Alerts
async function loadVisaAlerts() {
  const days = document.getElementById('daysSlider')?.value || 90;
  const alertsList = document.getElementById('visaAlertsList');

  try {
    const response = await fetch(`${API_BASE}/visas/alerts?days=${days}`);
    const data = await response.json();

    // Update counters
    document.getElementById('criticalCount').textContent = data.critical || 0;
    document.getElementById('warningCount').textContent = data.warning || 0;
    document.getElementById('upcomingCount').textContent = data.upcoming || 0;
    document.getElementById('totalAlerts').textContent = data.total || 0;

    if (!data.alerts || data.alerts.length === 0) {
      alertsList.innerHTML = '<p class="placeholder-text">No hay alertas de visa en este rango</p>';
      return;
    }

    alertsList.innerHTML = data.alerts.map(alert => `
      <div class="alert-item ${alert.urgencyLevel}">
        <span class="alert-badge ${alert.urgencyLevel}">
          ${alert.urgencyLevel === 'critical' ? '🔴 URGENTE' :
            alert.urgencyLevel === 'warning' ? '🟠 ADVERTENCIA' : '🟡 PRÓXIMO'}
        </span>
        <div style="flex: 1">
          <strong>${alert.employee.name}</strong> (ID: ${alert.employee.employeeId})
          <br>
          <small>${alert.employee.nationality || '-'} | ${alert.employee.dispatchCompany || '-'}</small>
        </div>
        <div style="text-align: right">
          <strong>${alert.daysUntilExpiry} días</strong>
          <br>
          <small>Vence: ${formatDate(alert.expiryDate)}</small>
        </div>
      </div>
    `).join('');

  } catch (error) {
    alertsList.innerHTML = `<p class="placeholder-text">Error: ${error.message}</p>`;
  }
}

// Salary Data
async function loadSalaryData() {
  try {
    const [statsRes, distRes, categoryRes, topRes] = await Promise.all([
      fetch(`${API_BASE}/salaries/stats`),
      fetch(`${API_BASE}/salaries/distribution`),
      fetch(`${API_BASE}/salaries/by-category`),
      fetch(`${API_BASE}/salaries/top-earners?top=10`)
    ]);

    const stats = await statsRes.json();
    const distribution = await distRes.json();
    const byCategory = await categoryRes.json();
    const topEarners = await topRes.json();

    // Update stats
    document.getElementById('avgHourlyRate').textContent = formatCurrency(stats.hourlyRate?.average);
    document.getElementById('avgBillingRate').textContent = formatCurrency(stats.billingRate?.average);
    document.getElementById('avgProfitMargin').textContent = formatCurrency(stats.profitMargin?.average);

    // Distribution Chart
    if (distribution && distribution.length > 0) {
      const distData = [{
        x: distribution.map(d => d.range),
        y: distribution.map(d => d.count),
        type: 'bar',
        marker: { color: '#4472C4' }
      }];
      Plotly.newPlot('salaryDistChart', distData, {
        margin: { t: 20, b: 80 },
        xaxis: { tickangle: -45 }
      });
    }

    // Category Comparison Chart
    if (byCategory && byCategory.length > 0) {
      const catData = [{
        x: byCategory.map(c => c.category),
        y: byCategory.map(c => c.average),
        type: 'bar',
        marker: { color: ['#4472C4', '#ED7D31', '#70AD47'] }
      }];
      Plotly.newPlot('categoryCompareChart', catData, { margin: { t: 20, b: 60 } });
    }

    // Top Earners Table
    if (topEarners && topEarners.length > 0) {
      const tableHtml = `
        <table class="data-table">
          <thead>
            <tr>
              <th>Nombre</th>
              <th>ID</th>
              <th>Categoría</th>
              <th>Tarifa/Hora</th>
              <th>Facturación</th>
              <th>Margen</th>
            </tr>
          </thead>
          <tbody>
            ${topEarners.map(emp => `
              <tr>
                <td>${emp.name}</td>
                <td>${emp.employeeId}</td>
                <td>${emp.category}</td>
                <td>${formatCurrency(emp.hourlyRate)}</td>
                <td>${formatCurrency(emp.billingRate)}</td>
                <td>${formatCurrency(emp.profitMargin)}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      `;
      document.getElementById('topEarnersTable').innerHTML = tableHtml;
    }

  } catch (error) {
    console.error('Error loading salary data:', error);
  }
}

// Reports Data
async function loadReportsData() {
  try {
    const [ageRes, tenureRes, summaryRes] = await Promise.all([
      fetch(`${API_BASE}/employees/stats/age`),
      fetch(`${API_BASE}/reports/tenure`),
      fetch(`${API_BASE}/reports/summary`)
    ]);

    const age = await ageRes.json();
    const tenure = await tenureRes.json();
    const summary = await summaryRes.json();

    // Age Chart
    if (age && age.length > 0) {
      const ageData = [{
        values: age.map(a => a.count),
        labels: age.map(a => a.label),
        type: 'pie',
        marker: { colors: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40'] }
      }];
      Plotly.newPlot('ageChart', ageData, { margin: { t: 20, b: 20 } });
    }

    // Tenure Chart
    if (tenure && tenure.length > 0) {
      const tenureData = [{
        x: tenure.map(t => t.label),
        y: tenure.map(t => t.count),
        type: 'bar',
        marker: { color: '#70AD47' }
      }];
      Plotly.newPlot('tenureChart', tenureData, {
        margin: { t: 20, b: 80 },
        xaxis: { tickangle: -45 }
      });
    }

    // Summary Report
    if (summary) {
      const summaryHtml = `
        <div class="summary-item"><span>Total Empleados:</span><span><strong>${summary.employeeStats?.total || 0}</strong></span></div>
        <div class="summary-item"><span>Empleados Activos:</span><span><strong>${summary.employeeStats?.active || 0}</strong></span></div>
        <div class="summary-item"><span>Tarifa Horaria Promedio:</span><span><strong>${formatCurrency(summary.salaryStats?.hourlyRate?.average)}</strong></span></div>
        <div class="summary-item"><span>Margen de Ganancia Promedio:</span><span><strong>${formatCurrency(summary.salaryStats?.profitMargin?.average)}</strong></span></div>
        <div class="summary-item"><span>Alertas de Visa (Total):</span><span><strong>${summary.visaAlerts?.total || 0}</strong></span></div>
        <div class="summary-item"><span>Alertas Críticas:</span><span class="text-danger"><strong>${summary.visaAlerts?.critical || 0}</strong></span></div>
        <div class="summary-item"><span>Generado:</span><span>${new Date(summary.generatedAt).toLocaleString()}</span></div>
      `;
      document.getElementById('summaryReport').innerHTML = summaryHtml;
    }

  } catch (error) {
    console.error('Error loading reports data:', error);
  }
}

// Download Export
function downloadExport(format) {
  const activeOnly = document.getElementById('exportActiveOnly')?.checked ?? true;
  const url = `${API_BASE}/reports/export/${format}?activeOnly=${activeOnly}`;
  window.location.href = url;
}
