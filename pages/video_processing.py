import streamlit as st
import os
import sys
import tempfile
import cv2
import time
import numpy as np
from datetime import datetime
import glob
from pathlib import Path

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.detection import PotholeDetector
from utils.visualization import draw_bounding_boxes
from utils.tutorial import get_tutorial_manager
from utils.data_processing import DATABASE_AVAILABLE

# Try to import database functions if available
if DATABASE_AVAILABLE:
    from utils.database import save_detection_to_db

st.set_page_config(
    page_title="Video Processing - Pothole Detection System",
    page_icon="🎥",
    layout="wide"
)

# Get tutorial manager
tutorial_manager = get_tutorial_manager()

# Render tutorial UI if active
if tutorial_manager.is_active():
    tutorial_manager.render_tutorial_ui("Video")

st.title("🎥 Real-Time Video Processing")
st.markdown("Process video files or webcam feed to detect potholes in real-time.")

# Initialize detector
@st.cache_resource
def get_detector():
    return PotholeDetector()

detector = get_detector()

# Create tabs for different video sources
tab1, tab2, tab3 = st.tabs(["Video Upload", "Webcam", "Results"])

# Directory setup
output_dir = "data/video_results"
os.makedirs(output_dir, exist_ok=True)
frames_dir = os.path.join(output_dir, "frames")
os.makedirs(frames_dir, exist_ok=True)

with tab1:
    st.subheader("Upload Video")
    
    # Option to use demo video
    use_demo = st.checkbox("Use a demo video", value=False)
    
    if use_demo:
        # Check for sample videos in the directory
        sample_dir = "data/sample_videos"
        os.makedirs(sample_dir, exist_ok=True)
        
        # Create demo video from image sequence if needed
        demo_video_path = os.path.join(sample_dir, "pothole_demo.mp4")
        
        if not os.path.exists(demo_video_path):
            st.info("Generating a demo video from sample images...")
            
            # Use sample images to create a video
            sample_images_dir = "data/sample_images"
            sample_images = glob.glob(os.path.join(sample_images_dir, "*.jpg")) + glob.glob(os.path.join(sample_images_dir, "*.png"))
            
            if sample_images:
                # Read first image to get dimensions
                first_img = cv2.imread(sample_images[0])
                height, width = first_img.shape[:2]
                
                # Create a video from the sample images
                fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
                demo_video = cv2.VideoWriter(demo_video_path, fourcc, 2.0, (width, height))
                
                # Add each image multiple times to create a longer video
                for img_path in sample_images:
                    img = cv2.imread(img_path)
                    # Add each frame 10 times (5 seconds per image at 2 FPS)
                    for _ in range(10):
                        demo_video.write(img)
                
                demo_video.release()
                st.success("Demo video created successfully!")
            else:
                st.warning("No sample images found to create a demo video.")
        
        # List available demo videos
        demo_videos = glob.glob(os.path.join(sample_dir, "*.mp4"))
        
        if demo_videos:
            selected_demo = st.selectbox(
                "Select a demo video",
                options=demo_videos,
                format_func=lambda x: os.path.basename(x)
            )
            
            # Display preview of selected demo
            st.video(selected_demo)
            
            # Use the selected demo
            video_path = selected_demo
            
            # Video info
            vid_cap = cv2.VideoCapture(video_path)
            if vid_cap.isOpened():
                frame_width = int(vid_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                frame_height = int(vid_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = int(vid_cap.get(cv2.CAP_PROP_FPS))
                frame_count = int(vid_cap.get(cv2.CAP_PROP_FRAME_COUNT))
                duration = frame_count / fps if fps > 0 else 0
                
                st.write(f"**Video Information:**")
                st.write(f"- Resolution: {frame_width}x{frame_height}")
                st.write(f"- FPS: {fps}")
                st.write(f"- Duration: {duration:.2f} seconds")
                st.write(f"- Total Frames: {frame_count}")
                vid_cap.release()
        else:
            st.warning("No demo videos available. Try uploading sample images first.")
    else:
        # Upload video file
        uploaded_file = st.file_uploader("Upload a video file", type=["mp4", "avi", "mov", "mkv"])
        video_path = None
    
    if 'video_path' in locals() and video_path is not None:
        # Process the selected demo video
        process_video = True
    elif uploaded_file is not None:
        # Save uploaded video to temp file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        temp_file.write(uploaded_file.read())
        video_path = temp_file.name
        
        # Video information
        vid_cap = cv2.VideoCapture(video_path)
        frame_width = int(vid_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(vid_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(vid_cap.get(cv2.CAP_PROP_FPS))
        frame_count = int(vid_cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0
        
        st.write(f"**Video Information:**")
        st.write(f"- Resolution: {frame_width}x{frame_height}")
        st.write(f"- FPS: {fps}")
        st.write(f"- Duration: {duration:.2f} seconds")
        st.write(f"- Total Frames: {frame_count}")
        
        # Video processing settings
        st.subheader("Processing Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            confidence_threshold = st.slider(
                "Confidence Threshold",
                min_value=0.1,
                max_value=0.9,
                value=0.25,
                step=0.05,
                help="Minimum confidence score for detection"
            )
        
        with col2:
            process_every_n_frame = st.slider(
                "Process Every N Frame",
                min_value=1,
                max_value=30,
                value=5,
                step=1,
                help="Process every Nth frame to speed up analysis"
            )
        
        save_frames = st.checkbox(
            "Save Detected Frames",
            value=True,
            help="Save frames with detections to disk"
        )
        
        save_to_database = False
        if DATABASE_AVAILABLE:
            save_to_database = st.checkbox(
                "Save to Database",
                value=True,
                help="Store detection results in the database"
            )
        
        # Process the video
        if st.button("Process Video", type="primary"):
            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Create a container for results
            results_container = st.container()
            
            # Prepare for output
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"pothole_detection_{timestamp}.mp4"
            output_path = os.path.join(output_dir, output_filename)
            
            # Create VideoWriter object
            fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))
            
            # Process the video
            frame_idx = 0
            processed_count = 0
            total_detections = 0
            detection_frames = []
            
            # Read the first frame to verify
            vid_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            success, frame = vid_cap.read()
            
            if not success:
                st.error("Failed to read the video file.")
                os.unlink(video_path)  # Clean up temp file
                st.stop()
            
            # Reset to beginning for processing
            vid_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            start_time = time.time()
            
            # Display a placeholder for the current frame being processed
            current_frame_placeholder = st.empty()
            
            # Store results for later display
            all_results = []
            
            try:
                while True:
                    # Read frame
                    success, frame = vid_cap.read()
                    if not success:
                        break
                    
                    # Update progress
                    progress = frame_idx / frame_count
                    progress_bar.progress(progress)
                    
                    # Process every N frames
                    if frame_idx % process_every_n_frame == 0:
                        # Convert frame for processing
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        
                        # Use detector on the frame
                        status_text.text(f"Processing frame {frame_idx}/{frame_count}...")
                        
                        # Show the current frame being processed (downscaled if needed)
                        if frame_width > 640:
                            display_scale = 640 / frame_width
                            display_frame = cv2.resize(frame_rgb, (0, 0), fx=display_scale, fy=display_scale)
                        else:
                            display_frame = frame_rgb
                        
                        current_frame_placeholder.image(display_frame, caption=f"Processing frame {frame_idx}", use_container_width=True)
                        
                        # Create a temp file for the frame
                        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_frame:
                            cv2.imwrite(temp_frame.name, frame)
                            frame_path = temp_frame.name
                        
                        # Detect potholes in the frame
                        processed_frame, detections, metadata = detector.detect_potholes(
                            frame_path,
                            conf_threshold=confidence_threshold
                        )
                        
                        # Remove the temp frame file
                        os.unlink(frame_path)
                        
                        # Draw bounding boxes on frame
                        if detections:
                            total_detections += len(detections)
                            
                            # Convert processed frame back to BGR for saving
                            processed_frame_bgr = cv2.cvtColor(processed_frame, cv2.COLOR_RGB2BGR)
                            
                            # Save frame with detections if requested
                            if save_frames:
                                frame_filename = f"frame_{frame_idx:06d}.jpg"
                                frame_save_path = os.path.join(frames_dir, frame_filename)
                                cv2.imwrite(frame_save_path, processed_frame_bgr)
                                detection_frames.append(frame_save_path)
                            
                            # Save to database if requested
                            if save_to_database and DATABASE_AVAILABLE:
                                try:
                                    frame_filename = f"video_frame_{timestamp}_{frame_idx:06d}.jpg"
                                    # Save the frame temporarily for database
                                    temp_frame_path = os.path.join(frames_dir, frame_filename)
                                    cv2.imwrite(temp_frame_path, processed_frame_bgr)
                                    
                                    # Add to database
                                    image_id = save_detection_to_db(temp_frame_path, detections, metadata)
                                    
                                    # Keep track of this frame and its detections
                                    all_results.append({
                                        'frame_idx': frame_idx,
                                        'frame_path': temp_frame_path,
                                        'detections': detections,
                                        'timestamp': time.time()
                                    })
                                except Exception as e:
                                    st.warning(f"Database error: {e}")
                            
                            # Write processed frame to output video
                            out.write(processed_frame_bgr)
                        else:
                            # Write original frame to output video
                            out.write(frame)
                        
                        processed_count += 1
                    else:
                        # Write original frame without processing
                        out.write(frame)
                    
                    # Next frame
                    frame_idx += 1
                
                # Complete
                progress_bar.progress(1.0)
                out.release()
                vid_cap.release()
                
                # Calculate processing stats
                elapsed_time = time.time() - start_time
                fps_processing = processed_count / elapsed_time if elapsed_time > 0 else 0
                
                # Store results in session state for the Results tab
                st.session_state.video_results = {
                    'output_path': output_path,
                    'total_frames': frame_count,
                    'processed_frames': processed_count,
                    'total_detections': total_detections,
                    'detection_frames': detection_frames,
                    'elapsed_time': elapsed_time,
                    'fps_processing': fps_processing,
                    'timestamp': timestamp,
                    'all_results': all_results
                }
                
                # Clear the current frame placeholder
                current_frame_placeholder.empty()
                
                # Display summary
                status_text.success("Video processing complete!")
                
                with results_container:
                    st.success(f"Processed {processed_count} frames and found {total_detections} potholes")
                    
                    # Basic stats
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Frames Processed", processed_count)
                    with col2:
                        st.metric("Total Potholes Detected", total_detections)
                    with col3:
                        st.metric("Processing Speed", f"{fps_processing:.2f} FPS")
                    
                    # Show the processed video
                    st.subheader("Processed Video")
                    st.video(output_path)
                    
                    # Option to view in results tab
                    st.info("Switch to the Results tab to see detailed analysis")
            
            except Exception as e:
                st.error(f"Error processing video: {e}")
            
            finally:
                # Clean up
                if 'out' in locals() and out is not None:
                    out.release()
                if 'vid_cap' in locals() and vid_cap is not None:
                    vid_cap.release()
                
                # Delete the temporary file
                try:
                    os.unlink(video_path)
                except Exception:
                    pass

with tab2:
    st.subheader("Webcam Feed")
    
    st.markdown("""
    This feature allows you to use your webcam or camera feed for real-time pothole detection.
    
    **Instructions:**
    1. Click "Start Webcam" to begin capturing from your camera
    2. Adjust the confidence threshold as needed
    3. The system will process frames in real-time and highlight any detected potholes
    4. Click "Stop" when finished
    """)
    
    # Settings for webcam processing
    confidence_threshold = st.slider(
        "Detection Confidence Threshold",
        min_value=0.1,
        max_value=0.9,
        value=0.3,
        step=0.05
    )
    
    # Frame processing rate (to reduce CPU usage)
    process_every_n_frame = st.slider(
        "Process Every N Frame",
        min_value=1,
        max_value=10,
        value=3,
        step=1,
        help="Higher values reduce CPU usage but make detection less responsive"
    )
    
    # Option to save detected frames
    save_detections = st.checkbox("Save Frames with Detections", value=True)
    
    # Start webcam button
    if st.button("Start Webcam"):
        # Placeholders for video display and status
        video_placeholder = st.empty()
        status_text = st.empty()
        
        # Stop button
        stop_button_placeholder = st.empty()
        stop_pressed = stop_button_placeholder.button("Stop Webcam")
        
        # Setup webcam capture
        cap = cv2.VideoCapture(0)  # 0 is usually the default webcam
        
        if not cap.isOpened():
            st.error("Failed to open webcam. Please check your camera connection.")
            st.stop()
        
        # Get webcam properties
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Prepare for saving video
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_output_path = os.path.join(output_dir, f"webcam_{timestamp}.mp4")
        fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
        out = cv2.VideoWriter(video_output_path, fourcc, 20.0, (frame_width, frame_height))
        
        # Variables for statistics
        frame_count = 0
        detection_count = 0
        start_time = time.time()
        
        # Store detections for results
        detection_results = []
        
        try:
            # Process until stop button is pressed
            while not stop_pressed:
                # Read frame from webcam
                ret, frame = cap.read()
                
                if not ret:
                    st.error("Failed to grab frame from webcam")
                    break
                
                # Increment frame counter
                frame_count += 1
                
                # Process every N frames to reduce CPU load
                if frame_count % process_every_n_frame == 0:
                    # Save frame to temp file for processing
                    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
                        cv2.imwrite(temp_file.name, frame)
                        frame_path = temp_file.name
                    
                    try:
                        # Detect potholes
                        processed_frame, detections, metadata = detector.detect_potholes(
                            frame_path,
                            conf_threshold=confidence_threshold
                        )
                        
                        # Update display with processed frame
                        video_placeholder.image(
                            processed_frame,
                            caption="Live Webcam Feed",
                            use_container_width=True
                        )
                        
                        # Save frame if it contains detections and option is enabled
                        if detections and save_detections:
                            detection_count += len(detections)
                            frame_filename = f"webcam_detection_{timestamp}_{frame_count}.jpg"
                            detection_path = os.path.join(frames_dir, frame_filename)
                            
                            # Convert processed frame back to BGR for saving
                            processed_frame_bgr = cv2.cvtColor(processed_frame, cv2.COLOR_RGB2BGR)
                            cv2.imwrite(detection_path, processed_frame_bgr)
                            
                            # Add to results
                            detection_results.append({
                                'frame': frame_count,
                                'path': detection_path,
                                'detections': len(detections),
                                'timestamp': time.time()
                            })
                        
                        # Write frame to video
                        processed_frame_bgr = cv2.cvtColor(processed_frame, cv2.COLOR_RGB2BGR)
                        out.write(processed_frame_bgr)
                        
                        # Update status
                        elapsed = time.time() - start_time
                        status_text.text(
                            f"Running: {elapsed:.1f}s | Frames: {frame_count} | "
                            f"Detections: {detection_count}"
                        )
                    
                    finally:
                        # Remove temp file
                        try:
                            os.unlink(frame_path)
                        except Exception:
                            pass
                
                # Check stop button
                stop_pressed = stop_button_placeholder.button("Stop Webcam", key=f"stop_{frame_count}")
                
                # Add a small delay to prevent overwhelming the CPU
                time.sleep(0.01)
        
        finally:
            # Release resources
            cap.release()
            out.release()
            
            # Calculate statistics
            total_time = time.time() - start_time
            fps = frame_count / total_time if total_time > 0 else 0
            
            # Store results in session state
            st.session_state.webcam_results = {
                'video_path': video_output_path,
                'frame_count': frame_count,
                'detection_count': detection_count,
                'detection_frames': detection_results,
                'processing_time': total_time,
                'fps': fps,
                'timestamp': timestamp
            }
            
            # Show summary
            video_placeholder.empty()
            st.success(f"Webcam session completed: {frame_count} frames processed with {detection_count} pothole detections")
            
            # Display the recorded video
            st.subheader("Recorded Video")
            st.video(video_output_path)
            
            # Option to view in results tab
            st.info("Switch to the Results tab to see detailed analysis")

with tab3:
    st.subheader("Video Analysis Results")
    
    # Check which results to display
    if 'video_results' in st.session_state:
        results = st.session_state.video_results
        source = "Uploaded Video"
    elif 'webcam_results' in st.session_state:
        results = st.session_state.webcam_results
        source = "Webcam Feed"
    else:
        st.info("No video processing results available. Process a video or use webcam first.")
        st.stop()
    
    # Display basic info
    st.write(f"**Source: {source}**")
    st.write(f"Processed on: {results.get('timestamp', 'Unknown')}")
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Frames", results.get('total_frames', results.get('frame_count', 0)))
    
    with col2:
        st.metric("Processed Frames", results.get('processed_frames', results.get('frame_count', 0)))
    
    with col3:
        st.metric("Total Detections", results.get('total_detections', results.get('detection_count', 0)))
    
    with col4:
        st.metric(
            "Processing Speed", 
            f"{results.get('fps_processing', results.get('fps', 0)):.2f} FPS"
        )
    
    # Display the video
    st.subheader("Processed Video")
    video_path = results.get('output_path', results.get('video_path', None))
    if video_path and os.path.exists(video_path):
        st.video(video_path)
    
    # Display frames with detections
    st.subheader("Detection Frames")
    detection_frames = results.get('detection_frames', [])
    
    if isinstance(detection_frames, list) and len(detection_frames) > 0:
        # If it's a simple list of frame paths
        if isinstance(detection_frames[0], str):
            # Show a sample of frames (first 10)
            display_frames = detection_frames[:10]
            
            # Create columns for displaying frames
            cols = st.columns(3)
            for i, frame_path in enumerate(display_frames):
                if os.path.exists(frame_path):
                    with cols[i % 3]:
                        st.image(frame_path, caption=f"Detection {i+1}", use_container_width=True)
            
            if len(detection_frames) > 10:
                st.info(f"Showing 10 of {len(detection_frames)} detection frames")
        
        # If it's a list of dictionaries with detailed detection info
        elif isinstance(detection_frames[0], dict):
            # Convert to DataFrame for easier display
            import pandas as pd
            
            df_data = []
            for i, frame in enumerate(detection_frames[:20]):  # Limit to first 20
                df_data.append({
                    'Frame': frame.get('frame', i),
                    'Detections': frame.get('detections', 0),
                    'Timestamp': frame.get('timestamp', 0)
                })
            
            if df_data:
                df = pd.DataFrame(df_data)
                st.dataframe(df, use_container_width=True)
            
            # Show a sample of frames (first 9)
            display_frames = detection_frames[:9]
            
            # Create columns for displaying frames
            cols = st.columns(3)
            for i, frame_info in enumerate(display_frames):
                frame_path = frame_info.get('path', '')
                if os.path.exists(frame_path):
                    with cols[i % 3]:
                        st.image(frame_path, caption=f"Detection {i+1}", use_container_width=True)
            
            if len(detection_frames) > 9:
                st.info(f"Showing 9 of {len(detection_frames)} detection frames")
    
    # Option to download the video
    if video_path and os.path.exists(video_path):
        with open(video_path, 'rb') as video_file:
            video_bytes = video_file.read()
            st.download_button(
                label="Download Processed Video",
                data=video_bytes,
                file_name=os.path.basename(video_path),
                mime="video/mp4"
            )
    
    # Option to clear results
    if st.button("Clear Results"):
        if 'video_results' in st.session_state:
            del st.session_state.video_results
        if 'webcam_results' in st.session_state:
            del st.session_state.webcam_results
        st.rerun()

# Information about video processing
st.markdown("---")
st.subheader("About Video Processing")
st.markdown("""
This feature allows you to process videos to detect potholes in a sequence of frames. 
The system analyzes either uploaded video files or a live webcam feed to identify and 
highlight potholes in real-time.

**How it works:**
1. Each frame is processed using the same YOLOv8 model used for still images
2. Detections are highlighted with bounding boxes and confidence scores
3. Processed frames are compiled into a new video file
4. Frames with detections can be saved for further analysis

**Tips for better results:**
- Use videos with good lighting and clear visibility
- Adjust the confidence threshold to balance between detection sensitivity and false positives
- For large videos, processing every N frames can significantly speed up analysis
- Webcam analysis works best with a steady camera and good lighting conditions
""")