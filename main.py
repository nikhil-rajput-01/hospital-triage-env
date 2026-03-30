import os
import time
import random
import json
from openai import OpenAI

busy_doctors = {}
doctor_current_patient = {}
patients = {}
patient_counter = 0
point = 0
max_patients = 20
total_generated = 0
total_treated = 0
total_died = 0
total_wait_time = 0

BASE_URL = os.getenv("API_BASE_URL", "https://openrouter.ai/api/v1")
API_KEY = os.getenv("HF_TOKEN")
MODEL_NAME = os.getenv("MODEL_NAME", "openai/gpt-4o-mini")

client = OpenAI(
    base_url=BASE_URL,
    api_key=API_KEY,
)

illness = {
        "0": "fever", "1": "cold", "2": "flu", "3": "minor_infections", "4": "general_checkups",
        "5": "hypertension", "6": "early_stage_infections", "7": "heart_disease", "8": "heart_attack",
        "9": "arrhythmia", "10": "chest_pain", "11": "acne", "12": "eczema", "13": "psoriasis",
        "14": "skin_rashes", "15": "skin_infections", "16": "epilepsy", "17": "stroke",
        "18": "nerve_disorders", "19": "migraine", "20": "chronic_pain", "21": "fractures",
        "22": "bone_injuries", "23": "joint_pain", "24": "arthritis", "25": "child_illnesses",
        "26": "vaccinations", "27": "growth_issues", "28": "pregnancy", "29": "reproductive_health",
        "30": "menstrual_disorders", "31": "hormonal_issues", "32": "abdominal_pain", "33": "depression",
        "34": "mental_health_disorders", "35": "anxiety", "36": "behavioral_issues", "37": "ear_infections",
        "38": "hearing_problems", "39": "sinusitis", "40": "throat_infections", "41": "general_fatigue"
}
can_die = [5, 7, 8, 9, 10, 16, 17]
doctor = [
        {"id": 0, "type": "general_physician", "treats": [0, 1, 2, 3, 4], "can_treat": [5, 6]},
        {"id": 1, "type": "cardiologist", "treats": [7, 8, 9], "can_treat": [5, 10]},
        {"id": 2, "type": "dermatologist", "treats": [11, 12, 13], "can_treat": [14, 15]},
        {"id": 3, "type": "neurologist", "treats": [16, 17, 18], "can_treat": [19, 20]},
        {"id": 4, "type": "orthopedic", "treats": [21, 22], "can_treat": [23, 24]},
        {"id": 5, "type": "pediatrician", "treats": [25, 26, 27], "can_treat": [0, 1, 2]},
        {"id": 6, "type": "gynecologist", "treats": [28, 29, 30], "can_treat": [31, 32]},
        {"id": 7, "type": "psychiatrist", "treats": [33, 34], "can_treat": [35, 36]},
        {"id": 8, "type": "ent_specialist", "treats": [37, 38], "can_treat": [39, 40]}
    ]

def generate_patient():
    global patient_counter, patients, total_generated

    patient_counter += 1
    total_generated += 1
    condition_id = random.randint(0, 41)
    severity = random.randint(1, 10)

    if severity >= 8:
        time_left = random.randint(10, 15)
    elif severity >= 4:
        time_left = random.randint(16, 25)
    else:
        time_left = random.randint(26, 40)

    patients[patient_counter] = {
        "id": patient_counter,
        "condition_id": condition_id,
        "severity": severity,
        "time_left": time_left,
        "time_takes": random.randint(1, 5) + severity // 2,
        "arrival_time": time.time(),
        "can_die": condition_id in can_die
    }


def askai():
    p_tem = [
    {
        "id": p["id"],
        "condition_id": p["condition_id"],
        "severity": p["severity"],
        "arrival_time": p["arrival_time"]
    }
    for p in patients.values()
]
    prompt = f"""
You are a hospital resource management AI.
illmess: {illness}
doctor: {doctor}
who can die: {can_die}
current time: {time.time()}

Goals:
- Save patients
- Prioritize high severity
- Match doctor specialty
- Avoid assigning busy doctors
- Switching allowed on high severity


Return ONLY valid JSON:
{{
  "assignments": [
    {{"type": "assign", "doctor_id": int, "patient_id": int}},
    {{"type": "assign", "doctor_id": int, "patient_id": int}}
  ]
}}

If no valid action:
{{"type": "noop"}}

State:
busy doctors: {list(busy_doctors.keys())}
patients: {p_tem}

"""
    #print(prompt)
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            extra_headers={
                "HTTP-Referer": "http://localhost",   # can change later
                "X-OpenRouter-Title": "Hospital AI"
            },
            messages=[
                {"role": "system", "content": "You are a precise decision-making AI. Output JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )

        text = response.choices[0].message.content.strip()
        text = text.replace("json", "")
        #print(text)
        # clean markdown if present
        if "```" in text:
            text = text.split("```")[1]
        
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        data = json.loads(text)
        assignments = data.get("assignments", [])
        if isinstance(assignments, list):
            for a in assignments:
                check_response(a)
        

    except Exception as e:
        print("\033[91m[OpenRouter error]\033[0m", e)
        return {"type": "noop"}


def check_response(response):
    global point, busy_doctors, patients, doctor_current_patient

    if response.get("type") == "assign":
        doctor_id = response.get("doctor_id")
        patient_id = response.get("patient_id")

        # invalid patient
        if patient_id not in patients:
            print(f"Patient {patient_id} not found")
            return False

        # SWITCHING LOGIC
        if doctor_id in busy_doctors:
            print(f"\033[35m[SWITCHING] Doctor {doctor_id} switching patients!\033[0m")
            prev_patient_id = doctor_current_patient.get(doctor_id)
            prev_patient = patients.get(prev_patient_id) if prev_patient_id else None
            new_patient = patients.get(patient_id)
            switch_penalty = 10

            # Emergency override
            if new_patient and new_patient["severity"] >= 9:
                print(f"\033[91m[EMERGENCY] Doctor {doctor_id} treating high severity patient!\033[0m")
                switch_penalty = 3   # lower penalty

            # Switching cost based on severity
            if prev_patient:
                switch_penalty += prev_patient["severity"]

            point -= switch_penalty

            # Death risk boost
            if prev_patient:
                if prev_patient.get("can_die"):
                    prev_patient["time_left"] -= 5
                    print(f"Previous patient {prev_patient_id} at high death risk!")

                prev_patient["progress"] = prev_patient.get("progress", 0) * 0.5
            point -= 10

        # assign new patient
        p = patients.pop(patient_id)
        busy_doctors[doctor_id] = p["time_takes"]
        doctor_current_patient[doctor_id] = patient_id
        condition = p["condition_id"]
        doc = doctor[doctor_id]

        # scoring
        if condition in doc["treats"]:
            point += 10
        elif condition in doc["can_treat"]:
            point += 5
        else:
            point -= 15

        print(f"Assigned Doctor {doctor_id} → Patient {patient_id}")
        return True

    elif response.get("type") == "noop":
        return True

    return False
    
def check_deaths():
    global patients, total_died, point
    dead_ids = []
    total_died += 1
    for pid, p in patients.items():
        p["time_left"] -= 1

        if p["time_left"] <= 0 and p["can_die"]:
            print(f"\033[91m[DEAD] Patient {pid} died\033[0m")
            point -= 1000
            dead_ids.append(pid)
    for pid in dead_ids:
        del patients[pid]

def doctor_free():
    global busy_doctors, doctor_current_patient, total_treated, point
    finished = []
    for d in busy_doctors:
        busy_doctors[d] -= 1
        if busy_doctors[d] <= 0:
            finished.append(d)

    for d in finished:
        print(f"\033[92m[DOCTOR FREE] Doctor {d} is now free\033[0m")
        total_treated += 1
        del busy_doctors[d]

        if d in doctor_current_patient:
            del doctor_current_patient[d]

def final_score():
    if total_generated == 0:
        return 0
    survival_rate = (total_generated - total_died) / total_generated
    treatment_rate = total_treated / total_generated
    avg_wait = total_wait_time / max(total_generated, 1)
    wait_score = max(0, 1 - (avg_wait / 50))   # normalize
    point_score = max(0, min(1, (point + 500) / 1000))
    final = (
        0.4 * survival_rate +
        0.3 * treatment_rate +
        0.2 * wait_score +
        0.1 * point_score
    )
    return round(final, 4)

def step(level):
    lev = {"easy": 2, "medium": 5, "hard": 10}
    steps = 0
    while steps < 10:
        steps += 1
        total_wait_time += sum(p["severity"] for p in patients.values())
        check_deaths()
        doctor_free()
        if len(patients) >= max_patients:
            point -= 50
            print("\033[93m[HOSPITAL OVERCROWDED] Penalty applied.\033[0m")
        else:
            for _ in range(lev.get(level, 5)):
                generate_patient()
        askai()
        print(point)
        print(list(busy_doctors.keys()))
        print(list(patients.keys()))
        time.sleep(2)
    print("FINAL RESULTS")
    print("Level:", level)
    print("Total Generated:", total_generated)
    print("Treated:", total_treated)
    print("Died:", total_died)
    print("Final Score:", final_score())

if __name__ == "__main__":
        step("medium") # you can change to easy,medium,hard
    
