from pymycobot.mycobot import MyCobot
from pymycobot.genre import Angle, Coord
import time

# Initialize the MyCobot connection
mc = MyCobot('COM7', 115200)

# Power on the robotic arm
mc.power_on()
print("Robotic arm powered on")

# Check connection status
if mc.is_controller_connected() != 1:
    print("Error: Not connected to controller")
    exit()

# Set movement speed (0-100)
mc.set_speed(50)

# Example 1: Move joints to specific angles
print("Moving joints to home position")
angles = [0, 0, 0, 0, 0, 0]
mc.send_angles(angles, 50)

# Wait for movement to complete
time.sleep(3)

# Example 2: Get current joint angles
current_angles = mc.get_angles()
print("Current joint angles:", current_angles)

# Example 3: Move to specific coordinates
print("Moving to coordinates [100, -100, 100, 0, 0, 0]")
coords = [100, -100, 100, 0, 0, 0]
mc.send_coords(coords, 50, 0)

time.sleep(3)

# Example 4: Control the gripper
print("Opening gripper")
mc.set_gripper_state(0, 50)  # 0 = open, 1 = close
time.sleep(2)

print("Closing gripper")
mc.set_gripper_state(1, 50)
time.sleep(2)

# Example 5: Jog control
print("Jogging joint 2")
mc.jog_angle(2, 1, 30)  # Joint 2, increase angle, speed 30
time.sleep(2)
mc.jog_stop()

# Example 6: Set RGB light color
print("Setting RGB light to blue")
mc.set_color(0, 0, 255)  # R, G, B values (0-255)

# Example 7: Check if moving
print("Is moving?", "Yes" if mc.is_moving() == 1 else "No")

# Example 8: Get gripper value
gripper_value = mc.get_gripper_value()
print("Gripper value:", gripper_value)

# Return to home position
print("Returning to home position")
mc.send_angles([0, 0, 0, 0, 0, 0], 50)
time.sleep(3)

# Power off the robotic arm
mc.power_off()
print("Robotic arm powered off")