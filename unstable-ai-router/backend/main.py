import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import load_config
from app.services.classification_service import ClassificationService
from app.services.llm.execution_factory import create_llm_service

load_dotenv(override=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = load_config()
    llm_service = create_llm_service(config)
    app.state.config = config
    app.state.classification_service = ClassificationService(
        llm=llm_service,
        execution_mode=config.execution_mode,
    )

    if config.execution_mode == "real_llm" and config.openai_api_key:
        from app.services.reliable_classification_service import ReliableClassificationService
        app.state.reliable_service = ReliableClassificationService(
            api_key=config.openai_api_key,
            execution_mode=config.execution_mode,
        )
        logger.info("Reliable classification service ready (Situation 3)")
    else:
        app.state.reliable_service = None
        logger.info("Reliable classification service disabled (demo_mode)")

    logger.info("Service ready — mode=%s", config.execution_mode)

    yield

    logger.info("Shutting down")


app = FastAPI(
    title="AI Quality Engineering Lab",
    description="Intent Classification & Routing Instability Simulator",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")
