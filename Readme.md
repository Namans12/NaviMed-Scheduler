# Smart AI Patient Appointment Scheduling System

## Overview
This project is an advanced AI-powered patient appointment scheduling system for healthcare providers. It combines reinforcement learning, predictive analytics, and a modern web interface to optimize appointment bookings, reduce no-shows, and provide actionable insights for administrators.

## Features
- **AI-Driven Scheduling:** Uses reinforcement learning (PPO) to optimize appointment slots and resource allocation.
- **No-Show Prediction:** Predicts patient no-shows using historical data and time series analysis.
- **Admin Dashboard:** Real-time statistics, analytics, and management tools for healthcare administrators.
- **Chatbot Booking:** Patients can book, reschedule, or cancel appointments via an interactive chatbot.
- **Notification Service:** Automated reminders and notifications for patients to reduce missed appointments.
- **Data Import & Preprocessing:** Tools for importing, cleaning, and merging healthcare datasets.
- **Model Training & Evaluation:** Scripts and logs for training, optimizing, and evaluating RL models.

## Tech Stack
- **Backend:** FastAPI, Python, SQLite/MySQL
- **Frontend:** Next.js, Zustand, Tailwind CSS
- **AI/ML:** PPO (Proximal Policy Optimization), Time Series Analysis
- **Deployment:** Azure, Docker

## Project Structure
```
backend/         # FastAPI backend, RL models, database logic
frontend/        # Next.js frontend, chatbot, dashboard
Datasets/        # Training and evaluation datasets
Docs/            # Project documentation
ppo_logs/        # RL training logs
eval_logs/       # Model evaluation logs
best_models/     # Saved RL models
optimized_models/# Optimized model versions
```

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+

## Installation

### Backend Setup (FastAPI)

```bash
cd backend                 # Navigate to backend folder
python -m venv venv       # (Optional) Create virtual environment
source venv/bin/activate  # Activate on Linux/macOS
venv\Scripts\activate     # Activate on Windows

pip install -r requirements.txt  # Install backend dependencies
python main.py                   # Run FastAPI backend
```

### Frontend Setup (React / Next.js)

```bash
cd frontend       # Navigate to frontend folder
npm install       # Install dependencies
npm run dev       # Start the development server
```


- Book appointments via the chatbot interface
- View analytics and manage schedules
- Train and evaluate RL models using provided scripts

## Data & Models
- Place your datasets in the `Datasets/` folder.
- RL models and logs are stored in `best_models/`, `optimized_models/`, and `ppo_logs/`.
- Evaluation logs are in `eval_logs/`.

## Contributing
Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## Contact

For questions or support, please contact the project maintainer.

