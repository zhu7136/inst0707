"""WandB Logger for InstinctRL training."""

import os
from typing import Any

try:
    import wandb

    WANDB_AVAILABLE = True
except ImportError:
    WANDB_AVAILABLE = False


class WandBLogger:
    """Encapsulates WandB logging operations."""

    def __init__(self, enabled: bool = False, **kwargs):
        """
        Args:
            enabled: Whether to enable WandB logging
            **kwargs: Arguments passed to wandb.init()
        """
        self.enabled = enabled and WANDB_AVAILABLE
        self.run = None

        if self.enabled:
            self.run = wandb.init(**kwargs)

    def log(self, metrics: dict[str, Any], step: int | None = None):
        """Log scalar metrics."""
        if self.enabled and self.run is not None:
            wandb.log(metrics, step=int(step) if step is not None else None)

    def log_video(self, key: str, video_path: str, step: int | None = None):
        """Log a video file."""
        if self.enabled and self.run is not None:
            wandb.log({key: wandb.Video(video_path)}, step=int(step) if step is not None else None)

    def log_config(self, config: dict):
        """Update wandb config."""
        if self.enabled and self.run is not None:
            wandb.config.update(config)

    def finish(self):
        """Finish wandb run."""
        if self.enabled and self.run is not None:
            wandb.finish()
