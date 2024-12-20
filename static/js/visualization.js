const parsedRows = window.parsedRowsData;
const columns = window.columnsData;

const xSelect = document.getElementById('x_col');
const ySelect = document.getElementById('y_col');
const formatSelect = document.getElementById('format_option');
const keywordInput = document.getElementById('keyword_filter');

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

function getFilteredRows() {
    const keyword = keywordInput.value.toLowerCase();
    const x_col = xSelect.value;

    if (!keyword) {
        return parsedRows;
    }

    return parsedRows.filter(row => {
        const val = (row.original[x_col] || '').toString().toLowerCase();
        return val.includes(keyword);
    });
}

function drawChart() {
    const filteredRows = getFilteredRows();
    const x_col = xSelect.value;
    const y_col = ySelect.value;
    const chosenFormat = formatSelect.value;

    const x_data = [];
    const y_data = [];
    const hover_text = [];

    for (const row of filteredRows) {
        const orig = row.original;
        const num = row.numeric;

        let val = num[y_col];
        if (typeof val === 'number') {
            x_data.push(orig[x_col]);
            let formattedValue;
            if (chosenFormat === 'PKR') {
                formattedValue = `PKR ${val.toLocaleString()}`;
            } else if (chosenFormat === '%') {
                formattedValue = `${val}%`;
            } else {
                formattedValue = val.toLocaleString();
            }

            hover_text.push(`${x_col}: ${orig[x_col]}<br>${y_col}: ${formattedValue}`);
            y_data.push(val);
        }
    }

    const trace = {
        x: x_data,
        y: y_data,
        type: 'bar',
        hoverinfo: 'text',
        hovertext: hover_text
    };

    let tickPrefix = '';
    let tickSuffix = '';
    if (chosenFormat === 'PKR') tickPrefix = 'PKR ';
    if (chosenFormat === '%') tickSuffix = '%';

    const layout = {
        title: `Visualization: ${x_col} vs ${y_col}`,
        xaxis: { title: x_col },
        yaxis: { 
            title: y_col,
            tickprefix: tickPrefix,
            ticksuffix: tickSuffix
        }
    };

    Plotly.newPlot('chart', [trace], layout);
}

drawChart();

xSelect.addEventListener('change', drawChart);
ySelect.addEventListener('change', drawChart);
formatSelect.addEventListener('change', drawChart);
keywordInput.addEventListener('input', drawChart);

