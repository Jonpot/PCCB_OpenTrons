"""
This script quickly boots the OT, captures a snapshot of the plate, and
saves the RGB results to a csv.
"""
OT_NUMBER = 6

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from camera.camera_w_calibration import PlateProcessor
from color_matching.robot.ot2_utils import OT2Manager

def main():
    """
    Main function to capture a snapshot of the plate and save the results.
    """
    info_path = f"secret/OT_{OT_NUMBER}/info.json"
    try:
        with open(info_path) as f:
            info = json.load(f)
    except Exception as e:
        raise SystemExit(f"Failed to read {info_path}: {e}")

    local_ip = info.get("local_ip")
    local_pw = info.get("local_password")
    local_pw = None if local_pw in (None, "None") else local_pw
    remote_ip = info.get("remote_ip")
    remote_pw = info.get("remote_password")

    remote_pw = None if remote_pw in (None, "None") else remote_pw
    local_key = f"secret/OT_{OT_NUMBER}/ot2_ssh_key"
    remote_key = f"secret/OT_{OT_NUMBER}/ot2_ssh_key_remote"

    cam_index = info.get("cam_index", 2)
    
    PlateProcessor().process_image(
        cam_index=cam_index,
        calib=f"secret/OT_{OT_NUMBER}/calibration.json"
    )

    try:
        robot = OT2Manager(hostname=local_ip,
                            username="root",
                            password=local_pw,
                            key_filename=local_key,
                            bypass_startup_key=True)
        print("Connected to OT2 locally.")
    except Exception as e:
        print(f"Local connection failed: {e}. Trying remote...")
        robot = OT2Manager(hostname=remote_ip,
                            username="root",
                            password=remote_pw,
                            key_filename=remote_key,
                            bypass_startup_key=True)
        print("Connected to OT2 remotely.")

    robot.add_turn_on_lights_action()
    robot.execute_actions_on_remote()

    plate_num = 0
    while input("Press Enter to capture and save a snapshot ('exit' to exit)...") != 'exit':
        print(f"Capturing snapshot for plate {plate_num}...")   
        plate_colors = PlateProcessor().process_image(
            cam_index=cam_index,
            calib=f"secret/OT_{OT_NUMBER}/calibration.json"
        )

        # Write the plate colors to a CSV file
        csv_path = f"quick_snapshot_plate_{plate_num}_colors_OT{OT_NUMBER}.csv"
        with open(csv_path, "w") as csv_file:
            csv_file.write("row,column,r,g,b\n")
            for row in range(plate_colors.shape[0]):
                for col in range(plate_colors.shape[1]):
                    r, g, b = plate_colors[row, col]
                    csv_file.write(f"{row},{col},{r},{g},{b}\n")

        plate_num += 1

    robot.add_turn_off_lights_action()
    robot.add_close_action()
    robot.execute_actions_on_remote()


if __name__ == "__main__":
    main()