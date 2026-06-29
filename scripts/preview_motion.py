"""Preview motion reference data in Isaac Sim."""

from isaaclab.app import AppLauncher
import argparse

parser = argparse.ArgumentParser(description="Preview motion reference.")
parser.add_argument("--num_envs", type=int, default=1)
AppLauncher.add_app_launcher_args(parser)
args = parser.parse_args()

app_launcher = AppLauncher(args)
simulation_app = app_launcher.app

import torch
import isaaclab.sim as sim_utils
from isaaclab.assets import ArticulationCfg
from isaaclab.envs import ViewerCfg
from isaaclab.scene import InteractiveScene, InteractiveSceneCfg
from isaaclab.sim import SimulationContext
from isaaclab.utils import configclass

from instinctlab.assets.hu_d04 import HU_D04_31DOF_CFG
from instinctlab.motion_reference import MotionReferenceManager
from instinctlab.motion_reference.motion_files.terrain_motion_cfg import TerrainMotionCfg
from instinctlab.motion_reference import MotionReferenceManagerCfg
from instinctlab.motion_reference.utils import motion_interpolate_bilinear
from instinctlab.assets import AssetBaseCfg

import os

MOTION_FOLDER = "/home/xf/InstinctLab-main/actions/50cm_kneeClimbStep"


@configclass
class PreviewTerrainMotionCfg(TerrainMotionCfg):
    path = MOTION_FOLDER
    metadata_yaml = os.path.join(MOTION_FOLDER, "metadata.yaml")
    max_origins_per_motion = 49
    ensure_link_below_zero_ground = False
    motion_start_from_middle_range = [0.0, 0.0]
    motion_start_height_offset = 0.0
    motion_bin_length_s = None  # Play full motion
    buffer_device = "output_device"
    motion_interpolate_func = motion_interpolate_bilinear
    velocity_estimation_method = "frontbackward"
    env_starting_stub_sampling_strategy = "independent"


motion_cfg = MotionReferenceManagerCfg(
    prim_path="{ENV_REGEX_NS}/Robot/base_link",
    robot_model_path=HU_D04_31DOF_CFG.spawn.asset_path,
    reference_prim_path="/World/envs/env_.*/RobotReference/base_link",
    link_of_interests=[
        "base_link", "left_shoulder_roll_link", "right_shoulder_roll_link",
        "left_elbow_link", "right_elbow_link", "left_wrist_yaw_link", "right_wrist_yaw_link",
        "left_hip_roll_link", "right_hip_roll_link", "left_knee_link", "right_knee_link",
        "left_ankle_roll_link", "right_ankle_roll_link",
    ],
    frame_interval_s=0.1, update_period=0.02, num_frames=10,
    data_start_from="current_time",
    visualizing_robot_offset=(0.0, 0.0, 0.0),
    visualizing_robot_from="reference_frame",
    visualizing_marker_types=["relative_links", "links"],
    motion_buffers={"TerrainMotion": PreviewTerrainMotionCfg()},
    mp_split_method="None",
    debug_vis=True,
)


@configclass
class PreviewSceneCfg(InteractiveSceneCfg):
    ground = AssetBaseCfg(prim_path="/World/defaultGroundPlane", spawn=sim_utils.GroundPlaneCfg())
    dome_light = AssetBaseCfg(prim_path="/World/Light", spawn=sim_utils.DomeLightCfg(intensity=3000.0))
    robot = HU_D04_31DOF_CFG.replace(prim_path="{ENV_REGEX_NS}/Robot")
    robot_reference = HU_D04_31DOF_CFG.replace(prim_path="{ENV_REGEX_NS}/RobotReference")
    motion_reference = motion_cfg


def main():
    sim_cfg = sim_utils.SimulationCfg(dt=0.005, device=args.device)
    sim = SimulationContext(sim_cfg)
    sim.set_camera_view(eye=[2.0, 2.0, 2.0], target=[0.0, 0.0, 0.5])

    scene_cfg = PreviewSceneCfg(num_envs=args.num_envs, env_spacing=4.0, replicate_physics=False)
    scene = InteractiveScene(scene_cfg)
    sim.reset()

    robot = scene["robot"]
    motion_ref: MotionReferenceManager = scene["motion_reference"]
    motion_ref.match_scene(scene)

    print("[INFO] Playing motion reference. Press Ctrl+C to stop.")
    step = 0
    while simulation_app.is_running():
        frame = motion_ref.reference_frame

        # Drive robot reference to match motion
        robot.write_root_pose_to_sim(
            torch.cat([frame.base_pos_w[:, 0], frame.base_quat_w[:, 0]], dim=-1)
        )
        robot.write_joint_state_to_sim(frame.joint_pos[:, 0], frame.joint_vel[:, 0])
        robot.write_root_velocity_to_sim(torch.zeros(robot.num_instances, 6, device="cuda"))

        # Reset when exhausted
        if not motion_ref.data.validity.any(dim=-1).all():
            reset_ids = torch.where(~motion_ref.data.validity.any(dim=-1))[0]
            motion_ref.reset(reset_ids)
            print(f"[INFO] Motion reset at step {step}")

        sim.render()
        scene.update(sim.get_physics_dt())
        step += 1

    simulation_app.close()


if __name__ == "__main__":
    main()
