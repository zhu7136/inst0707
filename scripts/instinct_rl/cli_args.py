from __future__ import annotations

import argparse
import os
import yaml
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from instinctlab.utils.wrappers.instinct_rl import InstinctRlOnPolicyRunnerCfg


def add_instinct_rl_args(parser: argparse.ArgumentParser):
    """Add INSTINCT-RL arguments to the parser.

    Args:
        parser: The parser to add the arguments to.
    """
    # create a new argument group
    arg_group = parser.add_argument_group("instinct_rl", description="Arguments for Instinct-RL agent.")
    # -- experiment arguments
    arg_group.add_argument(
        "--experiment_name", type=str, default=None, help="Name of the experiment folder where logs will be stored."
    )
    arg_group.add_argument("--run_name", type=str, default=None, help="Run name suffix to the log directory.")
    # -- load arguments
    arg_group.add_argument("--resume", default=None, action="store_true", help="Whether to resume from a checkpoint.")
    arg_group.add_argument("--load_run", type=str, default=None, help="Name of the run folder to resume from.")
    arg_group.add_argument("--checkpoint", type=str, default=None, help="Checkpoint file to resume from.")
    # -- wandb arguments
    arg_group.add_argument("--use_wandb", default=None, action="store_true", help="Enable WandB logging.")
    arg_group.add_argument("--wandb_project", type=str, default=None, help="WandB project name.")
    arg_group.add_argument("--wandb_entity", type=str, default=None, help="WandB entity (user or team).")
    arg_group.add_argument("--wandb_group", type=str, default=None, help="WandB group name for grouping runs.")


def parse_instinct_rl_cfg(task_name: str, args_cli: argparse.Namespace) -> InstinctRlOnPolicyRunnerCfg:
    """Parse configuration for Instinct-RL agent based on inputs.

    Args:
        task_name: The name of the environment.
        args_cli: The command line arguments.

    Returns:
        The parsed configuration for Instinct-RL agent based on inputs.
    """
    from isaaclab_tasks.utils.parse_cfg import load_cfg_from_registry

    # load the default configuration
    instinctrl_cfg: InstinctRlOnPolicyRunnerCfg = load_cfg_from_registry(task_name, "instinct_rl_cfg_entry_point")
    instinctrl_cfg = update_instinct_rl_cfg(instinctrl_cfg, args_cli)
    return instinctrl_cfg


def update_instinct_rl_cfg(agent_cfg: InstinctRlOnPolicyRunnerCfg, args_cli: argparse.Namespace):
    """Update configuration for Instinct-RL agent based on inputs.

    Args:
        agent_cfg: The configuration for Instinct-RL agent.
        args_cli: The command line arguments.

    Returns:
        The updated configuration for Instinct-RL agent.
    """
    # override the default configuration with CLI arguments
    if hasattr(args_cli, "seed") and args_cli.seed is not None:
        agent_cfg.seed = args_cli.seed
    if args_cli.resume is not None:
        agent_cfg.resume = args_cli.resume
    if args_cli.load_run is not None:
        agent_cfg.load_run = args_cli.load_run
    if args_cli.checkpoint is not None:
        agent_cfg.load_checkpoint = args_cli.checkpoint
    if args_cli.run_name is not None:
        agent_cfg.run_name = args_cli.run_name
    # wandb arguments
    if args_cli.use_wandb is not None:
        agent_cfg.use_wandb = args_cli.use_wandb
    if args_cli.wandb_project is not None:
        agent_cfg.wandb_project = args_cli.wandb_project
    if args_cli.wandb_entity is not None:
        agent_cfg.wandb_entity = args_cli.wandb_entity
    if args_cli.wandb_group is not None:
        agent_cfg.wandb_group = args_cli.wandb_group

    return agent_cfg
