import React, { useEffect, useState } from 'react';
import { fetchMarkets } from '../apiService';

function Markets() {
    const [markets, setMarkets] = useState([]);  // Original list of markets
    const [filteredMarkets, setFilteredMarkets] = useState([]);  // Filtered and sorted markets
    const [searchQuery, setSearchQuery] = useState('');  // Search query state
    const [sortOrder, setSortOrder] = useState('asc');  // Sorting order
    const [loading, setLoading] = useState(true);  // Loading state
    const [error, setError] = useState(null);  // Error state
    const [visibleCount, setVisibleCount] = useState(10);  // Number of markets to display initially

    // Fetch markets from the API once on component mount
    useEffect(() => {
        const getMarkets = async () => {
            try {
                const data = await fetchMarkets();
                if (data && Array.isArray(data)) {
                    setMarkets(data);
                    setFilteredMarkets(data);  // Initially, show all markets
                    console.log("Markets fetched:", data);
                } else {
                    setError("Invalid markets data format");
                }
            } catch (error) {
                console.error("Error fetching markets:", error);
                setError("Failed to load markets");
            } finally {
                setLoading(false);
            }
        };

        getMarkets();
    }, []);

    // Handle search input change and filter the markets based on the search query
    useEffect(() => {
        const filtered = markets.filter((market) =>
            market.toLowerCase().includes(searchQuery.toLowerCase())
        );
        setFilteredMarkets(filtered);  // Update filtered markets based on search query
        setVisibleCount(10);  // Reset the visible count when searching
    }, [searchQuery, markets]);

    // Sorting logic
    const handleSort = (order) => {
        const sortedMarkets = [...filteredMarkets].sort((a, b) => {
            return order === 'asc' ? a.localeCompare(b) : b.localeCompare(a);
        });
        setSortOrder(order);
        setFilteredMarkets(sortedMarkets);  // Update the filtered markets after sorting
    };

    // Function to load more markets
    const loadMore = () => {
        setVisibleCount((prevCount) => prevCount + 10);  // Show 10 more markets each time
    };

    if (loading) {
        return <p>Loading markets...</p>;
    }

    if (error) {
        return <p>{error}</p>;
    }

    return (
        <div>
            <h2>Available Markets</h2>

            {/* Search bar */}
            <input
                type="text"
                placeholder="Search markets..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}  // Update search query
                style={{ marginBottom: '20px', padding: '10px', width: '100%' }}
            />

            {/* Sorting buttons */}
            <div>
                <button onClick={() => handleSort('asc')}>Sort A-Z</button>
                <button onClick={() => handleSort('desc')}>Sort Z-A</button>
            </div>

            {/* Display limited filtered markets */}
            <ul>
                {filteredMarkets.slice(0, visibleCount).map((market, index) => (
                    <li key={index}>{market}</li>
                ))}
            </ul>

            {/* Show Load More button if there are more markets to display */}
            {visibleCount < filteredMarkets.length && (
                <button onClick={loadMore} style={{ marginTop: '20px' }}>
                    Load More
                </button>
            )}
        </div>
    );
}

export default Markets;
