import cv2
import numpy as np

def create_clean_profile_icon():
    # Create a blank transparent image (256x256)
    size = 256
    img = np.zeros((size, size, 4), dtype=np.uint8)

    # Define colors
    white = (255, 255, 255, 255) # RGBA
    
    # Center coordinates
    center = (size // 2, size // 2)
    radius = 100
    
    # 1. Draw Outer Circle (Ring)
    # Thickness = 10
    cv2.circle(img, center, radius, white, 10, lineType=cv2.LINE_AA)

    # 2. Draw Head (Solid Circle)
    head_radius = 40
    head_center = (size // 2, size // 2 - 20)
    cv2.circle(img, head_center, head_radius, white, -1, lineType=cv2.LINE_AA)

    # 3. Draw Body (Half Ellipse/Circle)
    # We will draw a filled ellipse and clip it to look like shoulders
    body_center = (size // 2, size // 2 + 50)
    body_axes = (60, 40) # Width, Height
    cv2.ellipse(img, body_center, body_axes, 0, 180, 360, white, -1, lineType=cv2.LINE_AA)

    # Save
    dst_path = r"c:\Users\HP\Projects\facepro\assets\icons\icon_profile.png"
    cv2.imwrite(dst_path, img)
    print(f"Created clean profile icon at: {dst_path}")

if __name__ == "__main__":
    create_clean_profile_icon()
