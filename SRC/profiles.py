from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict


@dataclass(frozen=True)
class Profile:
    key: str
    name: str
    data: Dict[str, Any]


def get_profiles_dir() -> Path:
    """
    Retourne le dossier /profiles à la racine du projet:
    .../agent-emploi/profiles
    SRC/ est à: .../agent-emploi/SRC
    """
    return Path(__file__).resolve().parents[1] / "profiles"


def list_available_profiles() -> Dict[str, Path]:
    """
    Renvoie un dict {key: filepath} où key est le nom de fichier sans extension.
    """
    profiles_dir = get_profiles_dir()
    if not profiles_dir.exists():
        return {}
    return {p.stem: p for p in sorted(profiles_dir.glob("*.json"))}


def load_profile(profile_key: str) -> Profile:
    """
    Charge un profil JSON. Si introuvable, retombe sur 'general' si possible.
    """
    available = list_available_profiles()

    chosen_key = profile_key if profile_key in available else "general"
    if chosen_key not in available:
        raise FileNotFoundError(
            f"Aucun profil trouvé. Attendu un fichier JSON dans {get_profiles_dir()}"
        )

    path = available[chosen_key]
    data = json.loads(path.read_text(encoding="utf-8"))

    name = str(data.get("name", chosen_key))
    return Profile(key=chosen_key, name=name, data=data)