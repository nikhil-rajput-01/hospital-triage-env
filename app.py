import gradio as gr
from env import HospitalEnv
from tasks import TASKS
from grader import grade
from inference import get_action


def run_simulation(task_name):
    config = TASKS[task_name]
    env = HospitalEnv(config)

    state = env.reset()

    logs = []

    while True:
        for _ in range(config["spawn_rate"]):
            env.generate_patient()

        action = get_action(state)
        state, reward, done, _ = env.step(action)

        logs.append(
            f"Step {env.step_count} | Patients: {len(state['patients'])} | Reward: {round(reward,2)}"
        )

        if done:
            break

    score = grade(env)
    logs.append(f"\nFINAL SCORE: {score}")

    return "\n".join(logs)


demo = gr.Interface(
    fn=run_simulation,
    inputs=gr.Dropdown(["easy", "medium", "hard"], label="Task"),
    outputs="text",
    title="Hospital Triage AI Simulator",
    description="AI assigns doctors to patients dynamically"
)

demo.launch()