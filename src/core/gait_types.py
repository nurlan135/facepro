"""
FacePro Gait Recognition Types
Gait tanıma üçün data strukturları.
"""

import time
from typing import List
from dataclasses import dataclass, field

import numpy as np


@dataclass
class GaitBuffer:
    """Bir şəxs üçün silhouette buffer."""
    track_id: int
    silhouettes: List[np.ndarray] = field(default_factory=list)
    last_update: float = field(default_factory=time.time)


@dataclass
class GaitMatch:
    """Gait tanıma nəticəsi."""
    user_id: int
    user_name: str
    confidence: float
    embedding_id: int
