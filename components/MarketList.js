// src/components/MarketList.js
import React, { useEffect, useState } from 'react';
import { fetchMarkets } from '../apiService';

const MarketList = () => {
    const [markets, setMarkets] = useState([]);

    useEffect(() => {
        const getMarkets = async () => {
            const data = await fetchMarkets();
            setMarkets(data);
        };
        getMarkets();
    }, []);

    return (
        <div>
            <h2>Available Markets</h2>
            <ul>
                {markets.map((market, index) => (
                    <li key={index}>{market}</li>
                ))}
            </ul>
        </div>
    );
};

export default MarketList;
