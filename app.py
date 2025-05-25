import streamlit as st
import os
import shutil
from pathlib import Path

# Import tutorial manager
from utils.tutorial import get_tutorial_manager

# Create necessary directories if they don't exist
Path("data/uploads").mkdir(parents=True, exist_ok=True)
Path("data/processed").mkdir(parents=True, exist_ok=True)
Path("data/results").mkdir(parents=True, exist_ok=True)
Path("data/sample_images").mkdir(parents=True, exist_ok=True)

# Copy sample images from attached assets if sample folder is empty
sample_images_dir = Path("data/sample_images")
if not list(sample_images_dir.glob("*.jpg")) and not list(sample_images_dir.glob("*.png")):
    # Check for assets in the attached_assets folder
    assets_dir = Path("attached_assets")
    if assets_dir.exists():
        image_files = list(assets_dir.glob("*.jpg")) + list(assets_dir.glob("*.png")) + list(assets_dir.glob("*.avif"))
        for img_file in image_files:
            # Copy to sample images directory
            if img_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.avif']:
                target_path = sample_images_dir / f"sample_{img_file.name}"
                shutil.copy(img_file, target_path)

# Set page config
st.set_page_config(
    page_title="Pothole Detection System",
    page_icon="🛣️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Get tutorial manager
tutorial_manager = get_tutorial_manager()

# Add tutorial controls to sidebar with enhanced UI
with st.sidebar:
    st.markdown("## 🎓 Interactive Tutorial")
    
    if not tutorial_manager.is_active() and not tutorial_manager.is_completed():
        # First time user - show attractive start option
        st.markdown("""
        <div style="padding: 10px; border-radius: 5px; border-left: 5px solid #4CAF50; background-color: #e8f5e9;">
            <p style="margin: 0; font-size: 15px;">New to the app? Take an interactive tour to learn all the features!</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚀 Start Interactive Tour", key="start_tutorial_btn"):
            tutorial_manager.start_tutorial()
            st.rerun()
            
    elif tutorial_manager.is_active():
        # Active tutorial - show progress and controls
        current_step = tutorial_manager.get_current_step()
        steps_total = len(tutorial_manager.steps) - 1  # Excluding final "completed" step
        current_index = st.session_state.tutorial_state['current_step']
        
        # Calculate progress percentage
        progress_pct = (current_index / steps_total) * 100 if steps_total > 0 else 0
        
        # Show progress bar
        st.progress(min(progress_pct/100, 1.0))
        st.success(f"Tutorial in progress: Step {current_index + 1} of {steps_total + 1}")
        
        # Show current location in tutorial
        if current_step and 'title' in current_step:
            st.info(f"Current: {current_step['title']}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⏸️ Pause Tour", key="pause_tutorial"):
                tutorial_manager.skip_tutorial()
                st.rerun()
        with col2:
            if current_index < steps_total:
                # Handle navigation to next step
                next_page = tutorial_manager.steps[current_index + 1]['page']
                btn_text = f"⏭️ Next Step ({next_page})" if next_page != "Home" else "⏭️ Next Step"
                if st.button(btn_text, key="next_tutorial_step"):
                    tutorial_manager.next_step()
                    # Navigate to the appropriate page if needed
                    current_page = "Home"  # Current page is Home since we're in app.py
                    if next_page != "Home" and next_page.lower() != current_page.lower():
                        # Navigate to the next step's page
                        page_map = {
                            'Upload': 'pages/upload.py',
                            'Gallery': 'pages/gallery.py',
                            'Dashboard': 'pages/dashboard.py',
                            'Map': 'pages/map.py',
                            'Database': 'pages/database.py',
                            'Batch': 'pages/batch_processing.py',
                            'Video': 'pages/video_processing.py',
                            'Alerts': 'pages/alerts.py',
                            'Repairs': 'pages/repair_requests.py',
                            'Manual': 'pages/manual.py',
                            'Code Viewer': 'pages/code_viewer.py'
                        }
                        if next_page in page_map:
                            st.switch_page(page_map[next_page])
                    st.rerun()
    else:
        # Tutorial was completed or skipped - offer to restart
        st.markdown("""
        <div style="padding: 10px; border-radius: 5px; border-left: 5px solid #2196F3; background-color: #e3f2fd;">
            <p style="margin: 0; font-size: 15px;">Want to rediscover app features? Restart the interactive tour!</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔄 Restart Interactive Tour", key="restart_tutorial_btn"):
            tutorial_manager.restart_tutorial()
            st.rerun()
            
    # Add a Help & Resources section below the tutorial controls
    st.markdown("---")
    st.markdown("### 📚 Help & Resources")
    
    # Links to important pages
    if st.button("📖 User Manual", key="user_manual_btn"):
        # Navigate to manual page
        st.switch_page("pages/manual.py")
        
    if st.button("❓ View App Code", key="view_code_btn"):
        # Navigate to code viewer
        st.switch_page("pages/code_viewer.py")

# Render tutorial UI if active
if tutorial_manager.is_active():
    tutorial_manager.render_tutorial_ui("Home")

# App title and description
st.title("🛣️ Pothole Detection System")
st.markdown("""
This application showcases a YOLOv8-based pothole detection system with visualization 
and analytics capabilities. Upload images to detect potholes, view previously processed images, 
and analyze detection statistics.
""")

# Display main menu options with icons
st.subheader("Main Features")
col1, col2, col3 = st.columns(3)

with col1:
    st.info("📤 **Upload & Detect**")
    st.markdown("Upload images and detect potholes using YOLOv8 model")
    
with col2:
    st.info("🖼️ **Gallery & Results**")
    st.markdown("View your processed images with detection results")
    
with col3:
    st.info("📊 **Analytics Dashboard**")
    st.markdown("View statistics and insights about detected potholes")

# Model information
st.subheader("Model Information")
st.markdown("""
The system uses YOLOv8, a powerful object detection model from Ultralytics,
specifically trained to detect potholes in road images. This model offers a good balance between
accuracy and computational efficiency.
""")

# Quick start guide
st.subheader("Quick Start Guide")
st.markdown("""
1. Navigate to **Upload** in the sidebar to upload and process images
2. View processed images in the **Gallery**
3. Analyze pothole statistics in the **Dashboard**
4. Visualize geotagged potholes in the **Map**
5. Process multiple images at once using **Batch Processing**
6. Manage detection records in the **Database**
""")

# Sample images section
if os.path.exists("data/sample_images"):
    sample_images = [f for f in os.listdir("data/sample_images") if f.endswith(('.jpg', '.jpeg', '.png'))]
    if sample_images:
        st.subheader("Sample Images")
        st.markdown("Try the application with these sample pothole images:")
        
        # Display up to 3 sample images in a row
        cols = st.columns(min(3, len(sample_images)))
        for i, sample in enumerate(sample_images[:3]):
            with cols[i % 3]:
                img_path = os.path.join("data/sample_images", sample)
                st.image(img_path, caption=f"Sample {i+1}", use_column_width=True)
                if st.button(f"Use Sample {i+1}", key=f"sample_{i}"):
                    # Save the path for use in upload page
                    st.session_state.selected_sample = img_path
                    # Redirect to upload page
                    st.switch_page("pages/upload.py")

# Footer
st.markdown("---")
st.markdown("© 2025 Pothole Detection System | Powered by YOLOv8 Ultralytics and Streamlit")
