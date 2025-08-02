from pydantic import BaseModel

class StudentAssociationRequest(BaseModel):
    invitation_code: str