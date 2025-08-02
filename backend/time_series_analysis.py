import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.arima.model import ARIMA
import warnings
warnings.filterwarnings('ignore')

class TimeSeriesAnalyzer:
    """Time series analysis for appointment patterns and forecasting"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        
    def analyze_appointment_patterns(self, appointments_data: List[Dict]) -> Dict:
        """Analyze appointment patterns for seasonality and trends"""
        
        # Convert to DataFrame
        df = pd.DataFrame(appointments_data)
        df['appointment_date'] = pd.to_datetime(df['appointment_date'])
        df['hour'] = df['appointment_date'].dt.hour
        df['day_of_week'] = df['appointment_date'].dt.dayofweek
        df['month'] = df['appointment_date'].dt.month
        
        # Daily appointment counts
        daily_counts = df.groupby(df['appointment_date'].dt.date).size()
        daily_counts.index = pd.to_datetime(daily_counts.index)
        
        # Analyze seasonality
        seasonal_analysis = self._analyze_seasonality(daily_counts)
        
        # Analyze hourly patterns
        hourly_patterns = self._analyze_hourly_patterns(df)
        
        # Analyze weekly patterns
        weekly_patterns = self._analyze_weekly_patterns(df)
        
        # Forecast next 7 days
        forecast = self._forecast_appointments(daily_counts)
        
        return {
            'seasonal_analysis': seasonal_analysis,
            'hourly_patterns': hourly_patterns,
            'weekly_patterns': weekly_patterns,
            'forecast': forecast,
            'summary_stats': {
                'total_appointments': len(df),
                'avg_daily_appointments': daily_counts.mean(),
                'peak_hour': hourly_patterns['peak_hour'],
                'peak_day': weekly_patterns['peak_day'],
                'trend': seasonal_analysis['trend_direction']
            }
        }
    
    def _analyze_seasonality(self, daily_counts: pd.Series) -> Dict:
        """Decompose time series into trend, seasonal, and residual components"""
        
        # Resample to daily frequency and fill missing values
        daily_counts = daily_counts.resample('D').sum().fillna(0)
        
        # Perform seasonal decomposition
        decomposition = seasonal_decompose(daily_counts, period=7, extrapolate_trend='freq')
        
        # Test for stationarity
        adf_result = adfuller(daily_counts)
        
        # Calculate trend direction
        trend_slope = np.polyfit(range(len(daily_counts)), daily_counts, 1)[0]
        trend_direction = "increasing" if trend_slope > 0 else "decreasing" if trend_slope < 0 else "stable"
        
        return {
            'trend': decomposition.trend.tolist(),
            'seasonal': decomposition.seasonal.tolist(),
            'residual': decomposition.resid.tolist(),
            'trend_direction': trend_direction,
            'trend_strength': abs(trend_slope),
            'is_stationary': adf_result[1] < 0.05,
            'adf_p_value': adf_result[1]
        }
    
    def _analyze_hourly_patterns(self, df: pd.DataFrame) -> Dict:
        """Analyze hourly appointment patterns"""
        
        hourly_counts = df.groupby('hour').size()
        peak_hour = hourly_counts.idxmax()
        
        # Calculate busy periods
        busy_hours = hourly_counts[hourly_counts > hourly_counts.mean() + hourly_counts.std()].index.tolist()
        
        return {
            'hourly_distribution': hourly_counts.to_dict(),
            'peak_hour': int(peak_hour),
            'busy_hours': [int(h) for h in busy_hours],
            'avg_appointments_per_hour': hourly_counts.mean(),
            'hourly_variance': hourly_counts.var()
        }
    
    def _analyze_weekly_patterns(self, df: pd.DataFrame) -> Dict:
        """Analyze weekly appointment patterns"""
        
        weekly_counts = df.groupby('day_of_week').size()
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        peak_day_idx = weekly_counts.idxmax()
        peak_day = day_names[peak_day_idx]
        
        return {
            'weekly_distribution': {day_names[i]: count for i, count in weekly_counts.items()},
            'peak_day': peak_day,
            'peak_day_index': int(peak_day_idx),
            'weekend_vs_weekday': {
                'weekday_avg': weekly_counts[:5].mean(),
                'weekend_avg': weekly_counts[5:].mean()
            }
        }
    
    def _forecast_appointments(self, daily_counts: pd.Series, days_ahead: int = 7) -> Dict:
        """Forecast appointment demand using ARIMA model"""
        
        # Prepare data
        daily_counts = daily_counts.resample('D').sum().fillna(0)
        
        try:
            # Fit ARIMA model
            model = ARIMA(daily_counts, order=(1, 1, 1))
            fitted_model = model.fit()
            
            # Forecast
            forecast = fitted_model.forecast(steps=days_ahead)
            forecast_dates = pd.date_range(start=daily_counts.index[-1] + timedelta(days=1), periods=days_ahead)
            
            return {
                'forecast_values': forecast.tolist(),
                'forecast_dates': [d.strftime('%Y-%m-%d') for d in forecast_dates],
                'confidence_intervals': fitted_model.get_forecast(steps=days_ahead).conf_int().tolist(),
                'model_aic': fitted_model.aic,
                'model_bic': fitted_model.bic
            }
        except Exception as e:
            # Fallback to simple moving average
            avg_appointments = daily_counts.mean()
            forecast_values = [avg_appointments] * days_ahead
            forecast_dates = [d.strftime('%Y-%m-%d') for d in pd.date_range(start=daily_counts.index[-1] + timedelta(days=1), periods=days_ahead)]
            
            return {
                'forecast_values': forecast_values,
                'forecast_dates': forecast_dates,
                'confidence_intervals': None,
                'model_aic': None,
                'model_bic': None,
                'fallback_used': True,
                'error': str(e)
            }
    
    def create_time_series_plots(self, analysis_results: Dict) -> Dict:
        """Create interactive plots for time series analysis"""
        
        plots = {}
        
        # Seasonal decomposition plot
        fig_decomp = make_subplots(
            rows=4, cols=1,
            subplot_titles=('Original', 'Trend', 'Seasonal', 'Residual'),
            vertical_spacing=0.05
        )
        
        dates = pd.date_range(start='2024-01-01', periods=len(analysis_results['seasonal_analysis']['trend']), freq='D')
        
        fig_decomp.add_trace(go.Scatter(x=dates, y=analysis_results['seasonal_analysis']['trend'], name='Trend'), row=2, col=1)
        fig_decomp.add_trace(go.Scatter(x=dates, y=analysis_results['seasonal_analysis']['seasonal'], name='Seasonal'), row=3, col=1)
        fig_decomp.add_trace(go.Scatter(x=dates, y=analysis_results['seasonal_analysis']['residual'], name='Residual'), row=4, col=1)
        
        fig_decomp.update_layout(height=800, title_text="Time Series Decomposition")
        plots['decomposition'] = fig_decomp.to_html()
        
        # Hourly pattern plot
        hourly_data = analysis_results['hourly_patterns']['hourly_distribution']
        fig_hourly = go.Figure(data=[
            go.Bar(x=list(hourly_data.keys()), y=list(hourly_data.values()))
        ])
        fig_hourly.update_layout(title="Hourly Appointment Distribution", xaxis_title="Hour", yaxis_title="Appointments")
        plots['hourly'] = fig_hourly.to_html()
        
        # Weekly pattern plot
        weekly_data = analysis_results['weekly_patterns']['weekly_distribution']
        fig_weekly = go.Figure(data=[
            go.Bar(x=list(weekly_data.keys()), y=list(weekly_data.values()))
        ])
        fig_weekly.update_layout(title="Weekly Appointment Distribution", xaxis_title="Day", yaxis_title="Appointments")
        plots['weekly'] = fig_weekly.to_html()
        
        # Forecast plot
        if analysis_results['forecast']['forecast_values']:
            forecast_dates = pd.to_datetime(analysis_results['forecast']['forecast_dates'])
            fig_forecast = go.Figure()
            fig_forecast.add_trace(go.Scatter(
                x=forecast_dates,
                y=analysis_results['forecast']['forecast_values'],
                mode='lines+markers',
                name='Forecast'
            ))
            fig_forecast.update_layout(title="7-Day Appointment Forecast", xaxis_title="Date", yaxis_title="Predicted Appointments")
            plots['forecast'] = fig_forecast.to_html()
        
        return plots 