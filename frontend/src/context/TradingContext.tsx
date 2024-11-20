import React, { createContext, useContext, useState, useEffect } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';

interface MarketData {
  currentPrice: number;
  high24h: number;
  low24h: number;
  volume24h: number;
  priceChange24h: number;
}

interface TradingContextType {
  selectedPair: string;
  setSelectedPair: (pair: string) => void;
  marketData: MarketData | null;
  isWebSocketConnected: boolean;
}

const TradingContext = createContext<TradingContextType | undefined>(undefined);

export const TradingProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [selectedPair, setSelectedPair] = useState('BTC-USDT');
  const [marketData, setMarketData] = useState<MarketData | null>(null);

  const { isConnected, lastMessage } = useWebSocket(
    `ws://localhost:8000/ws/${selectedPair.toLowerCase()}`
  );

  useEffect(() => {
    if (lastMessage?.type === 'market_data') {
      setMarketData(lastMessage.data);
    }
  }, [lastMessage]);

  const value = {
    selectedPair,
    setSelectedPair,
    marketData,
    isWebSocketConnected: isConnected,
  };

  return (
    <TradingContext.Provider value={value}>
      {children}
    </TradingContext.Provider>
  );
};

export const useTradingContext = () => {
  const context = useContext(TradingContext);
  if (context === undefined) {
    throw new Error('useTradingContext must be used within a TradingProvider');
  }
  return context;
};
