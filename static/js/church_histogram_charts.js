/**
 * Histogram (bar) charts — PHM-ARCC dark theme
 * - Value labels drawn on top of each bar
 * - Supports single series or grouped (multi-series) bars
 */
(function (global) {
  'use strict';

  const SCHEMES = {
    gold: {
      border: '#c8a84b',
      fillTop: 'rgba(200, 168, 75, 0.9)',
      fillBottom: 'rgba(200, 168, 75, 0.3)',
      hover: 'rgba(242, 211, 122, 0.95)',
      label: '#f2d37a',
    },
    green: {
      border: '#2ecc71',
      fillTop: 'rgba(46, 204, 113, 0.85)',
      fillBottom: 'rgba(46, 204, 113, 0.25)',
      hover: 'rgba(72, 220, 140, 0.95)',
      label: '#6fe6a0',
    },
    blue: {
      border: '#5dade2',
      fillTop: 'rgba(93, 173, 226, 0.8)',
      fillBottom: 'rgba(93, 173, 226, 0.22)',
      hover: 'rgba(133, 193, 233, 0.95)',
      label: '#8fc7ef',
    },
    teal: {
      border: '#1f8f86',
      fillTop: 'rgba(31, 143, 134, 0.92)',
      fillBottom: 'rgba(31, 143, 134, 0.45)',
      hover: 'rgba(46, 178, 167, 0.98)',
      label: '#3fb9ad',
    },
    orange: {
      border: '#e07a3f',
      fillTop: 'rgba(224, 122, 63, 0.92)',
      fillBottom: 'rgba(224, 122, 63, 0.45)',
      hover: 'rgba(240, 150, 90, 0.98)',
      label: '#f0975a',
    },
  };

  // Default palette order for grouped charts (matches reference image: teal + orange)
  const GROUP_ORDER = ['teal', 'orange', 'gold', 'blue', 'green'];

  function formatTzs(value) {
    const n = Number(value) || 0;
    if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
    if (n >= 1000) return (n / 1000).toFixed(0) + 'K';
    return n.toLocaleString('en-US');
  }

  function labelText(value, formatY) {
    if (value == null) return '';
    if (formatY === 'currency') return formatTzs(value);
    if (formatY === 'percent') return value + '%';
    return String(value);
  }

  function makeGradient(ctx, chartArea, scheme) {
    const g = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
    g.addColorStop(0, scheme.fillTop);
    g.addColorStop(1, scheme.fillBottom);
    return g;
  }

  // Plugin: draw the value on top of every bar
  const valueLabelsPlugin = {
    id: 'phmValueLabels',
    afterDatasetsDraw(chart, _args, opts) {
      const { ctx } = chart;
      const formatY = (opts && opts.formatY) || 'number';
      ctx.save();
      ctx.textAlign = 'center';
      ctx.textBaseline = 'bottom';
      ctx.font = '700 11px system-ui, -apple-system, Segoe UI, sans-serif';
      chart.data.datasets.forEach((dataset, di) => {
        const meta = chart.getDatasetMeta(di);
        if (meta.hidden || !meta.data) return;
        meta.data.forEach((bar, i) => {
          const value = dataset.data[i];
          if (value == null || value === 0) return;
          ctx.fillStyle = dataset._labelColor || '#e8eef4';
          ctx.fillText(labelText(value, formatY), bar.x, bar.y - 5);
        });
      });
      ctx.restore();
    },
  };

  function buildScheme(name, index) {
    if (name && SCHEMES[name]) return SCHEMES[name];
    const key = GROUP_ORDER[index % GROUP_ORDER.length];
    return SCHEMES[key];
  }

  function makeDataset(cfg, scheme, isGrouped) {
    return {
      label: cfg.datasetLabel || cfg.label || 'Thamani',
      data: cfg.data || [],
      borderColor: scheme.border,
      borderWidth: 1.5,
      borderRadius: { topLeft: 8, topRight: 8, bottomLeft: 2, bottomRight: 2 },
      borderSkipped: false,
      maxBarThickness: isGrouped ? 34 : 48,
      _labelColor: scheme.label,
      backgroundColor(context) {
        const { chart } = context;
        const { ctx, chartArea } = chart;
        if (!chartArea) return scheme.fillTop;
        return makeGradient(ctx, chartArea, scheme);
      },
      hoverBackgroundColor: scheme.hover,
    };
  }

  function baseOptions(formatY, showLegend) {
    const yTicks =
      formatY === 'currency'
        ? { color: '#9fb2c8', callback: (v) => formatTzs(v) }
        : formatY === 'percent'
        ? { color: '#9fb2c8', callback: (v) => v + '%' }
        : { color: '#9fb2c8', precision: 0, stepSize: 1 };

    return {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      layout: { padding: { top: 24 } },
      plugins: {
        legend: {
          display: showLegend,
          labels: { color: '#d8e2ef', font: { size: 12 }, boxWidth: 14, usePointStyle: true },
        },
        tooltip: {
          backgroundColor: 'rgba(15, 30, 46, 0.95)',
          titleColor: '#c8a84b',
          bodyColor: '#e8eef4',
          borderColor: 'rgba(200, 168, 75, 0.35)',
          borderWidth: 1,
          padding: 12,
          callbacks: {
            label(ctx) {
              const v = ctx.parsed.y;
              const name = ctx.dataset.label || '';
              if (formatY === 'currency') {
                return `${name}: ${Number(v).toLocaleString('en-US')} TZS`;
              }
              if (formatY === 'percent') return `${name}: ${v}%`;
              return `${name}: ${v}`;
            },
          },
        },
        phmValueLabels: { formatY },
      },
      scales: {
        x: {
          ticks: { color: '#9fb2c8', maxRotation: 45, minRotation: 0, font: { size: 11 } },
          grid: { display: false },
        },
        y: {
          beginAtZero: true,
          grace: '12%',
          ticks: yTicks,
          grid: { color: 'rgba(255, 255, 255, 0.06)' },
          border: { display: false },
        },
      },
      animation: { duration: 700, easing: 'easeOutQuart' },
    };
  }

  function showEmpty(canvas, text) {
    const wrap = canvas.parentElement;
    if (wrap) {
      const note = document.createElement('p');
      note.className = 'chart-empty-note';
      note.textContent = text || 'Hakuna data ya kuonyesha bado.';
      wrap.appendChild(note);
    }
    canvas.style.display = 'none';
  }

  function createHistogram(canvas, config) {
    if (!canvas || typeof Chart === 'undefined') return null;

    const labels = config.labels || [];
    const formatY = config.formatY || 'currency';

    // Grouped: config.datasets = [{ label, data, colorScheme }, ...]
    const grouped = Array.isArray(config.datasets) && config.datasets.length > 0;

    let datasets;
    if (grouped) {
      const hasData = config.datasets.some((d) => (d.data || []).some((v) => v));
      if (!labels.length || !hasData) {
        showEmpty(canvas, config.emptyText);
        return null;
      }
      datasets = config.datasets.map((d, i) =>
        makeDataset(d, buildScheme(d.colorScheme, i), true)
      );
    } else {
      const data = config.data || [];
      if (!labels.length || !data.length || !data.some((v) => v)) {
        showEmpty(canvas, config.emptyText);
        return null;
      }
      const scheme = SCHEMES[config.colorScheme] || SCHEMES.teal;
      datasets = [
        makeDataset(
          { datasetLabel: config.datasetLabel || 'Thamani', data },
          scheme,
          false
        ),
      ];
    }

    const showLegend = grouped || !!config.showLegend;

    return new Chart(canvas, {
      type: 'bar',
      data: { labels, datasets },
      options: baseOptions(formatY, showLegend),
      plugins: [valueLabelsPlugin],
    });
  }

  global.ChurchHistogram = {
    create: createHistogram,
    formatTzs,
  };
})(typeof window !== 'undefined' ? window : this);
