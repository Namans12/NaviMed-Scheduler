import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV
from sklearn.metrics import mean_squared_error, mean_absolute_error
import optuna
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from stable_baselines3.common.callbacks import EvalCallback
import joblib
import json
from datetime import datetime
import os

class ModelOptimizer:
    """Model optimization and performance tuning for RL agent"""
    
    def __init__(self, env_class, model_save_path: str = "optimized_models/"):
        self.env_class = env_class
        self.model_save_path = model_save_path
        os.makedirs(model_save_path, exist_ok=True)
        self.optimization_history = []
        
    def optimize_hyperparameters(self, n_trials: int = 50) -> Dict:
        """Optimize hyperparameters using Optuna"""
        
        def objective(trial):
            # Define hyperparameter search space
            learning_rate = trial.suggest_float('learning_rate', 1e-5, 1e-2, log=True)
            n_steps = trial.suggest_categorical('n_steps', [1024, 2048, 4096, 8192])
            batch_size = trial.suggest_categorical('batch_size', [32, 64, 128, 256])
            n_epochs = trial.suggest_int('n_epochs', 4, 20)
            gamma = trial.suggest_float('gamma', 0.9, 0.999)
            gae_lambda = trial.suggest_float('gae_lambda', 0.8, 0.99)
            clip_range = trial.suggest_float('clip_range', 0.1, 0.4)
            ent_coef = trial.suggest_float('ent_coef', 1e-8, 1e-1, log=True)
            vf_coef = trial.suggest_float('vf_coef', 0.1, 1.0)
            max_grad_norm = trial.suggest_float('max_grad_norm', 0.1, 2.0)
            
            # Network architecture
            net_arch = trial.suggest_categorical('net_arch', [
                [64, 64],
                [128, 128],
                [256, 256],
                [256, 256, 128],
                [512, 256, 128]
            ])
            
            try:
                # Create environment
                env = DummyVecEnv([lambda: self.env_class()])
                
                # Create model with trial parameters
                model = PPO(
                    'MlpPolicy',
                    env,
                    verbose=0,
                    learning_rate=learning_rate,
                    n_steps=n_steps,
                    batch_size=batch_size,
                    n_epochs=n_epochs,
                    gamma=gamma,
                    gae_lambda=gae_lambda,
                    clip_range=clip_range,
                    ent_coef=ent_coef,
                    vf_coef=vf_coef,
                    max_grad_norm=max_grad_norm,
                    policy_kwargs=dict(net_arch=net_arch)
                )
                
                # Train for a limited number of steps
                model.learn(total_timesteps=50000, progress_bar=False)
                
                # Evaluate model
                eval_env = DummyVecEnv([lambda: self.env_class()])
                eval_callback = EvalCallback(
                    eval_env,
                    best_model_save_path=f"{self.model_save_path}/trial_{trial.number}/",
                    log_path=f"{self.model_save_path}/trial_{trial.number}/",
                    eval_freq=1000,
                    deterministic=True,
                    render=False
                )
                
                # Run evaluation
                obs = eval_env.reset()
                total_reward = 0
                for _ in range(1000):
                    action, _ = model.predict(obs, deterministic=True)
                    obs, reward, done, _ = eval_env.step(action)
                    total_reward += reward[0]
                    if done[0]:
                        obs = eval_env.reset()
                
                return total_reward
                
            except Exception as e:
                print(f"Trial failed: {e}")
                return -1000  # Return very low reward for failed trials
        
        # Create study
        study = optuna.create_study(direction='maximize')
        study.optimize(objective, n_trials=n_trials)
        
        # Save best parameters
        best_params = study.best_params
        best_value = study.best_value
        
        optimization_result = {
            'best_params': best_params,
            'best_value': best_value,
            'optimization_history': study.trials_dataframe().to_dict('records'),
            'timestamp': datetime.now().isoformat()
        }
        
        # Save results
        with open(f"{self.model_save_path}/optimization_results.json", 'w') as f:
            json.dump(optimization_result, f, indent=2)
        
        self.optimization_history.append(optimization_result)
        
        return optimization_result
    
    def train_optimized_model(self, best_params: Dict, total_timesteps: int = 500000) -> str:
        """Train model with optimized hyperparameters"""
        
        # Create environment
        env = DummyVecEnv([lambda: self.env_class()])
        
        # Create optimized model
        model = PPO(
            'MlpPolicy',
            env,
            verbose=1,
            **best_params,
            policy_kwargs=dict(net_arch=best_params.get('net_arch', [256, 256, 128]))
        )
        
        # Train model
        model.learn(total_timesteps=total_timesteps)
        
        # Save optimized model
        model_path = f"{self.model_save_path}/optimized_ppo_model.zip"
        model.save(model_path)
        
        return model_path
    
    def a_b_test_models(self, model_a_path: str, model_b_path: str, n_episodes: int = 100) -> Dict:
        """Perform A/B testing between two models"""
        
        def evaluate_model(model_path: str, n_episodes: int) -> Dict:
            try:
                model = PPO.load(model_path)
                env = self.env_class()
                
                rewards = []
                patients_served = []
                emergencies_handled = []
                episode_lengths = []
                
                for _ in range(n_episodes):
                    obs = env.reset()
                    episode_reward = 0
                    episode_length = 0
                    
                    while True:
                        action, _ = model.predict(obs, deterministic=True)
                        obs, reward, done, info = env.step(action)
                        episode_reward += reward
                        episode_length += 1
                        
                        if done:
                            break
                    
                    rewards.append(episode_reward)
                    patients_served.append(info.get('patients_served', 0))
                    emergencies_handled.append(info.get('emergencies_handled', 0))
                    episode_lengths.append(episode_length)
                
                return {
                    'avg_reward': np.mean(rewards),
                    'std_reward': np.std(rewards),
                    'avg_patients_served': np.mean(patients_served),
                    'avg_emergencies_handled': np.mean(emergencies_handled),
                    'avg_episode_length': np.mean(episode_lengths),
                    'success_rate': np.mean([r > 0 for r in rewards])
                }
                
            except Exception as e:
                return {'error': str(e)}
        
        # Evaluate both models
        model_a_results = evaluate_model(model_a_path, n_episodes)
        model_b_results = evaluate_model(model_b_path, n_episodes)
        
        # Statistical comparison
        comparison = {
            'model_a': model_a_results,
            'model_b': model_b_results,
            'winner': None,
            'confidence': 0.0,
            'significant_difference': False
        }
        
        if 'error' not in model_a_results and 'error' not in model_b_results:
            # Simple comparison based on average reward
            if model_a_results['avg_reward'] > model_b_results['avg_reward']:
                comparison['winner'] = 'model_a'
                comparison['confidence'] = abs(model_a_results['avg_reward'] - model_b_results['avg_reward']) / max(model_a_results['avg_reward'], model_b_results['avg_reward'])
            else:
                comparison['winner'] = 'model_b'
                comparison['confidence'] = abs(model_b_results['avg_reward'] - model_a_results['avg_reward']) / max(model_a_results['avg_reward'], model_b_results['avg_reward'])
            
            # Determine if difference is significant (simple threshold)
            comparison['significant_difference'] = comparison['confidence'] > 0.1
        
        comparison['timestamp'] = datetime.now().isoformat()
        
        return comparison
    
    def model_performance_monitoring(self, model_path: str, monitoring_period: int = 30) -> Dict:
        """Monitor model performance over time"""
        
        monitoring_data = {
            'daily_performance': [],
            'drift_detection': {},
            'recommendations': []
        }
        
        # Simulate daily performance monitoring
        for day in range(monitoring_period):
            try:
                model = PPO.load(model_path)
                env = self.env_class()
                
                daily_rewards = []
                daily_patients = []
                daily_emergencies = []
                
                # Evaluate for 10 episodes per day
                for _ in range(10):
                    obs = env.reset()
                    episode_reward = 0
                    
                    while True:
                        action, _ = model.predict(obs, deterministic=True)
                        obs, reward, done, info = env.step(action)
                        episode_reward += reward
                        
                        if done:
                            break
                    
                    daily_rewards.append(episode_reward)
                    daily_patients.append(info.get('patients_served', 0))
                    daily_emergencies.append(info.get('emergencies_handled', 0))
                
                daily_performance = {
                    'day': day + 1,
                    'avg_reward': np.mean(daily_rewards),
                    'avg_patients': np.mean(daily_patients),
                    'avg_emergencies': np.mean(daily_emergencies),
                    'reward_std': np.std(daily_rewards),
                    'timestamp': datetime.now().isoformat()
                }
                
                monitoring_data['daily_performance'].append(daily_performance)
                
            except Exception as e:
                monitoring_data['daily_performance'].append({
                    'day': day + 1,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
        
        # Detect performance drift
        if len(monitoring_data['daily_performance']) > 7:
            recent_performance = [p['avg_reward'] for p in monitoring_data['daily_performance'][-7:] if 'avg_reward' in p]
            baseline_performance = [p['avg_reward'] for p in monitoring_data['daily_performance'][:7] if 'avg_reward' in p]
            
            if recent_performance and baseline_performance:
                recent_avg = np.mean(recent_performance)
                baseline_avg = np.mean(baseline_performance)
                drift_percentage = (recent_avg - baseline_avg) / baseline_avg * 100
                
                monitoring_data['drift_detection'] = {
                    'drift_percentage': drift_percentage,
                    'baseline_avg': baseline_avg,
                    'recent_avg': recent_avg,
                    'drift_detected': abs(drift_percentage) > 10
                }
                
                # Generate recommendations
                if drift_percentage < -10:
                    monitoring_data['recommendations'].append("Model performance has degraded. Consider retraining with recent data.")
                elif drift_percentage > 10:
                    monitoring_data['recommendations'].append("Model performance has improved. Consider updating baseline metrics.")
                else:
                    monitoring_data['recommendations'].append("Model performance is stable. Continue monitoring.")
        
        return monitoring_data
    
    def generate_performance_report(self, model_path: str) -> str:
        """Generate comprehensive performance report"""
        
        # Load model and evaluate
        model = PPO.load(model_path)
        env = self.env_class()
        
        # Comprehensive evaluation
        n_episodes = 50
        all_rewards = []
        all_patients_served = []
        all_emergencies_handled = []
        all_episode_lengths = []
        
        for _ in range(n_episodes):
            obs = env.reset()
            episode_reward = 0
            episode_length = 0
            
            while True:
                action, _ = model.predict(obs, deterministic=True)
                obs, reward, done, info = env.step(action)
                episode_reward += reward
                episode_length += 1
                
                if done:
                    break
            
            all_rewards.append(episode_reward)
            all_patients_served.append(info.get('patients_served', 0))
            all_emergencies_handled.append(info.get('emergencies_handled', 0))
            all_episode_lengths.append(episode_length)
        
        # Calculate metrics
        metrics = {
            'avg_reward': np.mean(all_rewards),
            'std_reward': np.std(all_rewards),
            'min_reward': np.min(all_rewards),
            'max_reward': np.max(all_rewards),
            'avg_patients_served': np.mean(all_patients_served),
            'avg_emergencies_handled': np.mean(all_emergencies_handled),
            'avg_episode_length': np.mean(all_episode_lengths),
            'success_rate': np.mean([r > 0 for r in all_rewards]),
            'efficiency_score': np.mean(all_patients_served) / np.mean(all_episode_lengths) if np.mean(all_episode_lengths) > 0 else 0
        }
        
        # Generate report
        report = f"""
# Model Performance Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary Statistics
- **Average Reward**: {metrics['avg_reward']:.2f} ± {metrics['std_reward']:.2f}
- **Success Rate**: {metrics['success_rate']:.1%}
- **Patients Served**: {metrics['avg_patients_served']:.1f} per episode
- **Emergencies Handled**: {metrics['avg_emergencies_handled']:.1f} per episode
- **Efficiency Score**: {metrics['efficiency_score']:.3f}

## Performance Range
- **Best Episode**: {metrics['max_reward']:.2f} reward
- **Worst Episode**: {metrics['min_reward']:.2f} reward
- **Episode Length**: {metrics['avg_episode_length']:.1f} steps average

## Recommendations
"""
        
        if metrics['success_rate'] < 0.8:
            report += "- Model success rate is below 80%. Consider retraining with different hyperparameters.\n"
        
        if metrics['avg_reward'] < 0:
            report += "- Model is performing poorly (negative average reward). Review reward function and training data.\n"
        
        if metrics['efficiency_score'] < 0.1:
            report += "- Low efficiency score. Consider optimizing episode length or patient throughput.\n"
        
        if not any([metrics['success_rate'] < 0.8, metrics['avg_reward'] < 0, metrics['efficiency_score'] < 0.1]):
            report += "- Model is performing well across all metrics. Continue monitoring for drift.\n"
        
        return report 