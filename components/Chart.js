// src/components/Chart.js
import React from 'react';
import Plot from 'react-plotly.js';

const Chart = ({ data, layout }) => {
    console.log('Chart component received data:', data);
    console.log('Chart component received layout:', layout);

    return (
        <div>
            <Plot
                data={data}
                layout={{ ...layout, autosize: true }}
                style={{ width: '100%', height: '100%' }}
                config={{ responsive: true, scrollZoom: true }}
                useResizeHandler={true}
            />
        </div>
    );
};

export default Chart;
