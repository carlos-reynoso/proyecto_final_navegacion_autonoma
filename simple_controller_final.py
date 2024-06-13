"""camera_pid controller."""

from controller import Display, Keyboard, Robot, Camera
from vehicle import Car, Driver
import numpy as np
import cv2
from datetime import datetime
import os
import csv


#Getting image from camera
def get_image(camera):
    raw_image = camera.getImage()  
    image = np.frombuffer(raw_image, np.uint8).reshape(
        (camera.getHeight(), camera.getWidth(), 4)
    )
    return image

#Image processing
def greyscale_cv2(image):
    gray_img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return gray_img

#Display image 
def display_image(display, image):
    # Image to display
    image_rgb = np.dstack((image, image,image,))
    # Display image
    image_ref = display.imageNew(
        image_rgb.tobytes(),
        Display.RGB,
        width=image_rgb.shape[1],
        height=image_rgb.shape[0],
    )
    display.imagePaste(image_ref, 0, 0, False)

#initial angle and speed 
manual_steering = 0
steering_angle = 0
angle = 0.0
speed = 30

# set target speed
def set_speed(kmh):
    global speed            #robot.step(50)
#update steering angle
def set_steering_angle(wheel_angle):
    global angle, steering_angle
    # Check limits of steering
    if (wheel_angle - steering_angle) > 0.1:
        wheel_angle = steering_angle + 0.1
    if (wheel_angle - steering_angle) < -0.1:
        wheel_angle = steering_angle - 0.1
    steering_angle = wheel_angle
  
    # limit range of the steering angle
    if wheel_angle > 0.5:
        wheel_angle = 0.5
    elif wheel_angle < -0.5:
        wheel_angle = -0.5
    # update steering angle
    angle = wheel_angle

#validate increment of steering angle
def change_steer_angle(inc):
    global manual_steering
    # Apply increment
    new_manual_steering = manual_steering + inc
    # Validate interval 
    if new_manual_steering <= 25.0 and new_manual_steering >= -25.0: 
        manual_steering = new_manual_steering
        set_steering_angle(manual_steering * 0.02)
    # Debugging
    if manual_steering == 0:
        print("going straight")
    else:
        turn = "left" if steering_angle < 0 else "right"
        print("turning {} rad {}".format(str(steering_angle),turn))



def save_image_steering_to_csv(filename, data):
    print('writing to csv ----------------------------------------------')
    """
    Saves name_image and steering information to a CSV file.
    :param filename: str - The name of the CSV file.
    :param data: list of dicts - A list where each element is a dictionary with 'name_image' and 'steering' keys.
    """
    # Define the header
    header = ['name_image', 'steering']
    
    # Open the file for writing
    with open(filename, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=header)
        
        # Write the header
        writer.writeheader()
        
        # Write the data
        for row in data:
            print(row)
            writer.writerow(row)

# main
def main():
    print("inside main")
    # Create the Robot instance.
    # robot = Car()
    driver = Driver()

    # Get the time step of the current world.
    timestep = int(driver.getBasicTimeStep())

    # Create camera instance
    camera = driver.getDevice("camera")
    camera.enable(timestep)  # timestep

    # processing display
    display_img = Display("display_image")

    #create keyboard instance
    keyboard=Keyboard()
    keyboard.enable(timestep)

    # Counter for taking a picture
    counter = 30 

    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Ensure the directory exists and has correct permissions
    image_dir = os.path.join(script_dir, "recorded_images")
    if not os.path.exists(image_dir):
        os.makedirs(image_dir, exist_ok=True)

    # Define a variable where we can store the data for the csv
    csv_data = []

    while driver.step() != -1:

        # Get image from camera
        image = get_image(camera)

        # Process and display image 
        grey_image = greyscale_cv2(image)
        display_image(display_img, grey_image)
        # Read keyboard
        key=keyboard.getKey()
        if key == keyboard.UP: #up
            set_speed(speed + 5.0)
            print("up")
        elif key == keyboard.DOWN: #down
            set_speed(speed - 5.0)
            print("down")
        elif key == keyboard.RIGHT: #right
            change_steer_angle(+.1)
            print("right")
        elif key == keyboard.LEFT: #left
            change_steer_angle(-.1)
            print("left")

        else:
            # Gradually return the steering angle to zero if no key is pressed
            if manual_steering > 0:
                change_steer_angle(-0.1)
            elif manual_steering < 0:
                change_steer_angle(+0.1)
        
        # Record image and save entry to the csv file
        # every time a picture is taken
        if(counter == 0):
            #filename with timestamp and saved in current directory
            current_datetime = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
            file_name = f"{current_datetime}.png"
            file_path = os.path.join(image_dir, file_name)
            print(f"Saving image to {file_path}")
            camera.saveImage(file_path, 1)

            # current steering angle
            current_steering = str(driver.steering_angle)
            #write the 
            csv_data.append({"steering":current_steering,"name_image":file_name})
                
            #update angle and speed
            driver.setSteeringAngle(angle)
            driver.setCruisingSpeed(speed)
            counter = 30
        counter-=1

    csv_file_path = os.path.join(image_dir, 'steering_data.csv')
    save_image_steering_to_csv(csv_file_path, csv_data)

if __name__ == "__main__":
    main()