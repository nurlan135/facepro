import cv2
import numpy as np
import os

# Source (generated) -> Destination (assets/icons)
MAPPING = {
    "raw_icon_home_1765961061266.png": "icon_home.png",
    "raw_icon_camera_1765961186257.png": "icon_camera.png",
    "raw_icon_faces_1765961295373.png": "icon_faces.png",
    "raw_icon_logs_1765961386200.png": "icon_logs.png",
    "raw_icon_settings_1765961452348.png": "icon_settings.png",
    "raw_icon_users_mgmt_1765961495487.png": "icon_users_mgmt.png",
    "raw_icon_password_1765961562825.png": "icon_password.png",
    "raw_icon_logout_1765961651305.png": "icon_logout.png",
    "raw_icon_exit_1765961746592.png": "icon_exit.png",
    "raw_icon_add_face_1765961857631.png": "icon_add_face.png"
}

SRC_DIR = r"C:\Users\HP\.gemini\antigravity\brain\3c9216e1-9910-4473-b135-741160f671f9"
DST_DIR = r"c:\Users\HP\Projects\facepro\assets\icons"

if not os.path.exists(DST_DIR):
    os.makedirs(DST_DIR)

def process_icon(src_path, dst_path):
    # Read image
    img = cv2.imread(src_path)
    if img is None:
        print(f"Failed to load: {src_path}")
        return

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Check background brightness (average of 4 corners)
    h, w = gray.shape
    corners = [gray[0, 0], gray[0, w-1], gray[h-1, 0], gray[h-1, w-1]]
    avg_corner = sum(corners) / 4

    # If background is bright (white/light grey), invert
    if avg_corner > 127:
        print(f"  > Detected light background ({avg_corner}), inverting...")
        gray = 255 - gray
    else:
        print(f"  > Detected dark background ({avg_corner})")

    # Check "Solidness" (Fill Ratio)
    # Count pixels that are considered "foreground" (bright)
    # If too many pixels are bright, it's likely a solid block/filled shape.
    _, binary = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY)
    fill_ratio = np.count_nonzero(binary) / (h * w)
    
    print(f"  > Fill Ratio: {fill_ratio:.2f}")

    if fill_ratio > 0.35: # If more than 35% is filled, convert to outline
        print("  > Auto-converting filled shape to outline...")
        kernel = np.ones((3,3), np.uint8)
        # Morphological Gradient = Dilation - Erosion (Extracts edges)
        gray = cv2.morphologyEx(gray, cv2.MORPH_GRADIENT, kernel)
        # Boost contrast of the edges
        gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)

    # SPECIAL HANDLING FOR PROFILE ICON which has persistent checkerboard issues
    if "icon_profile" in dst_path:
        print("  > Special profile icon cleanup...")
        # Hard threshold: Keep only very bright pixels (the white circle/person)
        _, gray = cv2.threshold(gray, 180, 255, cv2.THRESH_TOZERO)
        # Re-binarize to clear faint checkerboard patterns
        _, gray = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY)
        # Smooth edges
        gray = cv2.GaussianBlur(gray, (3, 3), 0)

    # Create solid white RGB channels
    white_img = np.zeros((h, w, 3), dtype=np.uint8)
    white_img[:] = (255, 255, 255)

    # Use grayscale brightness as alpha channel
    # 1. Normalize grayscale to full dynamic range (makes brightest pixels white)
    gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)
    
    # 2. Threshold to clean up background noise
    _, alpha = cv2.threshold(gray, 50, 255, cv2.THRESH_TOZERO)
    
    # 3. Boost alpha curves to make it "solid" faster
    # Any pixel > 100 becomes 255 (solid), smooth transition for edges
    # logic: if alpha > 128 -> 255 else alpha * 2
    # Simplified: Threshold binary + blur for softness? 
    # Or just standard power curve but stronger.
    
    # Let's try aggressive sharpening of opacity
    # Scale alpha: values 50..255 map to 0..255
    alpha = cv2.normalize(alpha, None, 0, 255, cv2.NORM_MINMAX)
    
    # Gamma correction to push mid-tones to white
    alpha = cv2.pow(alpha / 255.0, 0.5) * 255.0 # Gamma < 1 makes things brighter/more opaque
    alpha = alpha.astype(np.uint8)

    # Merge: White Color + Derived Alpha
    b, g, r = cv2.split(white_img)
    rgba = cv2.merge([b, g, r, alpha])

    # Save
    cv2.imwrite(dst_path, rgba)
    print(f"Processed: {dst_path}")

def main():
    print("Processing icons...")
    for src_name, dst_name in MAPPING.items():
        src = os.path.join(SRC_DIR, src_name)
        dst = os.path.join(DST_DIR, dst_name)
        process_icon(src, dst)
    print("Done.")

if __name__ == "__main__":
    main()
