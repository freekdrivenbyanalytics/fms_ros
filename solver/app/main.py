import logging
from contextlib import asynccontextmanager
from datetime import date

from fastapi import FastAPI

from app.schemas import EmployeeIn, OptimizeRequest, OptimizeResponse, VisitIn
from app.solve import solve_schedule

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _warm_up() -> None:
    """Solve a trivial problem once at startup.

    Timefold compiles the constraint provider into JVM bytecode the first time
    a solver actually runs; doing that here means a user's first real
    "Run Optimization" click isn't the one paying for it.
    """
    warm_up_request = OptimizeRequest(
        employees=[
            EmployeeIn(
                id=0,
                work_start_minutes=0,
                work_end_minutes=60,
                skill_ids=[],
                region_ids=[0],
                latitude=0.0,
                longitude=0.0,
            )
        ],
        visits=[
            VisitIn(
                id=0,
                requested_date=date(2000, 1, 1),
                duration_minutes=15,
                required_skill_ids=[],
                region_id=0,
                latitude=0.0,
                longitude=0.0,
            )
        ],
        time_limit_seconds=1,
    )
    solve_schedule(warm_up_request)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        _warm_up()
        logger.info("Solver warm-up complete")
    except Exception:
        logger.warning("Solver warm-up failed; first real request will be slower", exc_info=True)
    yield


app = FastAPI(title="fms_ros solver", lifespan=lifespan)


@app.post("/optimize", response_model=OptimizeResponse)
def optimize(payload: OptimizeRequest) -> OptimizeResponse:
    return solve_schedule(payload)
