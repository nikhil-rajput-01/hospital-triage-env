from fastapi import FastAPI
from env import HospitalEnv
from tasks import TASKS
import uvicorn

app = FastAPI()
env = None

def init_env(task: str = "easy"):
    global env
    config = TASKS.get(task, TASKS["easy"])
    env = HospitalEnv(config)
    env.reset()


@app.get("/")
def root():
    return {"status": "ok"}


@app.post("/reset")
def reset(task: str = "easy"):
    init_env(task)
    return env.state()


@app.post("/step")
def step(action: dict):
    global env
    if env is None:
        init_env()
    state, reward, done, info = env.step(action)
    return {
        "state": state,
        "reward": float(reward),
        "done": bool(done),
        "info": info if isinstance(info, dict) else {}
    }


@app.get("/state")
def get_state():
    global env
    if env is None:
        init_env()
    return env.state()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)