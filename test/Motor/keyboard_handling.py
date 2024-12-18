import Jetson.GPIO as GPIO
import time
import keyboard
import subprocess

# Set the sudo password for running commands with sudo
sudo_password = "12"

# Function to run shell commands with the sudo password
def run_command(command):
    full_command = f"echo {sudo_password} | sudo -S {command}"
    subprocess.run(full_command, shell=True, check=True)
    
# Initialize GPIO pins and PWM
servo_pin = 33 # PWM pin for servo motor
dc_motor_pwm_pin = 32 # PWM pin for DC motor speed
dc_motor_dir_pin1 = 29 # Direction control pin 1
dc_motor_dir_pin2 = 31 # Direction control pin 2

GPIO.setmode(GPIO.BOARD)
GPIO.setup(servo_pin, GPIO.OUT)
GPIO.setup(dc_motor_pwm_pin, GPIO.OUT)
GPIO.setup(dc_motor_dir_pin1, GPIO.OUT)
GPIO.setup(dc_motor_dir_pin2, GPIO.OUT)

servo = GPIO.PWM(servo_pin, 50) # 50Hz for servo motor
dc_motor_pwm = GPIO.PWM(dc_motor_pwm_pin, 1000) # 1kHz for DC motor
servo.start(0)
dc_motor_pwm.start(0)

# Initialize default spped and steering angle
fixed_speed = 75 # Fixed speed at 75%
current_speed = 0 # Start speed at 0 for smooth acceleration
current_angle = 90 # Middle position for straight driving

# Function to set servo angle
def set_servo_angle(angle):
    duty_cycle = 2 + (angle / 18)
    servo.ChangeDutyCycle(duty_cycle)
    time.sleep(0.1)
    servo.ChangeDutyCycle(0) # Turn off signal to avoid jitter
    
# Funciton to set DC motor speed and direction
def set_dc_motor(speed, direction="forward"):
    if direction == "forward":
        GPIO.output(dc_motor_dir_pin1, GPIO.HIGH)
        GPIO.output(dc_motor_dir_pin2, GPIO.LOW)
    elif direction == "backward":
        GPIO.output(dc_motor_dir_pin1, GPIO.LOW)
        GPIO.output(dc_motor_dir_pin2, GPIO.HIGH)
    
    dc_motor_pwm.ChangeDutyCycle(speed)
    
# Main control Loop with acceleration and deleleration
try:
    set_servo_angle(current_angle)
    
    print("Use W/S to control speed and A/D for steering. press 'q' to quit.")
    while True:
        # Speed control with W and S keys
        if keyboard.is_pressed('w'):
            current_speed = min(current_speed + 5, fixed_speed) # Accelerate to fixed speed
            set_dc_motor(current_speed, "forward")
            print(f"Speed increased to: {current_speed}%")
        elif keyboard.is_pressed('s'):
            current_speed = min(current_speed + 5, fixed_speed) # Accelerate to fixed speed
            set_dc_motor(current_speed, "backward")
            print(f"Speed decreased to: {current_speed}%")
            
        # Steering control with A and D keys
        if keyboard.is_pressed('a'):
            current_angle = max(0, current_angle - 5) # Steer left up to 0 degrees
            set_servo_angle(current_angle)
            print(f"Steering angle: {current_angle}도 (Left)")
        elif keyboard.is_pressed('d'):
            current_angle = min(180, current_angle + 5) # steer right up to 180 dgress
            set_servo_angle(current_angle)
            print(f"Steering angle: {current_angle}도 (Right)")
            
        # Deceleration when no key is pressed
        if not (keyboard.is_pressed('w') or keyboard.is_pressed('s')):
            if current_speed > 0:
                current_speed = max(current_speed - 5, 0) # Gradually decrease speed to 0
                set_dc_motor(current_speed, "forward")
            elif current_speed < 0:
                current_speed = min(current_speed + 5, 0) # Gradually decrease speed to 0
                set_dc_motor(abs(current_speed), "backward")
            print(f"Decelerating to: {current_speed}%")
        
        # Quit program
        if keyboard.is_pressed('q'):
            print("Quit key pressed")
            break
        
        time.sleep(0.1) # Small delay for smooth control
        
finally:
    # stop all PWM and clean up GPIO
    servo.stop()
    dc_motor_pwm.stop()
    GPIO.cleanup()