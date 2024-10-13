// src/components/MarketSelector.js
import React, { useState, useEffect } from 'react';
import { fetchMarkets } from '../apiService';

const MarketSelector = ({ onMarketSelect }) => {
    const [markets, setMarkets] = useState([]);
    const [selectedMarket, setSelectedMarket] = useState('BTC/USDT');

    useEffect(() => {
        const getMarkets = async () => {
            const availableMarkets = await fetchMarkets();
            setMarkets(availableMarkets);
        };
        getMarkets();
    }, []);

    const handleChange = (e) => {
        const market = e.target.value;
        setSelectedMarket(market);
        if (onMarketSelect) {
            onMarketSelect(market);
        }
    };

    return (
        <div>
            <h3>Select a Market</h3>
            <select value={selectedMarket} onChange={handleChange}>
                {markets.map((market, index) => (
                    <option key={index} value={market}>
                        {market}
                    </option>
                ))}
            </select>
        </div>
    );
};

export default MarketSelector;
