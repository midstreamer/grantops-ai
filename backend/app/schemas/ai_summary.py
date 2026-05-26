from pydantic import BaseModel, Field


class OpportunityAISummary(BaseModel):
    opportunity_summary: str = Field(..., description="Plain-English opportunity summary")
    why_it_fits: str = Field(..., description="Alignment with the research profile")
    concerns: str = Field(..., description="Risks or misalignments")
    recommended_framing: str = Field(..., description="Recommended narrative framing")
    recommended_next_actions: str = Field(..., description="Suggested next steps")
    possible_proposal_title: str = Field(..., description="Working proposal title")
