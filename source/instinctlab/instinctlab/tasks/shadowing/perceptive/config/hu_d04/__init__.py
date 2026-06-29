import gymnasium as gym

from . import agents

task_entry = "instinctlab.tasks.shadowing.perceptive.config.hu_d04"

gym.register(
    id="Instinct-Perceptive-Shadowing-HU_D04-v0",
    entry_point="instinctlab.envs:InstinctRlEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{task_entry}.perceptive_shadowing_cfg:HU_D04PerceptiveShadowingEnvCfg",
        "instinct_rl_cfg_entry_point": f"{agents.__name__}.instinct_rl_ppo_cfg:HU_D04PerceptiveShadowingPPORunnerCfg",
    },
)

gym.register(
    id="Instinct-Perceptive-Shadowing-HU_D04-Play-v0",
    entry_point="instinctlab.envs:InstinctRlEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{task_entry}.perceptive_shadowing_cfg:HU_D04PerceptiveShadowingEnvCfg_PLAY",
        "instinct_rl_cfg_entry_point": f"{agents.__name__}.instinct_rl_ppo_cfg:HU_D04PerceptiveShadowingPPORunnerCfg",
    },
)

gym.register(
    id="Instinct-Perceptive-Vae-HU_D04-v0",
    entry_point="instinctlab.envs:InstinctRlEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{task_entry}.perceptive_vae_cfg:HU_D04PerceptiveVaeEnvCfg",
        "instinct_rl_cfg_entry_point": f"{agents.__name__}.instinct_rl_vae_cfg:HU_D04PerceptiveVaePPORunnerCfg",
    },
)

gym.register(
    id="Instinct-Perceptive-Vae-HU_D04-Play-v0",
    entry_point="instinctlab.envs:InstinctRlEnv",
    disable_env_checker=True,
    kwargs={
        "env_cfg_entry_point": f"{task_entry}.perceptive_vae_cfg:HU_D04PerceptiveVaeEnvCfg_PLAY",
        "instinct_rl_cfg_entry_point": f"{agents.__name__}.instinct_rl_vae_cfg:HU_D04PerceptiveVaePPORunnerCfg",
    },
)
