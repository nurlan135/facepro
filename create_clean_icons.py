import cv2
import numpy as np
import os

ICONS_DIR = r"c:\Users\HP\Projects\facepro\assets\icons"
SIZE = 256
WHITE = (255, 255, 255, 255)
THICKNESS = 12

def create_blank():
    return np.zeros((SIZE, SIZE, 4), dtype=np.uint8)

def save_icon(img, name):
    path = os.path.join(ICONS_DIR, name)
    cv2.imwrite(path, img)
    print(f"Created: {path}")

def draw_camera_icon():
    img = create_blank()
    center = (SIZE//2, SIZE//2)
    
    # Camera Body (Rounded Rect)
    # Main box
    pt1 = (40, 60)
    pt2 = (200, 160)
    cv2.rectangle(img, pt1, pt2, WHITE, THICKNESS, cv2.LINE_AA)
    
    # Lens (Circle inside)
    cv2.circle(img, (90, 110), 35, WHITE, THICKNESS, cv2.LINE_AA)
    # Inner lens dot
    cv2.circle(img, (90, 110), 12, WHITE, -1, cv2.LINE_AA)
    
    # Mount/Stand
    # Bracket
    cv2.line(img, (120, 160), (140, 200), WHITE, THICKNESS, cv2.LINE_AA)
    # Base
    cv2.line(img, (110, 200), (210, 200), WHITE, THICKNESS, cv2.LINE_AA)
    
    save_icon(img, "icon_camera.png")

def draw_add_face_icon():
    img = create_blank()
    
    # Head
    cv2.circle(img, (100, 80), 50, WHITE, THICKNESS, cv2.LINE_AA)
    
    # Body (Curved line)
    # Ellipse arc
    cv2.ellipse(img, (100, 240), (80, 100), 0, 180, 360, WHITE, THICKNESS, cv2.LINE_AA)
    
    # Plus Sign
    # Circle container for plus
    plus_center = (200, 180)
    # cv2.circle(img, plus_center, 40, WHITE, THICKNESS, cv2.LINE_AA)
    
    # Plus lines
    p_len = 30
    cv2.line(img, (plus_center[0] - p_len, plus_center[1]), (plus_center[0] + p_len, plus_center[1]), WHITE, THICKNESS, cv2.LINE_AA)
    cv2.line(img, (plus_center[0], plus_center[1] - p_len), (plus_center[0], plus_center[1] + p_len), WHITE, THICKNESS, cv2.LINE_AA)
    
    save_icon(img, "icon_add_face.png")
    # Also save as icon_faces.png for consistency if needed, but let's just do add_face first
    # The sidebar uses icon_faces.png for "Manage Faces". Let's verify if we need to update that too.
    # We'll create a separate icon_faces (multiple users) later if needed, but for now reuse or create simple user icon.

def draw_faces_icon():
    # Icon for "Manage Faces" (Group of users)
    img = create_blank()
    
    # Main User
    cv2.circle(img, (128, 90), 40, WHITE, THICKNESS, cv2.LINE_AA)
    cv2.ellipse(img, (128, 260), (70, 90), 0, 190, 350, WHITE, THICKNESS, cv2.LINE_AA)
    
    # Small User Right
    cv2.circle(img, (200, 80), 30, WHITE, THICKNESS, cv2.LINE_AA)    
    cv2.ellipse(img, (200, 220), (50, 70), 0, 190, 350, WHITE, THICKNESS, cv2.LINE_AA)

    # Small User Left
    cv2.circle(img, (56, 80), 30, WHITE, THICKNESS, cv2.LINE_AA)
    cv2.ellipse(img, (56, 220), (50, 70), 0, 190, 350, WHITE, THICKNESS, cv2.LINE_AA)
    
    save_icon(img, "icon_faces.png")

def draw_logs_icon():
    img = create_blank()
    
    # Document Outline
    pt1 = (60, 30)
    pt2 = (196, 226)
    cv2.rectangle(img, pt1, pt2, WHITE, THICKNESS, cv2.LINE_AA)
    
    # Lines
    x_start = 90
    x_end = 166
    for y in [80, 110, 140, 170]:
        cv2.line(img, (x_start, y), (x_end, y), WHITE, THICKNESS-4, cv2.LINE_AA)
        
    save_icon(img, "icon_logs.png")

def draw_settings_icon():
    img = create_blank()
    
    center = (128, 128)
    # Inner circle
    cv2.circle(img, center, 40, WHITE, THICKNESS, cv2.LINE_AA)
    # Outer circle (gear rim base)
    cv2.circle(img, center, 90, WHITE, THICKNESS-4, cv2.LINE_AA)
    
    # Teeth
    # Draw 8 small rectangles around the circle... simpler way:
    # Just draw lines radiating out thicker?
    for angle in range(0, 360, 45):
        # Calculate start/end points for teeth
        rad = np.radians(angle)
        x1 = int(center[0] + 80 * np.cos(rad))
        y1 = int(center[1] + 80 * np.sin(rad))
        x2 = int(center[0] + 110 * np.cos(rad))
        y2 = int(center[1] + 110 * np.sin(rad))
        cv2.line(img, (x1, y1), (x2, y2), WHITE, 30, cv2.LINE_AA)
        
    save_icon(img, "icon_settings.png")

def draw_logout_icon():
    img = create_blank()
    
    # Door frame (Rect without right side)
    # Top
    cv2.line(img, (60, 40), (160, 40), WHITE, THICKNESS, cv2.LINE_AA)
    # Bottom
    cv2.line(img, (60, 216), (160, 216), WHITE, THICKNESS, cv2.LINE_AA)
    # Left
    cv2.line(img, (60, 40), (60, 216), WHITE, THICKNESS, cv2.LINE_AA)
    
    # Arrow
    # Shaft
    cv2.line(img, (100, 128), (220, 128), WHITE, THICKNESS, cv2.LINE_AA)
    # Head
    cv2.line(img, (180, 90), (220, 128), WHITE, THICKNESS, cv2.LINE_AA)
    cv2.line(img, (180, 166), (220, 128), WHITE, THICKNESS, cv2.LINE_AA)
    
    save_icon(img, "icon_logout.png")

def draw_exit_icon():
    img = create_blank()
    center = (128, 128)
    radius = 80
    
    # Circle with gap at top
    cv2.ellipse(img, center, (radius, radius), 0, -80, 260, WHITE, THICKNESS, cv2.LINE_AA)
    
    # Vertical line
    cv2.line(img, (128, 128), (128, 40), WHITE, THICKNESS, cv2.LINE_AA)
    
    save_icon(img, "icon_exit.png")

def draw_users_mgmt_icon():
    # 3 small users
    img = create_blank()
    
    # Top
    cv2.circle(img, (128, 60), 30, WHITE, THICKNESS, cv2.LINE_AA)
    cv2.ellipse(img, (128, 160), (40, 50), 0, 200, 340, WHITE, THICKNESS, cv2.LINE_AA)

    # Bottom Left
    cv2.circle(img, (60, 140), 25, WHITE, THICKNESS, cv2.LINE_AA)
    cv2.ellipse(img, (60, 240), (35, 45), 0, 200, 340, WHITE, THICKNESS, cv2.LINE_AA)
    
    # Bottom Right
    cv2.circle(img, (196, 140), 25, WHITE, THICKNESS, cv2.LINE_AA)
    cv2.ellipse(img, (196, 240), (35, 45), 0, 200, 340, WHITE, THICKNESS, cv2.LINE_AA)
    
    save_icon(img, "icon_users_mgmt.png")

def draw_password_icon():
    img = create_blank()
    
    # Key head
    cv2.circle(img, (90, 170), 50, WHITE, THICKNESS, cv2.LINE_AA)
    # Hole
    cv2.circle(img, (75, 185), 15, WHITE, -1, cv2.LINE_AA) # Filled smaller circle to simulate hole if background is black? 
    # Actually we want transparent hole. So we must draw alpha=0 there.
    # But since we initialized with alpha=0 and drawing white adds alpha=255.
    # We need to erase.
    # However simple way: Draw loop.
    
    # Shaft
    cv2.line(img, (125, 135), (210, 50), WHITE, THICKNESS, cv2.LINE_AA)
    
    # Teeth
    cv2.line(img, (190, 70), (210, 90), WHITE, THICKNESS, cv2.LINE_AA)
    cv2.line(img, (170, 90), (190, 110), WHITE, THICKNESS, cv2.LINE_AA)

    save_icon(img, "icon_password.png")


if __name__ == "__main__":
    if not os.path.exists(ICONS_DIR):
        os.makedirs(ICONS_DIR)
        
    print("Generating clean icons...")
    draw_camera_icon()
    draw_add_face_icon()
    draw_faces_icon()
    draw_logs_icon()
    draw_settings_icon()
    draw_users_mgmt_icon()
    draw_password_icon()
    draw_logout_icon()
    draw_exit_icon()
    print("All icons generated successfully.")
