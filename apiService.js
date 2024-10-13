// src/apiService.js
import axios from 'axios';

const api = axios.create({
    baseURL: 'http://localhost:8000',  // Ensure the base URL is correct
});


export async function fetchMarkets() {
    try {
        const response = await api.get('/markets');
        console.log("Full response from backend /markets:", response);  // Log the full response object
        console.log("Available markets in response:", response.data.available_markets);  // Log specifically the markets data
        return response.data.available_markets || [];  // Ensure the response is an array, or return an empty array
    } catch (error) {
        console.error("Error fetching markets:", error);
        return [];  // Return an empty array in case of an error
    }
}







export const fetchLiveData = async (pair) => {
    try {
        const response = await api.get(`/live-data/${encodeURIComponent(pair)}`);
        return response.data;
    } catch (error) {
        console.error('Error fetching live data:', error);
        return null;
    }
};

// Corrected fetchHistoricalData function in apiService.js
export const fetchHistoricalData = async (pair, timeframe, startDate, endDate) => {
    // Remove the '/' in the pair symbol (e.g., BTC/USDT becomes BTCUSDT)
    const formattedPair = pair.replace('/', '');

    try {
        const response = await api.get(`/historical-data/${encodeURIComponent(formattedPair)}`, {
            params: {
                timeframe,
                start_date: startDate,
                end_date: endDate,
            },
        });
        console.log("Historical data response:", response.data);  // Log the response for debugging
        return response.data;  // Return the data from the backend
    } catch (error) {
        console.error('Error fetching historical data:', error);  // Handle error
        return null;
    }
};



