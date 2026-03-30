import random
import time

class HospitalEnv:
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
            "patients": list(self.patients.values()),
            "doctors": list(self.busy_doctors.keys()),
            "time": self.step_count
        }

    def generate_patient(self):
        if len(self.patients) >= self.config["max_patients"]:
            self.point -= 50
            return

        self.patient_counter += 1
        self.total_generated += 1

        severity = random.randint(1, 10)

        self.patients[self.patient_counter] = {
            "id": self.patient_counter,
            "severity": severity,
            "time_left": random.randint(10, 30),
            "time_takes": random.randint(2, 6),
            "can_die": severity >= 8,
            "arrival_time": time.time()
        }

    def step(self, action):
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

        return self.state(), self.point, done, {}

    def _assign(self, action):
        doctor_id = action.get("doctor_id")
        patient_id = action.get("patient_id")

        if patient_id not in self.patients:
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
    
