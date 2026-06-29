import numpy as np
import os

import isaaclab.envs.mdp as mdp
from isaaclab.envs import ViewerCfg
from isaaclab.managers import SceneEntityCfg, TerminationTermCfg as DoneTermCfg
from isaaclab.utils import configclass

import instinctlab.envs.mdp as instinct_mdp
import instinctlab.tasks.shadowing.mdp as shadowing_mdp
import instinctlab.tasks.shadowing.perceptive.perceptive_env_cfg as perceptual_cfg
from instinctlab.assets.hu_d04 import (
    HU_D04_31DOF_CFG,
    HU_D04_ACTION_SCALE,
    HU_D04_31DOF_ACTUATORS,
    HU_D04_31DOF_LINKS,
)
from instinctlab.monitors import ActuatorMonitorTerm, MonitorTermCfg, ShadowingBasePosMonitorTerm
from instinctlab.motion_reference import MotionReferenceManagerCfg
from instinctlab.motion_reference.motion_files.amass_motion_cfg import AmassMotionCfg as AmassMotionCfgBase
from instinctlab.motion_reference.motion_files.terrain_motion_cfg import TerrainMotionCfg as TerrainMotionCfgBase
from instinctlab.motion_reference.utils import motion_interpolate_bilinear
from instinctlab.sensors import get_link_prim_targets

HU_D04_CFG = HU_D04_31DOF_CFG

MOTION_FOLDER = "/home/xf/InstinctLab-main/actions/50cm_kneeClimbStep"


@configclass
class TerrainMotionCfg(TerrainMotionCfgBase):
    path = os.path.expanduser(MOTION_FOLDER)
    metadata_yaml = os.path.expanduser(f"{MOTION_FOLDER}/metadata.yaml")
    max_origins_per_motion = 49

    ensure_link_below_zero_ground = False
    motion_start_from_middle_range = [0.0, 0.0]
    motion_start_height_offset = 0.0
    motion_bin_length_s = 1.0
    buffer_device = "output_device"
    motion_interpolate_func = motion_interpolate_bilinear
    velocity_estimation_method = "frontbackward"
    env_starting_stub_sampling_strategy = "concat_motion_bins"


@configclass
class AMASSMotionCfg(AmassMotionCfgBase):
    path = os.path.expanduser(MOTION_FOLDER)
    filtered_motion_selection_filepath = None
    ensure_link_below_zero_ground = False
    motion_start_from_middle_range = [0.0, 0.0]
    motion_start_height_offset = 0.0
    motion_bin_length_s = 1.0
    buffer_device = "output_device"
    motion_interpolate_func = motion_interpolate_bilinear
    velocity_estimation_method = "frontbackward"
    env_starting_stub_sampling_strategy = "concat_motion_bins"


motion_reference_cfg = MotionReferenceManagerCfg(
    prim_path="{ENV_REGEX_NS}/Robot/base_link",
    robot_model_path=HU_D04_CFG.spawn.asset_path,
    reference_prim_path="/World/envs/env_.*/RobotReference/base_link",
    link_of_interests=[
        "base_link",
        "left_shoulder_roll_link",
        "right_shoulder_roll_link",
        "left_elbow_link",
        "right_elbow_link",
        "left_wrist_yaw_link",
        "right_wrist_yaw_link",
        "left_hip_roll_link",
        "right_hip_roll_link",
        "left_knee_link",
        "right_knee_link",
        "left_ankle_roll_link",
        "right_ankle_roll_link",
    ],
    symmetric_augmentation_link_mapping=None,
    symmetric_augmentation_joint_mapping=None,
    symmetric_augmentation_joint_reverse_buf=None,
    frame_interval_s=0.1,
    update_period=0.02,
    num_frames=10,
    data_start_from="current_time",
    visualizing_robot_offset=(2.0, 0.0, 0.0),
    visualizing_robot_from="reference_frame",
    visualizing_marker_types=["relative_links", "links"],
    motion_buffers={
        "TerrainMotion": TerrainMotionCfg(),
    },
    mp_split_method="None",
)


@configclass
class HU_D04PerceptiveShadowingEnvCfg(perceptual_cfg.PerceptiveShadowingEnvCfg):
    scene: perceptual_cfg.PerceptiveShadowingSceneCfg = perceptual_cfg.PerceptiveShadowingSceneCfg(
        num_envs=4096,
        robot=HU_D04_CFG.replace(prim_path="{ENV_REGEX_NS}/Robot"),
        motion_reference=motion_reference_cfg,
    )

    def __post_init__(self):
        super().__post_init__()

        # Override camera prim_path to use base_link instead of torso_link
        self.scene.camera.prim_path = "{ENV_REGEX_NS}/Robot/base_link"
        self.scene.height_scanner.prim_path = "{ENV_REGEX_NS}/Robot/base_link"

        self.scene.camera.mesh_prim_paths.extend(get_link_prim_targets(HU_D04_31DOF_LINKS))

        self.scene.robot.actuators = HU_D04_31DOF_ACTUATORS
        self.actions.joint_pos.scale = HU_D04_ACTION_SCALE

        MOTION_NAME = list(self.scene.motion_reference.motion_buffers.keys())[0]
        self.scene.motion_reference.motion_buffers[MOTION_NAME].metadata_yaml = os.path.join(
            self.scene.motion_reference.motion_buffers[MOTION_NAME].path, "metadata.yaml"
        )
        self.scene.terrain.terrain_generator.sub_terrains["motion_matched"].path = (
            self.scene.motion_reference.motion_buffers[MOTION_NAME].path
        )
        self.scene.terrain.terrain_generator.sub_terrains["motion_matched"].metadata_yaml = os.path.join(
            self.scene.motion_reference.motion_buffers[MOTION_NAME].path, "metadata.yaml"
        )

        # match key links for observation terms
        self.observations.critic.link_pos.params["asset_cfg"].body_names = self.scene.motion_reference.link_of_interests
        self.observations.critic.link_rot.params["asset_cfg"].body_names = self.scene.motion_reference.link_of_interests

        # Override base_com event to use base_link instead of torso_link
        self.events.base_com = None

        # Override randomize_rigid_body_mass to use base_link instead of torso_link
        self.events.randomize_rigid_body_mass = None

        # Allow knee contact for kneelClimb task
        self.terminations.illegal_reset_contact = DoneTermCfg(
            func=instinct_mdp.illegal_reset_contact,
            time_out=True,
            params={
                "sensor_cfg": SceneEntityCfg(
                    "contact_forces",
                    body_names=[
                        r"^(?!left_ankle_roll_link$)(?!right_ankle_roll_link$)(?!left_wrist_yaw_link$)(?!right_wrist_yaw_link$)(?!left_knee_link$)(?!right_knee_link$).+$"
                    ],
                ),
                "threshold": 500,
                "episode_length_threshold": 2,
            },
        )

        self.run_name = "hu_d04Perceptive" + "".join(
            [
                (
                    "_concatMotionBins"
                    if self.scene.motion_reference.motion_buffers[MOTION_NAME].env_starting_stub_sampling_strategy
                    == "concat_motion_bins"
                    else "_independentMotionBins"
                ),
            ]
        )


@configclass
class HU_D04PerceptiveShadowingEnvCfg_PLAY(HU_D04PerceptiveShadowingEnvCfg):
    scene: perceptual_cfg.PerceptiveShadowingSceneCfg = perceptual_cfg.PerceptiveShadowingSceneCfg(
        num_envs=1,
        env_spacing=2.5,
        robot=HU_D04_CFG.replace(prim_path="{ENV_REGEX_NS}/Robot"),
        robot_reference=HU_D04_CFG.replace(prim_path="{ENV_REGEX_NS}/RobotReference"),
        motion_reference=motion_reference_cfg.replace(debug_vis=True),
    )

    viewer: ViewerCfg = ViewerCfg(
        eye=[1.5, 0.0, 1.5],
        lookat=[0.0, 0.0, 0.0],
        origin_type="asset_root",
        asset_name="robot",
    )

    def __post_init__(self):
        super().__post_init__()

        # deactivate adaptive sampling and start from the 0.0s of the motion
        self.curriculum.beyond_adaptive_sampling = None
        self.events.bin_fail_counter_smoothing = None
        MOTION_NAME = list(self.scene.motion_reference.motion_buffers.keys())[0]
        self.scene.motion_reference.motion_buffers[MOTION_NAME].motion_start_from_middle_range = [0.0, 0.0]
        self.scene.motion_reference.motion_buffers[MOTION_NAME].motion_bin_length_s = None
        self.scene.motion_reference.motion_buffers[MOTION_NAME].env_starting_stub_sampling_strategy = "independent"
        self.scene.motion_reference.motion_buffers[MOTION_NAME].metadata_yaml = os.path.join(
            self.scene.motion_reference.motion_buffers[MOTION_NAME].path, "metadata.yaml"
        )
        self.scene.terrain.terrain_generator.sub_terrains["motion_matched"].path = (
            self.scene.motion_reference.motion_buffers[MOTION_NAME].path
        )
        self.scene.terrain.terrain_generator.sub_terrains["motion_matched"].metadata_yaml = os.path.join(
            self.scene.motion_reference.motion_buffers[MOTION_NAME].path, "metadata.yaml"
        )

        self.scene.terrain.terrain_generator.num_rows = 6
        self.scene.terrain.terrain_generator.num_cols = 6

        self.scene.camera.debug_vis = True

        # remove some termination terms
        self.terminations.base_pos_too_far = None
        self.terminations.base_pg_too_far = None
        self.terminations.link_pos_too_far = None

        # remove some randomizations
        self.events.add_joint_default_pos = None
        self.events.base_com = None
        self.events.physics_material = None
        self.events.push_robot = None
        self.events.reset_robot.params["randomize_pose_range"]["x"] = [0.0] * 2
        self.events.reset_robot.params["randomize_pose_range"]["y"] = [0.0] * 2
        self.events.reset_robot.params["randomize_pose_range"]["z"] = (0.0, 0.0)
        self.events.reset_robot.params["randomize_pose_range"]["roll"] = (0.0, 0.0)
        self.events.reset_robot.params["randomize_pose_range"]["pitch"] = (0.0, 0.0)
        self.events.reset_robot.params["randomize_pose_range"]["yaw"] = (0.0, 0.0)
        self.events.reset_robot.params["randomize_velocity_range"]["x"] = (0.0, 0.0)
        self.events.reset_robot.params["randomize_velocity_range"]["y"] = (0.0, 0.0)
        self.events.reset_robot.params["randomize_velocity_range"]["z"] = (0.0, 0.0)
        self.events.reset_robot.params["randomize_velocity_range"]["roll"] = (0.0, 0.0)
        self.events.reset_robot.params["randomize_velocity_range"]["pitch"] = (0.0, 0.0)
        self.events.reset_robot.params["randomize_velocity_range"]["yaw"] = (0.0, 0.0)
        self.events.reset_robot.params["randomize_joint_pos_range"] = (0.0, 0.0)

        # add some additional monitor terms
        self.monitors.shadowing_position_stats = MonitorTermCfg(
            func=ShadowingBasePosMonitorTerm,
            params=dict(
                robot_cfg=SceneEntityCfg("robot"),
                motion_reference_cfg=SceneEntityCfg("motion_reference"),
            ),
        )
        self.monitors.right_ankle_pitch_actuator = MonitorTermCfg(
            func=ActuatorMonitorTerm,
            params=dict(
                asset_cfg=SceneEntityCfg("robot", joint_names="right_ankle_pitch.*"),
            ),
        )
        self.monitors.left_ankle_pitch_actuator = MonitorTermCfg(
            func=ActuatorMonitorTerm,
            params=dict(
                asset_cfg=SceneEntityCfg("robot", joint_names="left_ankle_pitch.*"),
            ),
        )
        self.monitors.right_knee_actuator = MonitorTermCfg(
            func=ActuatorMonitorTerm,
            params=dict(
                asset_cfg=SceneEntityCfg("robot", joint_names="right_knee.*"),
            ),
        )
        self.monitors.left_knee_actuator = MonitorTermCfg(
            func=ActuatorMonitorTerm,
            params=dict(
                asset_cfg=SceneEntityCfg("robot", joint_names="left_knee.*"),
            ),
        )
