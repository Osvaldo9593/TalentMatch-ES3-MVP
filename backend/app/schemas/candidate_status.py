from typing import Literal
from pydantic import BaseModel

ApplicationStatusValue = Literal["PENDIENTE", "EN_REVISION", "DESCARTADO", "SELECCIONADO"]


class CandidateStatusUpdate(BaseModel):
    status: ApplicationStatusValue
