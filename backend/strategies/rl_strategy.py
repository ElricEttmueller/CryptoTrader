import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from .base_strategy import BaseStrategy
import gym
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
import ta

class TradingEnvironment(gym.Env):
    """
    Custom Trading Environment that follows gym interface
    """
    def __init__(self, data: pd.DataFrame, initial_balance: float = 10000):
        super(TradingEnvironment, self).__init__()
        
        self.data = data
        self.initial_balance = initial_balance
        self.current_step = 0
        self.balance = initial_balance
        self.position = 0
        
        # Action space: -1 (sell), 0 (hold), 1 (buy)
        self.action_space = gym.spaces.Discrete(3)
        
        # Observation space: price data and indicators
        self.observation_space = gym.spaces.Box(
            low=-np.inf, high=np.inf, shape=(10,), dtype=np.float32
        )
    
    def _get_observation(self) -> np.array:
        """Get the current state observation"""
        obs = np.array([
            self.data['returns'].iloc[self.current_step],
            self.data['rsi'].iloc[self.current_step],
            self.data['macd'].iloc[self.current_step],
            self.data['atr'].iloc[self.current_step],
            self.data['ma_ratio'].iloc[self.current_step],
            self.data['volatility'].iloc[self.current_step],
            self.data['volume_ratio'].iloc[self.current_step],
            self.balance / self.initial_balance,
            self.position,
            self.data['close'].iloc[self.current_step] / self.data['close'].iloc[0]
        ])
        return obs.astype(np.float32)
    
    def step(self, action: int) -> Tuple[np.array, float, bool, dict]:
        """Execute one step in the environment"""
        current_price = self.data['close'].iloc[self.current_step]
        
        # Convert action from [0,1,2] to [-1,0,1]
        action = action - 1
        
        # Calculate reward
        reward = 0
        done = False
        
        if action == 1 and self.position <= 0:  # Buy
            self.position = 1
            reward = -0.0001  # Small transaction cost
        elif action == -1 and self.position >= 0:  # Sell
            if self.position > 0:
                price_diff = current_price - self.data['close'].iloc[self.current_step - 1]
                reward = price_diff / current_price  # Reward is the return
            self.position = -1
            reward -= 0.0001  # Transaction cost
        
        # Update balance based on position
        if self.position != 0:
            price_diff = self.data['close'].iloc[self.current_step] - self.data['close'].iloc[self.current_step - 1]
            self.balance += self.position * price_diff
        
        # Move to next step
        self.current_step += 1
        if self.current_step >= len(self.data) - 1:
            done = True
        
        return self._get_observation(), reward, done, {}
    
    def reset(self):
        """Reset the environment"""
        self.current_step = 0
        self.balance = self.initial_balance
        self.position = 0
        return self._get_observation()

class RLTradingStrategy(BaseStrategy):
    def __init__(self, lookback_period: int = 20):
        """
        Initialize RL trading strategy
        """
        super().__init__('RL Trading Strategy')
        self.lookback_period = lookback_period
        self.model = None
        
    def prepare_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare data for RL model
        """
        df = data.copy()
        
        # Calculate features
        df['returns'] = df['close'].pct_change()
        df['rsi'] = ta.momentum.rsi(df['close'], window=14)
        df['macd'] = ta.trend.macd_diff(df['close'])
        df['atr'] = ta.volatility.average_true_range(df['high'], df['low'], df['close'])
        df['sma_20'] = ta.trend.sma_indicator(df['close'], window=20)
        df['sma_50'] = ta.trend.sma_indicator(df['close'], window=50)
        df['ma_ratio'] = df['sma_20'] / df['sma_50']
        df['volatility'] = df['returns'].rolling(window=20).std()
        df['volume_ma'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma']
        
        return df.dropna()
    
    def train_model(self, data: pd.DataFrame, total_timesteps: int = 10000) -> None:
        """
        Train the RL model
        """
        # Prepare data
        df = self.prepare_data(data)
        if df.empty:
            return
        
        # Create environment
        env = DummyVecEnv([lambda: TradingEnvironment(df)])
        
        # Initialize and train model
        self.model = PPO('MlpPolicy', env, verbose=1)
        self.model.learn(total_timesteps=total_timesteps)
    
    def generate_signals(self, data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals using RL model
        """
        if self.model is None:
            return pd.Series(0, index=data.index)
        
        try:
            # Prepare data
            df = self.prepare_data(data)
            if df.empty:
                return pd.Series(0, index=data.index)
            
            # Create environment
            env = TradingEnvironment(df)
            
            # Generate signals
            signals = pd.Series(0, index=df.index)
            obs = env.reset()
            
            for i in range(len(df)):
                action, _ = self.model.predict(obs, deterministic=True)
                signals.iloc[i] = action - 1  # Convert [0,1,2] to [-1,0,1]
                obs, _, done, _ = env.step(action)
                if done:
                    break
            
            # Align signals with original data
            signals = signals.reindex(data.index, fill_value=0)
            return signals
            
        except Exception as e:
            print(f"Error generating RL signals: {str(e)}")
            return pd.Series(0, index=data.index)
