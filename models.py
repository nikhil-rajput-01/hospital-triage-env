from pydantic import BaseModel
from typing import List, Dict, Optional


class Patient(BaseModel):
    id: int
    condition_id: int
    severity: float
    time_left: float


class Doctor(BaseModel):
    id: int
    type: str
    busy: bool


class State(BaseModel):
    patients: List[Patient]
    doctors: List[Doctor]
    time: int


class Action(BaseModel):
    type: str
    doctor_id: Optional[int] = None
    patient_id: Optional[int] = None


class StepResponse(BaseModel):
    state: State
    reward: float
    done: bool
    info: Dict