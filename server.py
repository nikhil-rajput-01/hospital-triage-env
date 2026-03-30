from fastapi import FastAPI
from env import HospitalEnv
from tasks import TASKS
import uvicorn

app = FastAPI()

# Global env instance, initialized on reset
env = None

@app.get("/")
def root():
    return {"status": "ok"}

@app.post("/reset")
def reset(task: str = "easy"):
    global env
    config = TASKS.get(task, TASKS["easy"])
    env = HospitalEnv(config)
    initial_state = env.reset()
    return initial_state

@app.post("/step")
def step(action: dict):
    global env
    if env is None:
        return {"error": "Environment not initialized. Call /reset first."}
    state, reward, done, info = env.step(action)
    return {"state": state, "reward": reward, "done": done, "info": info}

@app.get("/state")
def get_state():
    global env
    if env is None:
        return {"error": "Environment not initialized. Call /reset first."}
    return env.state()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)