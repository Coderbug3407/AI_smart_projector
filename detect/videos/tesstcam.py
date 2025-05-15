import cv2
import numpy as np

# Global variables to store mouse position and clicked points
mouse_x = 0
mouse_y = 0
clicked_points = []  # Array to store all clicked coordinates

def mouse_callback(event, x, y, flags, param):
    # Update global mouse position
    global mouse_x, mouse_y
    mouse_x = x
    mouse_y = y
    
    # Store coordinates when left mouse button is clicked
    if event == cv2.EVENT_LBUTTONDOWN:
        if len(clicked_points) < 4:  # Only store up to 4 points
            clicked_points.append((x, y))
            print(f"Point {len(clicked_points)} stored: ({x}, {y})")
        else:
            print("Already have 4 points. Press 'c' to clear and start over.")

def draw_rectangle(frame):
    if len(clicked_points) >= 4:
        # Draw lines between points in sequence
        for i in range(4):
            pt1 = clicked_points[i]
            pt2 = clicked_points[(i + 1) % 4]  # %4 to connect back to first point
            cv2.line(frame, pt1, pt2, (0, 255, 0), 2)  # Green lines
            
        # Calculate area of the rectangle (using simple method)
        width = int(((clicked_points[1][0] - clicked_points[0][0])**2 + 
                    (clicked_points[1][1] - clicked_points[0][1])**2)**0.5)
        height = int(((clicked_points[2][0] - clicked_points[1][0])**2 + 
                     (clicked_points[2][1] - clicked_points[1][1])**2)**0.5)
        area = width * height
        
        # Display area information
        cv2.putText(frame, f"Width: {width}px", (20, 90), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"Height: {height}px", (20, 120), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"Area: {area}px^2", (20, 150), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

# Initialize the camera
cap = cv2.VideoCapture('/dev/video2')

# Check if the camera opened successfully
if not cap.isOpened():
    print("Error: Could not open video stream.")
    exit()

# Create window and set mouse callback
cv2.namedWindow('Camera Feed with Rectangle Drawing')
cv2.setMouseCallback('Camera Feed with Rectangle Drawing', mouse_callback)

while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
    
    if not ret:
        print("Error: Failed to grab frame")
        break
        
    # Create a copy of the frame to draw on
    frame_with_overlay = frame.copy()
    
    # Always display current coordinates on the frame
    text = f"Current Position: ({mouse_x}, {mouse_y})"
    cv2.putText(frame_with_overlay, text, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                0.7, (255, 0, 0), 2)
    
    # Display number of stored points
    points_text = f"Points: {len(clicked_points)}/4"
    cv2.putText(frame_with_overlay, points_text, (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 
                0.7, (0, 255, 0), 2)
    
    # Draw current mouse position (red dot)
    cv2.circle(frame_with_overlay, (mouse_x, mouse_y), 5, (0, 0, 255), -1)
    
    # Draw all stored points (yellow dots with numbers)
    for i, point in enumerate(clicked_points):
        # Draw point
        cv2.circle(frame_with_overlay, point, 5, (0, 255, 255), -1)
        # Draw point number
        cv2.putText(frame_with_overlay, str(i+1), 
                    (point[0] + 10, point[1] - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
    
    # Draw rectangle if we have 4 points
    draw_rectangle(frame_with_overlay)
    
    # Display the frame
    cv2.imshow('Camera Feed with Rectangle Drawing', frame_with_overlay)
    
    # Break the loop on 'q' press, 'c' to clear points
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('c'):  # Clear all stored points
        clicked_points.clear()
        print("Cleared all stored points")

# Print final stored coordinates
print("\nFinal stored coordinates:")
for i, point in enumerate(clicked_points):
    print(f"Point {i+1}: ({point[0]}, {point[1]})")

# Release everything when done
cap.release()
cv2.destroyAllWindows()
