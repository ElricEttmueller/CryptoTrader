// src/components/Dashboard.js
import React, { useState, useEffect, useRef } from 'react';
import Chart from './Chart';
import MarketSelector from './MarketSelector';


const Dashboard = () => {
    const [liveData, setLiveData] = useState([]);
    const [selectedPair, setSelectedPair] = useState('BTC-USDT');
    const ws = useRef(null);

    // Connect to WebSocket when selectedPair changes
    useEffect(() => {
        if (ws.current) {
            ws.current.close();
        }

        ws.current = new WebSocket(`ws://localhost:8000/ws/${encodeURIComponent(selectedPair)}`);

        ws.current.onopen = () => {
            console.log('WebSocket connection opened');
        };

        ws.current.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log('Received data:', data);

            setLiveData((prevData) => {
                const newData = [...prevData, data];
                // Limit data to the last 1000 points
                if (newData.length > 1000) {
                    newData.shift();
                }
                return newData;
            });
        };

        ws.current.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        ws.current.onclose = () => {
            console.log('WebSocket connection closed');
        };

        // Cleanup on unmount or pair change
        return () => {
            if (ws.current) {
                ws.current.close();
            }
        };
    }, [selectedPair]);

    // Prepare data for the chart
    const chartData = [
        {
            x: liveData.map((d) => new Date(d.timestamp)),
            y: liveData.map((d) => d.last),
            type: 'scatter',
            mode: 'lines',
            line: { color: 'blue' },
        },
    ];

    const layout = {
        title: `${selectedPair} Live Price`,
        xaxis: { title: 'Time' },
        yaxis: { title: 'Price' },
    };

    const handleMarketSelect = (market) => {
        setSelectedPair(market); // Use the market as is, e.g., 'BTC/USDT'
        setLiveData([]); // Reset data when pair changes
    };
    

    return (
        <div>
            <h2>{selectedPair} Live Chart</h2>
            <MarketSelector onMarketSelect={handleMarketSelect} />
            <Chart data={chartData} layout={layout} />
        </div>
    );
};


export default Dashboard;
