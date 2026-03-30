---
title: Hospital Triage Environment
emoji: 🐍
colorFrom: green
colorTo: blue
sdk: docker
short_description: AI system to allocate doctors to patients dynamically
python_version: "3.11"
app_file: app.py
pinned: false
---
# Hospital Triage Environment

An AI-powered hospital resource allocation simulation that models real-world triage and doctor-patient assignment challenges.

## Overview

This project simulates a hospital environment where an AI agent must intelligently assign doctors to patients while managing constraints like:

- **Patient severity levels** - Varying from minor ailments to life-threatening conditions
- **Doctor specialties** - Different doctors can treat specific conditions
- **Limited resources** - Doctors have finite availability and treatment time
- **Patient mortality risk** - Failure to treat critical patients quickly results in penalties

The goal is to maximize patient outcomes by making optimal assignment decisions.

## Project Structure

```
hospital-triage-env/
├── app.py              # Gradio web interface for simulation
├── server.py           # FastAPI backend server
├── env.py              # Hospital environment core logic
├── inference.py        # AI agent inference module
├── tasks.py            # Task configurations (easy/medium/hard)
├── grader.py           # Scoring and evaluation system
├── requirements.txt    # Python dependencies
├── Dockerfile          # Docker container configuration
├── openenv.yml         # Environment configuration file
├── main.py             # For running full logic in terminal 
└── README.md           # This file
```

## Key Features

### Multiple Medical Conditions
Conditions categorized across 9 medical specialties:
- General Physician, Cardiologist, Dermatologist, Neurologist, Orthopedic, Pediatrician, Gynecologist, Psychiatrist, ENT Specialist

### Multiple Difficulty Levels
- **Easy**: Manageable patient load, fewer critical cases
- **Medium**: Balanced difficulty with mixed severity patients
- **Hard**: High load with critical cases requiring quick decisions

### AI-Powered Agent
- Uses LLM (via OpenRouter API) for intelligent decision-making
- Evaluates patient severity, doctor availability, and treatment urgency
- Can be replaced with custom agents

### Scoring System
Reward calculation based on:
- Successful patient treatments
- Prevented patient deaths
- Minimized wait times
- Optimal resource utilization

## Installation

### Prerequisites
- Python 3.10+
- Virtual environment (optional but recommended)

### Setup

1. **Clone and navigate to project**
   ```bash
   cd hospital-triage-env
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   export API_BASE_URL="https://openrouter.ai/api/v1"
   export HF_TOKEN="your_api_key_here"
   export MODEL_NAME="openai/gpt-4o-mini"
   ```

## Usage

### 1. Web Interface (Gradio)
```bash
python app.py
```
Access at `http://localhost:7860` - Interactive UI to run simulations with different difficulty levels.

### 2. FastAPI Server
```bash
python server.py && python inference.py
```
API endpoints:
- `GET /` - Health check
- `POST /reset?task=easy` - Initialize environment
- `POST /step` - Execute action and get state
- `GET /state` - Get current state


### 3. Command-Line Simulation
```bash
python main.py
```
```python
if __name__ == "__main__":
        step("medium") # you can change to easy,medium,hard
```
Run agent-based simulation in terminal with detailed step-by-step output.

## API Reference

### Environment State
```json
{
  "patients": [
    {
      "id": 0,
      "condition_id": 5,
      "severity": 0.8,
      "time_left": 10,
      "arrived_at": 0
    }
  ],
  "doctors": [
    {
      "id": 0,
      "specialty": "general_physician",
      "busy": false,
      "time_remaining": 0
    }
  ],
  "current_time": 5
}
```

### Action Format
```json
{
  "type": "assign",
  "doctor_id": 0,
  "patient_id": 1
}
```
Or for no action:
```json
{
  "type": "noop"
}
```

### Step Response
```json
{
  "state": { ... },
  "reward": 0.5,
  "done": false,
  "info": { "message": "Assignment successful" }
}
```

## Customization

### Add Custom Agent
Modify `inference.py` to implement custom decision-making logic:
```python
def get_action(state):
    return {"type": "noop"}
```

### Adjust Task Configurations
Edit `tasks.py` to modify:
- Number of doctors
- Patient spawn rate
- Simulation duration
- Difficulty parameters

## Evaluation Metrics

The grader calculates scores based on:
- **Treatment success rate** - Percentage of patients successfully treated
- **Mortality rate** - Percentage of preventable deaths
- **Average wait time** - Mean time patients spend waiting
- **Resource efficiency** - Doctor utilization ratio

## Docker Deployment

Build and run with Docker:
```bash
docker build -t hospital-triage .
docker run -p 8000:8000 hospital-triage
```

## Dependencies

- **fastapi** - Web API framework
- **uvicorn** - ASGI server
- **gradio** - Web UI framework
- **openai** - LLM integration
- **requests** - HTTP client

See `requirements.txt` for full list.
