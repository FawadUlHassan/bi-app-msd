console.log("Initialization of advanced visualization...");

const parsedRows = window.parsedRowsData || [];
const columns = window.columnsData || [];

//////////////////////
// Data Preview
//////////////////////
function createDataPreview() {
  const container = document.getElementById('dataPreviewContent');
  if (!container) return;

  const maxRows = 10;
  let html = '<table class="table table-sm table-bordered">';
  // Table head
  html += '<thead><tr>';
  columns.forEach(col => {
    html += `<th>${col}</th>`;
  });
  html += '</tr></thead><tbody>';

  // Table body (up to 10 rows)
  for (let i = 0; i < Math.min(parsedRows.length, maxRows); i++) {
    const rowData = parsedRows[i].original;
    html += '<tr>';
    columns.forEach(col => {
      html += `<td>${rowData[col] || ''}</td>`;
    });
    html += '</tr>';
  }
  html += '</tbody></table>';

  container.innerHTML = html;
}
createDataPreview();

//////////////////////
// Filter Management
//////////////////////
const keywordInput = document.getElementById('keyword_filter');
const addFilterBtn = document.getElementById('add_filter_btn');
const filtersContainer = document.getElementById('filters_container');

// Distinct values for each column
const distinctValues = {};
columns.forEach(col => {
  const set = new Set();
  parsedRows.forEach(row => {
    if (row.original[col] != null) {
      set.add(row.original[col].toString());
    }
  });
  distinctValues[col] = Array.from(set);
});

// Add filter row
function addFilterRow() {
  const rowDiv = document.createElement('div');
  rowDiv.className = 'd-flex mb-2 align-items-start flex-wrap';

  const colSelect = document.createElement('select');
  colSelect.className = 'form-select me-2 mb-2';
  colSelect.innerHTML = '<option value="">Select Column</option>';
  columns.forEach(c => {
    const opt = document.createElement('option');
    opt.value = c;
    opt.textContent = c;
    colSelect.appendChild(opt);
  });

  const valSelect = document.createElement('select');
  valSelect.className = 'form-select me-2 mb-2';
  valSelect.style.display = 'none';

  const removeBtn = document.createElement('button');
  removeBtn.type = 'button';
  removeBtn.className = 'btn btn-sm btn-danger mb-2';
  removeBtn.textContent = 'X';

  rowDiv.appendChild(colSelect);
  rowDiv.appendChild(valSelect);
  rowDiv.appendChild(removeBtn);
  filtersContainer.appendChild(rowDiv);

  colSelect.addEventListener('change', () => {
    const selectedCol = colSelect.value;
    if (selectedCol) {
      valSelect.innerHTML = '';
      const vals = distinctValues[selectedCol] || [];
      valSelect.appendChild(new Option("Select Value", ""));
      vals.forEach(v => {
        const opt = document.createElement('option');
        opt.value = v;
        opt.textContent = v;
        valSelect.appendChild(opt);
      });
      valSelect.style.display = 'block';
    } else {
      valSelect.style.display = 'none';
    }
    drawAllCharts();
  });

  valSelect.addEventListener('change', () => {
    drawAllCharts();
  });

  removeBtn.addEventListener('click', () => {
    rowDiv.remove();
    drawAllCharts();
  });
}
addFilterBtn.addEventListener('click', addFilterRow);

function getCurrentFilters() {
  const filterRows = filtersContainer.querySelectorAll('div.d-flex');
  const filters = [];
  filterRows.forEach(row => {
    const selects = row.querySelectorAll('select');
    if (selects.length === 2) {
      const colSelect = selects[0];
      const valSelect = selects[1];
      if (colSelect.value && valSelect.value) {
        filters.push({ column: colSelect.value, value: valSelect.value });
      }
    }
  });
  return filters;
}

//////////////////////
// Chart Management
//////////////////////

// We have 4 charts. For each chart, we have a chartType, X selection, Y selection
const chartConfigs = [
  { 
    typeSelectId: 'chart1_type',
    xSelectorId: 'chart1_x_selector',
    xFieldsId: 'chart1_x_fields',
    ySelectorId: 'chart1_y_selector',
    yFieldsId: 'chart1_y_fields',
    chartDivId: 'chart1',
    xCols: [],
    yCols: []
  },
  { 
    typeSelectId: 'chart2_type',
    xSelectorId: 'chart2_x_selector',
    xFieldsId: 'chart2_x_fields',
    ySelectorId: 'chart2_y_selector',
    yFieldsId: 'chart2_y_fields',
    chartDivId: 'chart2',
    xCols: [],
    yCols: []
  },
  {
    typeSelectId: 'chart3_type',
    xSelectorId: 'chart3_x_selector',
    xFieldsId: 'chart3_x_fields',
    ySelectorId: 'chart3_y_selector',
    yFieldsId: 'chart3_y_fields',
    chartDivId: 'chart3',
    xCols: [],
    yCols: []
  },
  {
    typeSelectId: 'chart4_type',
    xSelectorId: 'chart4_x_selector',
    xFieldsId: 'chart4_x_fields',
    ySelectorId: 'chart4_y_selector',
    yFieldsId: 'chart4_y_fields',
    chartDivId: 'chart4',
    xCols: [],
    yCols: []
  },
];

// Attach events for each chart config
chartConfigs.forEach(cfg => {
  // Fill the X and Y dropdown with columns
  const xSelector = document.getElementById(cfg.xSelectorId);
  const ySelector = document.getElementById(cfg.ySelectorId);

  columns.forEach(col => {
    const optX = document.createElement('option');
    optX.value = col;
    optX.textContent = col;
    xSelector.appendChild(optX);

    const optY = document.createElement('option');
    optY.value = col;
    optY.textContent = col;
    ySelector.appendChild(optY);
  });

  // When user picks a new X field, we create a "pill" and add it to xCols
  xSelector.addEventListener('change', () => {
    const val = xSelector.value;
    if (val) {
      cfg.xCols.push(val);
      addPill(cfg.xFieldsId, val, cfg.xCols);
      xSelector.value = '';
      drawAllCharts();
    }
  });

  // Same for Y
  ySelector.addEventListener('change', () => {
    const val = ySelector.value;
    if (val) {
      cfg.yCols.push(val);
      addPill(cfg.yFieldsId, val, cfg.yCols);
      ySelector.value = '';
      drawAllCharts();
    }
  });

  // Also handle chart type changes
  const typeSelect = document.getElementById(cfg.typeSelectId);
  typeSelect.addEventListener('change', () => {
    drawAllCharts();
  });
});

// Add a "pill" to the given container. On remove, remove from array.
function addPill(containerId, val, arr) {
  const container = document.getElementById(containerId);
  const pill = document.createElement('span');
  pill.className = 'badge bg-primary me-2 mb-2 d-flex align-items-center';
  pill.style.cursor = 'pointer';

  const text = document.createElement('span');
  text.textContent = val;
  pill.appendChild(text);

  const removeIcon = document.createElement('span');
  removeIcon.textContent = ' ✕';
  removeIcon.style.marginLeft = '5px';
  removeIcon.addEventListener('click', () => {
    // Remove from array
    const idx = arr.indexOf(val);
    if (idx >= 0) arr.splice(idx, 1);
    container.removeChild(pill);
    drawAllCharts();
  });
  pill.appendChild(removeIcon);

  container.appendChild(pill);
}

// The main draw function for each chart
function drawAllCharts() {
  const filters = getCurrentFilters();
  const keyword = keywordInput.value.toLowerCase();

  let filtered = parsedRows;
  // Keyword filter on any X-col
  if (keyword) {
    // We'll unify all X columns from all charts (but that might be weird).
    // Instead, let's not unify. The user said "I want all filters to refine the data"
    // So we do a single approach: we check if ANY row's original col includes it? 
    // This can get complex. We'll just do it in a single approach:
    filtered = filtered.filter(row => {
      // If there's ANY X col across ANY chart? We'll do a simpler approach: 
      // If any original field includes the keyword => keep. 
      // Or if you want specifically x-axis from some chart? 
      // We'll do a global approach for simplicity:
      return Object.keys(row.original).some(c => {
        const val = row.original[c];
        return val && val.toString().toLowerCase().includes(keyword);
      });
    });
  }

  // Apply column-value filters
  filters.forEach(f => {
    filtered = filtered.filter(row => {
      const colVal = row.original[f.column];
      return colVal != null && colVal.toString() === f.value;
    });
  });

  // For each chart, we gather the config and produce traces
  chartConfigs.forEach(cfg => {
    drawSingleChart(cfg, filtered);
  });
}

function drawSingleChart(cfg, filteredRows) {
  const chartTypeSelect = document.getElementById(cfg.typeSelectId);
  const chartType = chartTypeSelect.value; // bar, line, scatter, pie

  const isDarkMode = document.body.classList.contains('dark-mode');
  const layout = {
    paper_bgcolor: isDarkMode ? '#333333' : '#ffffff',
    plot_bgcolor: isDarkMode ? '#333333' : '#ffffff',
    font: { color: isDarkMode ? '#ffffff' : '#000000' },
    margin: { t: 30, r: 10, b: 50, l: 50 },
  };

  const xCols = cfg.xCols;
  const yCols = cfg.yCols;

  const traces = [];

  if (!xCols.length || !yCols.length) {
    const cDiv = document.getElementById(cfg.chartDivId);
    cDiv.innerHTML = "<p class='text-muted'>No X/Y fields selected.</p>";
    return;
  }

  // If pie => we only use the first X col and first Y col
  // If bar/line/scatter => for each X col, for each Y col => a trace
  if (chartType === 'pie') {
    const xCol = xCols[0];
    const yCol = yCols[0];

    // Sum up numeric values by category
    const categoryMap = {};
    filteredRows.forEach(row => {
      const cat = row.original[xCol];
      const val = row.numeric[yCol];
      if (cat && typeof val === 'number') {
        categoryMap[cat] = (categoryMap[cat] || 0) + val;
      }
    });

    const labels = Object.keys(categoryMap);
    const values = Object.values(categoryMap);

    if (labels.length) {
      traces.push({
        labels,
        values,
        type: 'pie',
        hoverinfo: 'label+value+percent',
        textinfo: 'value',
      });
    }
  } else {
    yCols.forEach(yCol => {
      xCols.forEach(xCol => {
        const x_data = [];
        const y_data = [];
        const hover_text = [];

        filteredRows.forEach(row => {
          const xVal = row.original[xCol];
          const yVal = row.numeric[yCol];
          if (xVal != null && typeof yVal === 'number') {
            x_data.push(xVal);
            y_data.push(yVal);
            hover_text.push(`${xCol}: ${xVal}<br>${yCol}: ${yVal}`);
          }
        });

        if (x_data.length) {
          let trace = {
            x: x_data,
            y: y_data,
            hovertext: hover_text,
            hoverinfo: 'text',
            name: `${yCol} vs ${xCol}`
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
    const cDiv = document.getElementById(cfg.chartDivId);
    cDiv.innerHTML = "<p>No valid data for these selections.</p>";
    return;
  }

  // Build final layout
  layout.title = chartType.toUpperCase() + ` Chart`;
  const cDiv = document.getElementById(cfg.chartDivId);
  Plotly.newPlot(cDiv, traces, layout, { responsive: true });
}

// On load, let's do a single draw
drawAllCharts();
console.log("Advanced Visualization init complete.");

