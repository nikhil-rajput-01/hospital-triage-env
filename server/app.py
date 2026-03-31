from fastapi import FastAPI
from models import Action, StepResponse
from env import HospitalEnv
from tasks import TASKS
import uvicorn

app = FastAPI()



env = None


def init_env(task="easy"):
    global env
    env = HospitalEnv(TASKS[task])
    env.reset()


@app.get("/")
def root():
    return {"status": "ok"}


@app.post("/reset")
def reset(task: str = "easy"):
    init_env(task)
    return env.state()


@app.post("/step", response_model=StepResponse)
def step(action: Action):
    global env

    if env is None:
        init_env()

    state, reward, done, info = env.step(action.dict())

    return StepResponse(
        state=state,
        reward=float(reward),
        done=bool(done),
        info=info or {}
    )


@app.get("/state")
def state():
    global env
    if env is None:
        init_env()
    return env.state()


def main():
    uvicorn.run("server.app:app", host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()
