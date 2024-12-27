// my_bi_tool/static/js/visualization.js

console.log("Enhanced Visualization with pagination + chart saving...");

// Global data
const parsedRows = window.parsedRowsData || [];
const columns = window.columnsData || [];
const dsSummaryData = window.dsSummaryData || {};
const currentUploadId = window.currentUploadId || 0;

// Pagination state
let currentPage = 1;
const PAGE_SIZE = 10; // Show 10 rows per page

// 1. Show DS summary
function showDSSummary() {
  const dsSummaryEl = document.getElementById('dsSummary');
  if (!dsSummaryEl) return;

  if (!Object.keys(dsSummaryData).length) {
    dsSummaryEl.innerHTML = "<p class='text-muted'>No numeric column stats available.</p>";
    return;
  }

  let html = '<ul class="list-group">';
  for (let col in dsSummaryData) {
    const st = dsSummaryData[col];
    html += `<li class="list-group-item">
               <strong>${col}</strong><br>
               Count: ${st.count}<br>
               Min: ${st.min}<br>
               Max: ${st.max}<br>
               Mean: ${st.mean.toFixed(2)}<br>
               Distinct: ${st.distinct}
             </li>`;
  }
  html += '</ul>';
  dsSummaryEl.innerHTML = html;
}
showDSSummary();

// 2. Data Preview (paginated)
function createDataPreview(page) {
  const dataPreviewContent = document.getElementById('dataPreviewContent');
  if (!dataPreviewContent) return;

  const totalRows = parsedRows.length;
  const totalPages = Math.ceil(totalRows / PAGE_SIZE);

  if (page < 1) page = 1;
  if (page > totalPages) page = totalPages || 1;

  currentPage = page;

  const startIndex = (currentPage - 1) * PAGE_SIZE;
  const endIndex = startIndex + PAGE_SIZE;
  const displayRows = parsedRows.slice(startIndex, endIndex);

  let html = '<table class="table table-bordered table-sm"><thead><tr>';
  columns.forEach(col => {
    html += `<th>${col}</th>`;
  });
  html += '</tr></thead><tbody>';

  displayRows.forEach(pr => {
    const row = pr.original;
    html += '<tr>';
    columns.forEach(col => {
      html += `<td>${row[col] !== undefined ? row[col] : ''}</td>`;
    });
    html += '</tr>';
  });

  html += '</tbody></table>';
  dataPreviewContent.innerHTML = html;

  const pageNumberEl = document.getElementById('pageNumber');
  if (pageNumberEl) {
    pageNumberEl.value = `${currentPage} / ${totalPages || 1}`;
  }
}

const prevBtn = document.getElementById('prevPage');
const nextBtn = document.getElementById('nextPage');
if (prevBtn && nextBtn) {
  prevBtn.addEventListener('click', () => {
    createDataPreview(currentPage - 1);
  });
  nextBtn.addEventListener('click', () => {
    createDataPreview(currentPage + 1);
  });
}
// Initialize preview page
createDataPreview(1);

// 3. Charts
const chartConfigs = [
  {
    chartNum: 1,
    titleId: 'chart1_title',
    editIconId: 'chart1_edit',
    titleEditId: 'chart1_title_edit',
    titleInputId: 'chart1_title_input',
    titleConfirmId: 'chart1_title_confirm',
    titleCancelId: 'chart1_title_cancel',
    typeId: 'chart1_type',
    xFieldsId: 'chart1_x_fields',
    xSelectorId: 'chart1_x_selector',
    xKeywordId: 'chart1_xkeyword',
    yFieldsId: 'chart1_y_fields',
    ySelectorId: 'chart1_y_selector',
    yKeywordId: 'chart1_ykeyword',
    chartDivId: 'chart1',
    xCols: [],
    yCols: [],
    chartName: 'Chart 1'
  },
  {
    chartNum: 2,
    titleId: 'chart2_title',
    editIconId: 'chart2_edit',
    titleEditId: 'chart2_title_edit',
    titleInputId: 'chart2_title_input',
    titleConfirmId: 'chart2_title_confirm',
    titleCancelId: 'chart2_title_cancel',
    typeId: 'chart2_type',
    xFieldsId: 'chart2_x_fields',
    xSelectorId: 'chart2_x_selector',
    xKeywordId: 'chart2_xkeyword',
    yFieldsId: 'chart2_y_fields',
    ySelectorId: 'chart2_y_selector',
    yKeywordId: 'chart2_ykeyword',
    chartDivId: 'chart2',
    xCols: [],
    yCols: [],
    chartName: 'Chart 2'
  },
  {
    chartNum: 3,
    titleId: 'chart3_title',
    editIconId: 'chart3_edit',
    titleEditId: 'chart3_title_edit',
    titleInputId: 'chart3_title_input',
    titleConfirmId: 'chart3_title_confirm',
    titleCancelId: 'chart3_title_cancel',
    typeId: 'chart3_type',
    xFieldsId: 'chart3_x_fields',
    xSelectorId: 'chart3_x_selector',
    xKeywordId: 'chart3_xkeyword',
    yFieldsId: 'chart3_y_fields',
    ySelectorId: 'chart3_y_selector',
    yKeywordId: 'chart3_ykeyword',
    chartDivId: 'chart3',
    xCols: [],
    yCols: [],
    chartName: 'Chart 3'
  },
  {
    chartNum: 4,
    titleId: 'chart4_title',
    editIconId: 'chart4_edit',
    titleEditId: 'chart4_title_edit',
    titleInputId: 'chart4_title_input',
    titleConfirmId: 'chart4_title_confirm',
    titleCancelId: 'chart4_title_cancel',
    typeId: 'chart4_type',
    xFieldsId: 'chart4_x_fields',
    xSelectorId: 'chart4_x_selector',
    xKeywordId: 'chart4_xkeyword',
    yFieldsId: 'chart4_y_fields',
    ySelectorId: 'chart4_y_selector',
    yKeywordId: 'chart4_ykeyword',
    chartDivId: 'chart4',
    xCols: [],
    yCols: [],
    chartName: 'Chart 4'
  }
];

function createPill(value, arrayRef, containerEl) {
  const pill = document.createElement('span');
  pill.className = 'badge bg-primary me-2 mb-2 d-flex align-items-center';
  pill.style.cursor = 'pointer';
  pill.textContent = value + ' ';

  const removeIcon = document.createElement('span');
  removeIcon.textContent = '✕';
  removeIcon.style.marginLeft = '5px';
  removeIcon.addEventListener('click', () => {
    const idx = arrayRef.indexOf(value);
    if (idx >= 0) arrayRef.splice(idx, 1);
    containerEl.removeChild(pill);
    drawAllCharts();
  });
  pill.appendChild(removeIcon);

  return pill;
}

// Setup chart config interactions
chartConfigs.forEach(cfg => {
  const titleEl = document.getElementById(cfg.titleId);
  const editIcon = document.getElementById(cfg.editIconId);
  const titleEditDiv = document.getElementById(cfg.titleEditId);
  const titleInput = document.getElementById(cfg.titleInputId);
  const confirmBtn = document.getElementById(cfg.titleConfirmId);
  const cancelBtn = document.getElementById(cfg.titleCancelId);

  editIcon.addEventListener('click', () => {
    titleEditDiv.style.display = 'flex';
    titleInput.value = cfg.chartName;
  });
  confirmBtn.addEventListener('click', () => {
    cfg.chartName = titleInput.value || cfg.chartName;
    titleEl.textContent = cfg.chartName;
    titleEditDiv.style.display = 'none';
    drawAllCharts();
  });
  cancelBtn.addEventListener('click', () => {
    titleEditDiv.style.display = 'none';
  });

  // chart type
  const typeSelect = document.getElementById(cfg.typeId);
  typeSelect.addEventListener('change', () => drawAllCharts());

  // X fields
  const xSelector = document.getElementById(cfg.xSelectorId);
  const xFieldsDiv = document.getElementById(cfg.xFieldsId);
  xSelector.addEventListener('change', () => {
    const val = xSelector.value;
    if (val) {
      cfg.xCols.push(val);
      xFieldsDiv.appendChild(createPill(val, cfg.xCols, xFieldsDiv));
      xSelector.value = '';
      drawAllCharts();
    }
  });

  // Y fields
  const ySelector = document.getElementById(cfg.ySelectorId);
  const yFieldsDiv = document.getElementById(cfg.yFieldsId);
  ySelector.addEventListener('change', () => {
    const val = ySelector.value;
    if (val) {
      cfg.yCols.push(val);
      yFieldsDiv.appendChild(createPill(val, cfg.yCols, yFieldsDiv));
      ySelector.value = '';
      drawAllCharts();
    }
  });

  // keywords
  document.getElementById(cfg.xKeywordId).addEventListener('input', () => drawAllCharts());
  document.getElementById(cfg.yKeywordId).addEventListener('input', () => drawAllCharts());
});

// Populate selectors
function populateSelectors() {
  chartConfigs.forEach(cfg => {
    const xSel = document.getElementById(cfg.xSelectorId);
    const ySel = document.getElementById(cfg.ySelectorId);
    columns.forEach(col => {
      let optX = document.createElement('option');
      optX.value = col;
      optX.textContent = col;
      xSel.appendChild(optX);

      let optY = document.createElement('option');
      optY.value = col;
      optY.textContent = col;
      ySel.appendChild(optY);
    });
  });
}
populateSelectors();

// Draw all charts
function drawAllCharts() {
  chartConfigs.forEach(cfg => {
    drawSingleChart(cfg);
  });
}

function drawSingleChart(cfg) {
  const chartType = document.getElementById(cfg.typeId).value;
  const chartDiv = document.getElementById(cfg.chartDivId);
  const chartName = document.getElementById(cfg.titleId).textContent;
  const isDarkMode = document.body.classList.contains('dark-mode');

  const layout = {
    title: chartName,
    paper_bgcolor: isDarkMode ? '#333333' : '#ffffff',
    plot_bgcolor: isDarkMode ? '#333333' : '#ffffff',
    font: { color: isDarkMode ? '#ffffff' : '#000000' },
    margin: { t: 40, r: 20, b: 60, l: 60 }
  };

  const xCols = cfg.xCols;
  const yCols = cfg.yCols;
  const xKw = document.getElementById(cfg.xKeywordId).value.trim().toLowerCase();
  const yKw = document.getElementById(cfg.yKeywordId).value.trim().toLowerCase();

  if (!xCols.length || !yCols.length) {
    chartDiv.innerHTML = "<p class='text-muted'>No X/Y fields selected.</p>";
    return;
  }

  // Filter
  const filtered = parsedRows.filter(r => {
    let passX = true;
    if (xKw) {
      passX = xCols.some(xc => {
        const val = r.original[xc];
        return val && val.toString().toLowerCase().includes(xKw);
      });
    }
    let passY = true;
    if (yKw) {
      passY = yCols.some(yc => {
        const val = r.original[yc];
        return val && val.toString().toLowerCase().includes(yKw);
      });
    }
    return passX && passY;
  });

  const traces = [];
  if (chartType === 'pie') {
    // single X -> labels, single Y -> values
    const xCol = xCols[0];
    const yCol = yCols[0];
    const catMap = {};
    filtered.forEach(r => {
      const lab = r.original[xCol];
      const val = r.processed[yCol];
      if (lab && typeof val === 'number') {
        catMap[lab] = (catMap[lab] || 0) + val;
      }
    });
    const labels = Object.keys(catMap);
    const values = Object.values(catMap);
    if (labels.length) {
      traces.push({
        labels,
        values,
        type: 'pie',
        hoverinfo: 'label+value+percent',
        textinfo: 'value'
      });
    }
  } else {
    // bar/line/scatter
    yCols.forEach(yc => {
      xCols.forEach(xc => {
        const xData = [];
        const yData = [];
        const hoverText = [];
        filtered.forEach(r => {
          const xv = r.original[xc];
          const yv = r.processed[yc];
          if (xv && typeof yv === 'number') {
            xData.push(xv);
            yData.push(yv);
            hoverText.push(`${xc}: ${xv}<br>${yc}: ${yv}`);
          }
        });
        if (xData.length) {
          let trace = {
            x: xData,
            y: yData,
            hovertext: hoverText,
            hoverinfo: 'text',
            name: `${yc} vs ${xc}`
          };
          switch (chartType) {
            case 'bar':
              trace.type = 'bar';
              break;
            case 'line':
              trace.type = 'scatter';
              trace.mode = 'lines+markers';
              break;
            case 'scatter':
              trace.type = 'scatter';
              trace.mode = 'markers';
              break;
          }
          traces.push(trace);
        }
      });
    });
  }

  if (!traces.length) {
    chartDiv.innerHTML = "<p>No valid data for these selections.</p>";
    return;
  }

  Plotly.newPlot(chartDiv, traces, layout, { responsive: true });
}

// Initial draw
drawAllCharts();

// Toggling data preview
const dataPreviewToggle = document.getElementById('dataPreviewToggle');
const dataPreviewSection = document.getElementById('dataPreviewSection');
let previewExpanded = false;
if (dataPreviewToggle && dataPreviewSection) {
  dataPreviewToggle.addEventListener('click', () => {
    previewExpanded = !previewExpanded;
    dataPreviewSection.style.display = previewExpanded ? 'block' : 'none';
    dataPreviewToggle.textContent = previewExpanded ? '▲' : '▼';
  });
}

// ------------------- SAVE CHART LOGIC -------------------
const saveChartBtn = document.getElementById('saveChartBtn');
if (saveChartBtn) {
  saveChartBtn.addEventListener('click', () => {
    // We'll just save the first chart's config as an example,
    // or gather all 4 if you want to store multiple. 
    // For demonstration, let's just store "Chart 1" config:

    const c1 = chartConfigs[0]; // or whichever chart we want to save
    const chartData = {
      chartTitle: c1.chartName,
      chartType: document.getElementById(c1.typeId).value,
      xCols: c1.xCols,
      yCols: c1.yCols,
      xKeyword: document.getElementById(c1.xKeywordId).value.trim().toLowerCase(),
      yKeyword: document.getElementById(c1.yKeywordId).value.trim().toLowerCase()
    };

    fetch(`/data/save_chart/${currentUploadId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(chartData)
    })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        alert(`Chart saved! ID: ${data.chart_id}`);
      } else {
        alert(`Error saving chart: ${data.error || 'Unknown error'}`);
      }
    })
    .catch(err => {
      console.error(err);
      alert('Failed to save chart. Check console for details.');
    });
  });
}

console.log("Visualization with chart saving initialized.");

