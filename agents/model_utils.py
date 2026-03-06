import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ModelArtifactsError(FileNotFoundError):
    """Raised when model artifacts are missing or invalid."""


@dataclass(frozen=True)
class ModelSpec:
    key: str
    default_dir: str
    required_files: List[str]
    weight_files_any: List[str]
    metadata_file: str = "metadata.json"


MODEL_SPECS: Dict[str, ModelSpec] = {
    "bert_detection": ModelSpec(
        key="bert_detection",
        default_dir="models/distilbert_log_classifier",
        required_files=["config.json", "vocab.txt"],
        weight_files_any=["model.safetensors", "pytorch_model.bin"],
    ),
    "correlation": ModelSpec(
        key="correlation",
        default_dir="models/correlation_roberta",
        required_files=["config.json", "vocab.json", "merges.txt"],
        weight_files_any=["model.safetensors", "pytorch_model.bin"],
    ),
    "ti_enrichment": ModelSpec(
        key="ti_enrichment",
        default_dir="models/ti_enrichment_bert",
        required_files=["config.json", "vocab.txt"],
        weight_files_any=["model.safetensors", "pytorch_model.bin"],
    ),
    "response": ModelSpec(
        key="response",
        default_dir="models/response_albert",
        required_files=["config.json", "spiece.model"],
        weight_files_any=["model.safetensors", "pytorch_model.bin"],
    ),
}


def _read_json(file_path: Path) -> dict:
    with file_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _resolve_candidates(model_path: Optional[str], default_dir: str) -> List[Path]:
    candidates: List[Path] = []

    if model_path:
        requested = Path(model_path)
        if requested.is_absolute():
            candidates.append(requested)
        else:
            candidates.append((PROJECT_ROOT / requested).resolve())
            candidates.append((Path.cwd() / requested).resolve())

    candidates.append((PROJECT_ROOT / default_dir).resolve())
    candidates.append((Path.cwd() / default_dir).resolve())

    unique_candidates: List[Path] = []
    seen = set()
    for candidate in candidates:
        candidate_str = str(candidate)
        if candidate_str not in seen:
            unique_candidates.append(candidate)
            seen.add(candidate_str)

    return unique_candidates


def resolve_model_dir(spec_key: str, model_path: Optional[str] = None) -> Path:
    if spec_key not in MODEL_SPECS:
        raise ValueError(f"Unknown model spec key: {spec_key}")

    spec = MODEL_SPECS[spec_key]
    candidates = _resolve_candidates(model_path, spec.default_dir)

    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            return candidate

    checked = "\n".join(str(path) for path in candidates)
    raise ModelArtifactsError(
        f"Model directory not found for '{spec_key}'. Checked:\n{checked}"
    )


def validate_model_artifacts(spec_key: str, model_path: Optional[str] = None) -> Path:
    model_dir = resolve_model_dir(spec_key, model_path)
    spec = MODEL_SPECS[spec_key]

    missing_files: List[str] = []
    for file_name in spec.required_files:
        if not (model_dir / file_name).exists():
            missing_files.append(file_name)

    if not any((model_dir / weight_name).exists() for weight_name in spec.weight_files_any):
        missing_files.append(f"one of {spec.weight_files_any}")

    if missing_files:
        raise ModelArtifactsError(
            f"Missing artifacts for '{spec_key}' at {model_dir}: {', '.join(missing_files)}"
        )

    return model_dir


def get_model_metadata(model_dir: Path, fallback_max_length: int = 128) -> dict:
    metadata_file = model_dir / "metadata.json"
    config_file = model_dir / "config.json"

    metadata: dict = {}
    if metadata_file.exists():
        metadata = _read_json(metadata_file)
    elif config_file.exists():
        config_data = _read_json(config_file)
        if "label_map" in config_data and "id_to_label" in config_data:
            metadata = {
                "label_map": config_data.get("label_map", {}),
                "id_to_label": config_data.get("id_to_label", {}),
                "max_length": config_data.get("max_length", fallback_max_length),
                "model_name": config_data.get("model_name"),
            }
        elif "label2id" in config_data and "id2label" in config_data:
            label_map = {
                str(label): int(idx)
                for label, idx in config_data.get("label2id", {}).items()
            }
            id_to_label = {
                str(idx): str(label)
                for idx, label in config_data.get("id2label", {}).items()
            }
            metadata = {
                "label_map": label_map,
                "id_to_label": id_to_label,
                "max_length": config_data.get("max_position_embeddings", fallback_max_length),
                "model_name": config_data.get("_name_or_path"),
            }

    if not metadata or "label_map" not in metadata or "id_to_label" not in metadata:
        raise ModelArtifactsError(
            f"Model metadata missing for {model_dir}. Expected metadata.json or label mapping fields in config.json"
        )

    normalized_label_map = {
        str(label): int(idx) for label, idx in metadata["label_map"].items()
    }
    normalized_id_to_label = {
        int(idx): str(label) for idx, label in metadata["id_to_label"].items()
    }

    return {
        "label_map": normalized_label_map,
        "id_to_label": normalized_id_to_label,
        "max_length": int(metadata.get("max_length", fallback_max_length)),
        "model_name": metadata.get("model_name"),
    }


def validate_all_models() -> Dict[str, str]:
    resolved: Dict[str, str] = {}
    failures: List[str] = []

    for spec_key in MODEL_SPECS:
        try:
            model_dir = validate_model_artifacts(spec_key)
            resolved[spec_key] = str(model_dir)
        except ModelArtifactsError as error:
            failures.append(str(error))

    if failures:
        joined = "\n- " + "\n- ".join(failures)
        raise ModelArtifactsError(f"Model startup validation failed:{joined}")

    return resolved
