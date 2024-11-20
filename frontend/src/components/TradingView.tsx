import React, { useEffect, useRef } from 'react';
import { Box } from '@mui/material';

declare global {
  interface Window {
    TradingView: any;
  }
}

const TradingView: React.FC = () => {
  const container = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const script = document.createElement('script');
    script.src = 'https://s3.tradingview.com/tv.js';
    script.async = true;
    script.onload = () => {
      if (container.current && window.TradingView) {
        new window.TradingView.widget({
          container_id: container.current.id,
          symbol: 'BINANCE:BTCUSDT',
          interval: '1D',
          timezone: 'Etc/UTC',
          theme: 'dark',
          style: '1',
          locale: 'en',
          toolbar_bg: '#f1f3f6',
          enable_publishing: false,
          allow_symbol_change: true,
          save_image: false,
          height: '100%',
          width: '100%',
        });
      }
    };
    document.head.appendChild(script);

    return () => {
      if (script.parentNode) {
        script.parentNode.removeChild(script);
      }
    };
  }, []);

  return (
    <Box sx={{ height: '500px', width: '100%' }}>
      <div id="tradingview_widget" ref={container} style={{ height: '100%', width: '100%' }} />
    </Box>
  );
};

export default TradingView;
