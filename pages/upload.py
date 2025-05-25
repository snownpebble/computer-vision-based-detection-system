import streamlit as st
import os
import numpy as np
import time
import io
import cv2
from PIL import Image
from datetime import datetime
import sys
import uuid

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.detection import PotholeDetector
from utils.visualization import draw_bounding_boxes, encode_image_to_base64
from utils.data_processing import save_processed_image
from utils.tutorial import get_tutorial_manager

st.set_page_config(
    page_title="Upload & Detect - Pothole Detection System",
    page_icon="📤",
    layout="wide"
)

# Get tutorial manager
tutorial_manager = get_tutorial_manager()

# Render tutorial UI if active
if tutorial_manager.is_active():
    tutorial_manager.render_tutorial_ui("Upload")

st.title("📤 Upload & Detect")
st.markdown("Upload an image to detect potholes using YOLOv8 model.")

# Initialize the detector
@st.cache_resource
def get_detector():
    return PotholeDetector()

detector = get_detector()

# Layout with two columns
col1, col2 = st.columns([1, 1])

with col1:
    # Check if we have a sample image from the homepage
    sample_image_path = st.session_state.get('selected_sample', None)
    sample_used = False
    
    if sample_image_path and os.path.exists(sample_image_path):
        st.success(f"Using sample image: {os.path.basename(sample_image_path)}")
        st.image(sample_image_path, caption="Selected Sample Image", use_column_width=True)
        sample_used = True
        
        # Add option to clear the sample
        if st.button("Choose a different image"):
            st.session_state.pop('selected_sample', None)
            st.rerun()
    
    # File uploader (show only if not using a sample)
    if not sample_used:
        uploaded_file = st.file_uploader("Choose an image file", type=["jpg", "jpeg", "png"])
    else:
        # Create a file-like object from the sample image
        with open(sample_image_path, "rb") as f:
            image_bytes = f.read()
        uploaded_file = io.BytesIO(image_bytes)
        uploaded_file.name = os.path.basename(sample_image_path)
    
    # Tutorial hint for upload step
    if tutorial_manager.is_active() and tutorial_manager.get_current_step()['page'] == 'Upload':
        st.info("📋 Tutorial Hint: Upload an image or use one of the sample images to detect potholes.")
    
    # Model parameters
    st.subheader("Detection Parameters")
    confidence_threshold = st.slider(
        "Confidence Threshold", 
        min_value=0.1, 
        max_value=1.0, 
        value=0.3, 
        step=0.05,
        help="Minimum confidence score for a detection to be considered valid"
    )

    # Process the image
    if uploaded_file is not None:
        # Create a unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        original_filename = uploaded_file.name
        unique_filename = f"{os.path.splitext(original_filename)[0]}_{timestamp}"
        
        # Status message
        status_message = st.empty()
        status_message.info("Processing image...")
        
        try:
            # Read the image
            image_bytes = uploaded_file.getvalue()
            image = Image.open(io.BytesIO(image_bytes))
            image_np = np.array(image)
            
            # Detect potholes
            image_rgb, detections, metadata = detector.detect_potholes(
                io.BytesIO(image_bytes), 
                conf_threshold=confidence_threshold
            )
            
            # Save results
            with st.spinner("Saving results..."):
                # Save original image
                uploads_dir = "data/uploads"
                os.makedirs(uploads_dir, exist_ok=True)
                original_path = os.path.join(uploads_dir, f"{unique_filename}.jpg")
                
                with open(original_path, "wb") as f:
                    f.write(image_bytes)
                
                # Save detection results
                if image_rgb is not None:
                    # Draw bounding boxes
                    image_with_boxes = draw_bounding_boxes(image_rgb, detections, min_confidence=confidence_threshold)
                    
                    # Save the processed image and results
                    image_path, json_path = detector.save_results(
                        image_with_boxes,
                        detections,
                        metadata,
                        unique_filename,
                        output_dir="data/results"
                    )
                    
                    st.session_state.last_detection = {
                        'image_path': image_path,
                        'json_path': json_path,
                        'detections': detections,
                        'metadata': metadata
                    }
                
            status_message.success(f"Processed image with {len(detections)} pothole detections!")
            
        except Exception as e:
            status_message.error(f"Error processing image: {e}")
            st.stop()

with col2:
    # Display results
    st.subheader("Detection Results")
    
    if uploaded_file is not None and 'last_detection' in st.session_state:
        last_detection = st.session_state.last_detection
        
        # Display the processed image
        image_path = last_detection['image_path']
        if os.path.exists(image_path):
            image = cv2.imread(image_path)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            st.image(image, caption="Processed Image with Detections", use_column_width=True)
        
        # Display detection details
        detections = last_detection['detections']
        if detections:
            st.write(f"**Found {len(detections)} potholes:**")
            
            # Create a table for the detections
            detection_data = []
            for i, det in enumerate(detections):
                detection_data.append({
                    "ID": i+1,
                    "Confidence": f"{det['confidence']:.2f}",
                    "Position": f"({det['bbox'][0]}, {det['bbox'][1]}, {det['bbox'][2]}, {det['bbox'][3]})"
                })
            
            st.table(detection_data)
            
            # Display metadata
            metadata = last_detection['metadata']
            st.write("**Image Information:**")
            st.write(f"- Dimensions: {metadata.get('image_width', 'N/A')} × {metadata.get('image_height', 'N/A')} pixels")
            st.write(f"- Processing Time: {metadata.get('inference_time', 'N/A'):.3f} seconds")
            
            # Export options
            st.subheader("Export Options")
            export_format = st.selectbox(
                "Select export format",
                options=["csv", "json", "txt"],
                index=0
            )
            
            if st.button("Export Results"):
                buffer, mime_type, file_ext = detector.export_results(
                    detections,
                    metadata,
                    format_type=export_format
                )
                
                # Generate download link
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"pothole_detection_{timestamp}.{file_ext}"
                
                st.download_button(
                    label=f"Download {export_format.upper()} File",
                    data=buffer,
                    file_name=filename,
                    mime=mime_type
                )
                
                # Tutorial completion for this step
                if tutorial_manager.is_active() and tutorial_manager.get_current_step()['page'] == 'Upload':
                    st.success("✅ Great job! You've completed the Upload & Detect tutorial step.")
                    # Add a button to continue the tutorial
                    if st.button("Continue to Next Tutorial Step"):
                        tutorial_manager.next_step()
                        # If next step is gallery, navigate there
                        next_step = tutorial_manager.get_current_step()
                        if next_step and next_step['page'] == 'Gallery':
                            st.switch_page("pages/gallery.py")
                        else:
                            st.rerun()
        else:
            st.info("No potholes detected in the image.")
    else:
        st.info("Upload an image to see detection results here.")

# Display some tips
st.markdown("---")
st.subheader("Tips for Better Detection")
st.markdown("""
- Ensure the image is clear and well-lit
- Avoid extreme angles or distorted perspectives
- For best results, potholes should be clearly visible in the frame
- Adjust the confidence threshold to filter out false positives
""")
