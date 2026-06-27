import os
from dataclasses import dataclass
from pathlib import Path

VALID_MODES = frozenset({"real_llm", "demo_mode"})

_DATASETS_DIR = Path(__file__).parent / "datasets"


@dataclass(frozen=True)
class Config:
    execution_mode: str          # "real_llm" | "demo_mode"
    openai_api_key: str
    demo_scenarios_path: str


def load_config() -> Config:
    mode = os.getenv("EXECUTION_MODE", "real_llm").lower().strip()

    if mode not in VALID_MODES:
        raise ValueError(
            f"Invalid EXECUTION_MODE={mode!r}. Valid values: {sorted(VALID_MODES)}"
        )

    api_key = os.getenv("OPENAI_API_KEY", "")
    if mode == "real_llm" and not api_key:
        raise RuntimeError("OPENAI_API_KEY is required when EXECUTION_MODE=real_llm")

    return Config(
        execution_mode=mode,
        openai_api_key=api_key,
        demo_scenarios_path=str(_DATASETS_DIR / "demo_scenarios.json"),
    )
