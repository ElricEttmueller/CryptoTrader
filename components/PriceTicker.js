import React, { useState, useEffect } from 'react';
import { fetchLiveData } from '../apiService';

const PriceTicker = ({ market }) => {
    const [price, setPrice] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            const data = await fetchLiveData(market);
            if (data && data.pair_received) {
                setPrice(data.price); // Assume price is part of the API response
            }
        };

        fetchData();
        const interval = setInterval(fetchData, 5000); // Update every 5 seconds

        return () => clearInterval(interval);
    }, [market]);

    return (
        <div>
            <h2>Live Price for {market}: {price ? `$${price}` : 'Loading...'}</h2>
        </div>
    );
};

export default PriceTicker;
