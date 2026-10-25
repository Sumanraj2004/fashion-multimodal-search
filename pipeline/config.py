"""Paths used by reproducible pipeline stages."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PipelinePaths:
    """Filesystem layout for catalog artifacts."""

    root: Path = Path("data")

    @property
    def raw(self) -> Path:
        return self.root / "raw"

    @property
    def processed(self) -> Path:
        return self.root / "processed"

    @property
    def artifacts(self) -> Path:
        return self.root / "artifacts"

    def ensure_directories(self) -> None:
        """Create the expected artifact directories."""

        for path in (self.raw, self.processed, self.artifacts):
            path.mkdir(parents=True, exist_ok=True)
