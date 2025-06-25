class FarmDashboard {
  constructor() {
    this.updateInterval = 30000; // Default 30 secondi
    this.retryCount = 0;
    this.maxRetries = 3;
    this.intervalId = null;
    this.init();
  }

  init() {
    this.setupRefreshRateSelector();
    this.loadDashboard();
    this.startAutoUpdate();
  }

  setupRefreshRateSelector() {
    const selector = document.getElementById("refresh-rate");
    if (selector) {
      const savedRate = localStorage.getItem("refreshRate");
      if (savedRate) {
        selector.value = savedRate;
        this.updateInterval = parseInt(savedRate);
      }
      selector.addEventListener("change", (e) => {
        this.updateInterval = parseInt(e.target.value);
        localStorage.setItem("refreshRate", this.updateInterval);
        this.stopAutoUpdate();
        this.startAutoUpdate();
      });
    }
  }

  async loadDashboard() {
    try {
      await Promise.allSettled([
        this.loadKPIs(),
        this.loadCharts(),
        this.loadSystemStatus(),
      ]);
      this.updateTimestamp();
      this.retryCount = 0;
    } catch (error) {
      console.error("Error loading dashboard:", error);
      this.handleLoadError();
    }
  }

  async fetchData(url) {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    if (data.error) {
      throw new Error(data.error);
    }
    return data;
  }

  async loadKPIs() {
    try {
      const kpis = await this.fetchData("/api/kpis");
      this.renderKPIs(kpis);
      this.generateAlerts(kpis);
    } catch (error) {
      console.error("Error loading KPIs:", error);
      this.renderKPIError();
    }
  }

  async loadCharts() {
    try {
      const charts = await this.fetchData("/api/charts");
      this.renderCharts(charts);
    } catch (error) {
      console.error("Error loading charts:", error);
      this.renderChartErrors();
    }
  }

  async loadSystemStatus() {
    try {
      const data = await this.fetchData("/api/system-status");
      this.renderSystemStatus(data);
    } catch (error) {
      console.error("Error loading system status:", error);
      this.renderSystemError();
    }
  }

  renderSystemStatus(data) {
    const container = document.getElementById("systems-status");
    if (!data.status || Object.keys(data.status).length === 0) {
      container.innerHTML = this.createErrorState(
        "Nessun dato di sistema disponibile"
      );
      return;
    }
    container.innerHTML = "";

    const servoData = data.status["Stato_Servo"] || {};
    const servoStats = data.statistics?.servo || { aperture_oggi: 0 };
    container.appendChild(this.createServoWidget(servoData, servoStats));

    const pumpData = data.status["Stato_Pompa"] || {};
    const pumpStats = data.statistics?.pompa || { ml_oggi: 0 };
    container.appendChild(this.createPumpWidget(pumpData, pumpStats));
  }

  createServoWidget(statusData, statsData) {
    const isOpen = statusData.status === "active";
    const widget = document.createElement("div");
    widget.className = "system-widget";
    widget.innerHTML = `
            <div class="widget-header">
                <div class="widget-icon">🚪</div>
                <div class="widget-title">Servo Cancello</div>
                <div class="status-indicator ${isOpen ? "active" : "inactive"}">
                    ${isOpen ? "APERTO" : "CHIUSO"}
                </div>
            </div>
            <div class="widget-content">
                <div class="stat-item">
                    <span class="stat-label">Aperture oggi</span>
                    <span class="stat-value">${
                      statsData.aperture_oggi || 0
                    }</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Ultimo Aggiornamento</span>
                    <span class="stat-value">${this.formatTimestamp(
                      statusData.timestamp
                    )}</span>
                </div>
            </div>
        `;
    return widget;
  }

  createPumpWidget(statusData, statsData) {
    const isActive = statusData.status === "active";
    const mlTotali = statsData.ml_oggi || 0;
    const dailyTargetMl = 5000; // Target giornaliero di 5L
    const progressPercentage = Math.min((mlTotali / dailyTargetMl) * 100, 100);

    let volumeDisplay =
      mlTotali < 1000
        ? `${mlTotali} ml`
        : `${(mlTotali / 1000).toFixed(2)} L`;

    const widget = document.createElement("div");
    widget.className = "system-widget";
    widget.innerHTML = `
            <div class="widget-header">
                <div class="widget-icon">💧</div>
                <div class="widget-title">Pompa Acqua</div>
                <div class="status-indicator ${isActive ? "active" : "inactive"}">
                    ${isActive ? "ATTIVA" : "SPENTA"}
                </div>
            </div>
            <div class="widget-content">
                <div class="stat-item">
                    <span class="stat-label">Volume erogato oggi</span>
                    <span class="stat-value">${volumeDisplay}</span>
                </div>
                <div class="progress-bar-container">
                    <div class="progress-bar" style="width: ${progressPercentage}%;"></div>
                </div>
                <div class="stat-item" style="margin-top: 8px;">
                    <span class="stat-label">Ultimo Aggiornamento</span>
                    <span class="stat-value">${this.formatTimestamp(
                      statusData.timestamp
                    )}</span>
                </div>
            </div>
        `;
    return widget;
  }

  renderKPIs(kpis) {
    const container = document.getElementById("kpi-container");
    if (!kpis || kpis.length === 0) {
      container.innerHTML = this.createErrorState(
        "Nessun dato KPI disponibile"
      );
      return;
    }
    container.innerHTML = "";
    kpis.forEach((kpi) => {
      const kpiHtml = `
                <div class="kpi-card status-${kpi.status}">
                    <div class="kpi-header">
                        <div class="kpi-title">${this.escapeHtml(kpi.title)}</div>
                        <div class="kpi-icon">${kpi.icon}</div>
                    </div>
                    <div class="kpi-value">${kpi.value}${kpi.unit}</div>
                    <div class="kpi-status">${this.getStatusText(
                      kpi.status
                    )}</div>
                </div>
            `;
      container.innerHTML += kpiHtml;
    });
  }

  renderCharts(charts) {
    this.renderChart("humidity-chart", charts.humidity, "Umidità");
    this.renderChart("resources-chart", charts.resources, "Risorse");
    this.renderChart("temperature-chart", charts.temperature, "Temperatura");
  }

  renderChart(elementId, chartData, chartName) {
    const element = document.getElementById(elementId);
    if (!element) return;

    try {
      if (chartData) {
        const parsedData = JSON.parse(chartData);
        element.innerHTML = "";
        const config = { responsive: true, displayModeBar: false };
        Plotly.newPlot(elementId, parsedData.data, parsedData.layout, config);
      } else {
        element.innerHTML = this.createErrorState(
          `${chartName} non disponibile`
        );
      }
    } catch (error) {
      console.error(`Error rendering ${chartName}:`, error);
      element.innerHTML = this.createErrorState(
        `Errore nel caricamento di ${chartName}`
      );
    }
  }

  generateAlerts(kpis) {
    const container = document.getElementById("alerts-container");
    if (!kpis || kpis.length === 0) {
      container.innerHTML = "";
      return;
    }
    let alerts = [];
    kpis.forEach((kpi) => {
      if (kpi.status === "critical")
        alerts.push({
          type: "critical",
          message: `🚨 CRITICO: ${kpi.title} a ${kpi.value}${kpi.unit}!`,
        });
      else if (kpi.status === "low")
        alerts.push({
          type: "warning",
          message: `⚠️ ATTENZIONE: ${kpi.title} basso: ${kpi.value}${kpi.unit}`,
        });
      else if (kpi.status === "high")
        alerts.push({
          type: "danger",
          message: `🔥 ALTO: ${kpi.title} elevato: ${kpi.value}${kpi.unit}`,
        });
    });

    if (alerts.length === 0) {
      container.innerHTML = `<div class="alert-item alert-success">✅ Tutti i parametri sono nella norma.</div>`;
    } else {
      container.innerHTML = alerts
        .map(
          (alert) =>
            `<div class="alert-item alert-${alert.type}">${this.escapeHtml(
              alert.message
            )}</div>`
        )
        .join("");
    }
  }

  renderError(containerId, message) {
    const container = document.getElementById(containerId);
    if (container) container.innerHTML = this.createErrorState(message, true);
  }
  renderKPIError() {
    this.renderError("kpi-container", "Errore nel caricamento dei KPI");
  }
  renderChartErrors() {
    ["humidity-chart", "resources-chart", "temperature-chart"].forEach((id) =>
      this.renderError(id, "Errore nel caricamento del grafico")
    );
  }
  renderSystemError() {
    this.renderError(
      "systems-status",
      "Errore nel caricamento dello stato sistemi"
    );
  }

  createErrorState(message, showRetry = false) {
    return `<div class="error-state"><h3>⚠️ Errore</h3><p>${this.escapeHtml(
      message
    )}</p>${
      showRetry
        ? `<button class="retry-button" onclick="dashboard.loadDashboard()">🔄 Riprova</button>`
        : ""
    }</div>`;
  }

  handleLoadError() {
    if (this.retryCount < this.maxRetries) {
      this.retryCount++;
      setTimeout(() => this.loadDashboard(), 5000);
    }
  }

  getStatusText(status) {
    const statuses = {
      good: "✅ Normale",
      low: "⚠️ Basso",
      high: "🔥 Alto",
      critical: "🚨 Critico",
    };
    return statuses[status] || "";
  }

  formatTimestamp(timestamp) {
    if (!timestamp) return "--:--";
    return new Date(timestamp).toLocaleTimeString("it-IT", {
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  updateTimestamp() {
    const element = document.getElementById("update-time");
    if (element)
      element.textContent = new Date().toLocaleTimeString("it-IT", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      });
  }

  startAutoUpdate() {
    if (this.intervalId) clearInterval(this.intervalId);
    this.intervalId = setInterval(
      () => this.loadDashboard(),
      this.updateInterval
    );
  }

  stopAutoUpdate() {
    if (this.intervalId) clearInterval(this.intervalId);
  }

  escapeHtml(text) {
    return text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
}

let dashboard;
document.addEventListener("DOMContentLoaded", () => {
  dashboard = new FarmDashboard();
});