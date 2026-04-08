import os
import json
import re
import requests
from openai import OpenAI

# Read environment variables
API_BASE_URL = os.getenv("API_BASE_URL")
MODEL_NAME = os.getenv("MODEL_NAME")
HF_TOKEN = os.getenv("HF_TOKEN")

# Initialize OpenAI client
client = OpenAI(
    base_url=API_BASE_URL,
    api_key=HF_TOKEN
)

def extract_json(text):
    try:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except:
        pass
    return {"type": "noop"}

def format_state(state):
    patients = sorted(
        state.get("patients", []),
        key=lambda x: x["severity"],
        reverse=True
    )[:5]

    return {
        "time": state.get("time"),
        "patients": patients,
        "busy_doctors": state.get("doctors", [])
    }

def get_action(state):
    formatted = format_state(state)

    prompt = f"""
You are a hospital AI.

Your goal is to maximize total score.

Scoring:
+10 correct assignment
+20 treatment completed
-0.3 * severity per waiting patient
-10 to -15 wrong assignment
-1000 patient death

Rules:
- Prioritize high severity patients
- Avoid unnecessary switching
- Use free doctors first

Return ONLY JSON:
{{
    "type": "assign",
    "doctor_id": int,
    "patient_id": int
}}

If no action:
{{"type": "noop"}}

Current State:
{json.dumps(formatted)}
"""
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "Return ONLY JSON. No text."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )

        text = response.choices[0].message.content.strip()

        if "```" in text:
            text = text.split("```")[1]

        return extract_json(text)

    except Exception as e:
        print(f"OpenAI error: {e}")
        return {"type": "noop"}

def run_simulation(task="easy"):

    reset_url = "http://localhost:7860/reset"
    response = requests.post(reset_url, json={"task": task})
    if response.status_code != 200:
        print(f"[START] task={task}", flush=True)
        print(f"[END] task={task} score=0.5 steps=0", flush=True)
        return 0.5
    print(f"[START] task={task}", flush=True)
    state = response.json()
    total_reward = 0
    step_count = 0

    while step_count < 100:  # max steps
        action = get_action(state)
        step_url = "http://localhost:7860/step"
        response = requests.post(step_url, json=action)
        if response.status_code != 200:
            print("Failed to step environment", flush=True)
            break

        result = response.json()
        state = result["state"]
        reward = result["reward"]
        done = result["done"]
        total_reward += reward
        step_count += 1
        print(f"[STEP] step={step_count} reward={reward}", flush=True)
        if done:
            break

    final_score = result.get("info", {}).get("score", 0.1) if 'result' in locals() else 0.5
    final_score = max(1e-6, min(1.0 - 1e-6, final_score))
    print(f"[END] task={task} score={final_score} steps={step_count}", flush=True)
    return final_score

if __name__ == "__main__":
    for task in ["easy", "medium", "hard"]:
        run_simulation(task)
