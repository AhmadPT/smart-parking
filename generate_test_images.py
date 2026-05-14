#!/usr/bin/env python3
"""Generate test images with license plates for fallback mode."""
import cv2
import numpy as np
from pathlib import Path

def create_test_plate_image(plate_text, filename):
    """Create a test image with a license plate."""
    # Create blank image
    img = np.ones((480, 640, 3), dtype=np.uint8) * 200
    
    # Create a license plate (white rectangle with text)
    plate_height = 60
    plate_width = 200
    x = (img.shape[1] - plate_width) // 2
    y = (img.shape[0] - plate_height) // 2
    
    # Draw plate background
    cv2.rectangle(img, (x, y), (x + plate_width, y + plate_height), (255, 255, 255), -1)
    cv2.rectangle(img, (x, y), (x + plate_width, y + plate_height), (0, 0, 0), 2)
    
    # Draw plate text
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1.2
    font_thickness = 2
    
    text_size = cv2.getTextSize(plate_text, font, font_scale, font_thickness)[0]
    text_x = x + (plate_width - text_size[0]) // 2
    text_y = y + (plate_height + text_size[1]) // 2
    
    cv2.putText(img, plate_text, (text_x, text_y), font, font_scale, (0, 0, 0), font_thickness)
    
    # Save image
    cv2.imwrite(filename, img)
    print(f"Created {filename} with plate: {plate_text}")

# Create output directory
test_frames_dir = Path(__file__).parent / 'media' / 'test_frames'
test_frames_dir.mkdir(parents=True, exist_ok=True)

# Use actual registered plate numbers from seed_parking
test_plates = [
    '16TAC123',
    '16TZA456',
    '16ALD789',
    '16BAB012',
    '16BOV345',
]

for i, plate in enumerate(test_plates):
    filename = test_frames_dir / f'test_plate_{i+1}.jpg'
    create_test_plate_image(plate, str(filename))

print(f"\nGenerated {len(test_plates)} test images in {test_frames_dir}")

