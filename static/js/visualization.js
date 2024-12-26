console.log("Initializing visualization.js...");

const parsedRows = window.parsedRowsData;
const columns = window.columnsData;

const xSelect = document.getElementById('x_col');
const ySelect = document.getElementById('y_col');
const keywordInput = document.getElementById('keyword_filter');
const addFilterBtn = document.getElementById('add_filter_btn');
const filtersContainer = document.getElementById('filters_container');

// Populate dropdowns with columns
columns.forEach(col => {
    const xOption = document.createElement('option');
    xOption.value = col;
    xOption.textContent = col;
    xSelect.appendChild(xOption);

    const yOption = document.createElement('option');
    yOption.value = col;
    yOption.textContent = col;
    ySelect.appendChild(yOption);
});

if (columns.length > 0) xSelect.value = columns[0];
if (columns.length > 1) ySelect.value = columns[1];

// Compute distinct values for each column to support multiple filters
const distinctValues = {};
columns.forEach(col => {
    const set = new Set();
    parsedRows.forEach(row => {
        if (row && row.original && row.original[col] != null) {
            set.add(row.original[col].toString());
        }
    });
    distinctValues[col] = Array.from(set);
});
console.log("distinctValues:", distinctValues);

// Function to read current filters from the UI
function getCurrentFilters() {
    const filters = [];
    const rows = filtersContainer.querySelectorAll('div.d-flex');
    rows.forEach(row => {
        const selects = row.querySelectorAll('select');
        if (selects.length === 2) {
            const colSelect = selects[0];
            const valSelect = selects[1];
            const col = colSelect.value;
            const val = valSelect.value;
            if (col && val) {
                filters.push({ column: col, value: val });
            }
        }
    });
    return filters;
}

// Filter rows based on keyword and additional filters
function getFilteredRows() {
    const keyword = keywordInput.value.toLowerCase();
    const x_col = xSelect.value;
    const activeFilters = getCurrentFilters();

    // Start with all rows
    let filtered = parsedRows;

    // Apply keyword filter
    if (keyword && x_col) {
        filtered = filtered.filter(row => {
            const val = (row.original[x_col] || '').toString().toLowerCase();
            return val.includes(keyword);
        });
    }

    // Apply additional column-value filters
    for (const f of activeFilters) {
        filtered = filtered.filter(row => {
            const colVal = row.original[f.column];
            return colVal != null && colVal.toString() === f.value;
        });
    }

    return filtered;
}

// Draw the chart with filtered rows
function drawChart() {
    const filteredRows = getFilteredRows();
    const x_col = xSelect.value;
    const y_col = ySelect.value;

    const x_data = [];
    const y_data = [];
    const hover_text = [];

    for (const row of filteredRows) {
        const orig = row.original;
        const num = row.numeric;

        // Use x_col from original, y_col from numeric
        let val = num[y_col];
        if (typeof val === 'number') {
            x_data.push(orig[x_col]);
            y_data.push(val);

            // Build hover text
            hover_text.push(`${x_col}: ${orig[x_col]}<br>${y_col}: ${val}`);
        }
    }

    if (x_data.length === 0 || y_data.length === 0) {
        document.getElementById('chart').innerHTML = "<p>No valid data available for the selected columns after filtering.</p>";
        return;
    }

    const trace = {
        x: x_data,
        y: y_data,
        type: 'bar',
        hoverinfo: 'text',
        hovertext: hover_text
    };

    const layout = {
        title: `Visualization: ${x_col} vs ${y_col}`,
        xaxis: { title: x_col },
        yaxis: { title: y_col }
    };

    Plotly.newPlot('chart', [trace], layout);
}

// Add filter row logic
function addFilterRow() {
    const filterRow = document.createElement('div');
    filterRow.className = 'd-flex mb-2 align-items-start flex-wrap';

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

    filterRow.appendChild(colSelect);
    filterRow.appendChild(valSelect);
    filterRow.appendChild(removeBtn);
    filtersContainer.appendChild(filterRow);

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
        drawChart();
    });

    valSelect.addEventListener('change', () => {
        drawChart();
    });

    removeBtn.addEventListener('click', () => {
        filterRow.remove();
        drawChart();
    });
}

// Event listeners
xSelect.addEventListener('change', drawChart);
ySelect.addEventListener('change', drawChart);
keywordInput.addEventListener('input', drawChart);
addFilterBtn.addEventListener('click', () => {
    addFilterRow();
});

// Initial chart
drawChart();
console.log("Initialization complete.");

