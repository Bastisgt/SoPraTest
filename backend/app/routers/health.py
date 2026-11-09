from fastapi import APIRouter

# All routes in this router live under /api, so the frontend proxy needs only one rule.
# The tag groups the endpoint under "health" in the Swagger docs.
router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    """
    Liveness probe: returns 200 as long as the app is running and routing works. Deliberately does not check the database or other dependencies.
    """
    return {"status": "ok"}
