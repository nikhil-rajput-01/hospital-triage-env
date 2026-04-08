import random
import time
import math
# Doctor definitions
DOCTOR_LIST = [
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

CAN_DIE = [5, 7, 8, 9, 10, 16, 17]


class HospitalEnv:
    def __init__(self, config):
        self.config = config
        self.reset()

    def get_normalized_score(self):
        EPS = 1e-6
        score = 1 / (1 + math.exp(-self.point / 200))
        return max(EPS, min(1.0 - EPS, score))
    def __init__(self, config):
        self.config = config
        self.reset()

    def reset(self):
        random.seed(42)  # for reproducibility
        self.doctors = self.config.get("doctors", [1, 2, 3])
        self.patients = {}
        self.busy_doctors = {}
        self.doctor_current_patient = {}

        self.patient_counter = 0

        self.point = 0
        self.total_generated = 0
        self.total_treated = 0
        self.total_died = 0
        self.total_wait_time = 0

        self.step_count = 0

        return self.state()

    def state(self):
        return {
            "patients": [
                {
                    "id": int(p),
                    "condition_id": int(self.patients[p]["condition_id"]),
                    "severity": float(self.patients[p]["severity"]),
                    "time_left": float(self.patients[p]["time_left"])
                }
                for p in self.patients
            ],
            "doctors": [
                {
                    "id": int(d),
                    "type": str(DOCTOR_LIST[d]["type"]),
                    "busy": bool(d in self.busy_doctors),
                }
                for d in self.doctors
            ],
            "time": int(self.step_count)
        }

    def generate_patient(self):
        if len(self.patients) >= self.config["max_patients"]:
            self.point -= 50
            return

        self.patient_counter += 1
        self.total_generated += 1

        condition_id = random.randint(0, 41)
        severity = random.randint(1, 10)

        self.patients[self.patient_counter] = {
            "id": self.patient_counter,
            "condition_id": condition_id,
            "severity": severity,
            "time_left": random.randint(10, 30),
            "time_takes": random.randint(2, 6),
            "can_die": condition_id in CAN_DIE,
            "arrival_time": self.step_count
        }

    def step(self, action):
        if self.config["steps"] == 0:
            return self.state(), 0.0, True, {"score": self.get_normalized_score()}
        prev_point = self.point
        self.step_count += 1
        # Generate new patients
        for _ in range(self.config.get("spawn_rate", 1)):
            self.generate_patient()
        # waiting penalty
        self.total_wait_time += sum(p["severity"] for p in self.patients.values())
        waiting_penalty = sum(p["severity"] * 0.3 for p in self.patients.values())
        self.point -= waiting_penalty
        # apply action
        if action.get("type") == "assign":
            self._assign(action)
        # update doctors
        self._update_doctors()
        # update patients
        self._update_patients()
        done = self.step_count >= self.config["steps"]
        reward = self.point - prev_point
        return self.state(), reward, done, {"score": self.get_normalized_score()}

    def _assign(self, action):
        doctor_id = action.get("doctor_id")
        patient_id = action.get("patient_id")

        if patient_id not in self.patients or doctor_id not in self.doctors:
            return

        # switching
        if doctor_id in self.busy_doctors:
            prev_id = self.doctor_current_patient.get(doctor_id)
            prev = self.patients.get(prev_id)

            penalty = 10
            new = self.patients.get(patient_id)

            if new and new["severity"] >= 9:
                penalty = 3

            if prev:
                penalty += min(prev["severity"], 5)
                if prev["can_die"]:
                    prev["time_left"] -= 5

            self.point -= penalty

        p = self.patients.pop(patient_id)

        self.busy_doctors[doctor_id] = p["time_takes"]
        self.doctor_current_patient[doctor_id] = patient_id
        if p["severity"] >= 9:
            self.point += 5
        self.point += 10  # simplified scoring

    def _update_doctors(self):
        finished = []
        for d in self.busy_doctors:
            self.busy_doctors[d] -= 1
            if self.busy_doctors[d] <= 0:
                finished.append(d)

        for d in finished:
            self.total_treated += 1
            self.point += 20
            del self.busy_doctors[d]
            self.doctor_current_patient.pop(d, None)

    def _update_patients(self):
        dead = []
        for pid, p in self.patients.items():
            p["time_left"] -= 1
            if p["time_left"] <= 0 and p["can_die"]:
                dead.append(pid)

        for pid in dead:
            self.total_died += 1
            self.point -= 1000
            del self.patients[pid]
    
