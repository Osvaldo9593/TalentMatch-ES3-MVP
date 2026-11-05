from fastapi import APIRouter
from app.api.v1.endpoints import health, job_offers, cvs, evaluations, dashboard, auth

api_router = APIRouter()

# Register endpoints
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(job_offers.router, prefix="/job-offers", tags=["Job Offers"])
api_router.include_router(
    cvs.router,
    prefix="/job-offers/{job_offer_id}/cvs",
    tags=["Candidate CVs"]
)
api_router.include_router(
    evaluations.router,
    tags=["AI CV Evaluations"]
)
api_router.include_router(cvs.actions_router, prefix="/cvs", tags=["Candidate CV Actions"])

