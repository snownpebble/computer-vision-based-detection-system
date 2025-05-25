import streamlit as st
import os
import sys
import pandas as pd
import cv2
import time
from datetime import datetime
import glob
import shutil

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.detection import PotholeDetector
from utils.data_processing import prepare_batch_results, DATABASE_AVAILABLE
from utils.tutorial import get_tutorial_manager

# Try to import database functions if available
if DATABASE_AVAILABLE:
    from utils.database import save_detection_to_db

st.set_page_config(
    page_title="Batch Processing - Pothole Detection System",
    page_icon="🔄",
    layout="wide"
)

# Get tutorial manager
tutorial_manager = get_tutorial_manager()

# Render tutorial UI if active
if tutorial_manager.is_active():
    tutorial_manager.render_tutorial_ui("Batch")

st.title("🔄 Batch Processing")
st.markdown("Process multiple images at once to detect potholes.")

# Initialize detector
@st.cache_resource
def get_detector():
    return PotholeDetector()

detector = get_detector()

# Create tabs for different batch operations
tab1, tab2 = st.tabs(["Folder Processing", "Results"])

with tab1:
    st.subheader("Process Images from Folder")
    
    # Folder selection
    st.markdown("#### Select Source Folder")
    
    # For demonstration, we'll use predefined folders
    source_folder = st.selectbox(
        "Select a source folder:",
        ["data/samples", "data/uploads", "data/custom"]
    )
    
    # Create folder if it doesn't exist
    os.makedirs(source_folder, exist_ok=True)
    
    # List files in the folder
    image_files = glob.glob(os.path.join(source_folder, "*.jpg")) + \
                 glob.glob(os.path.join(source_folder, "*.jpeg")) + \
                 glob.glob(os.path.join(source_folder, "*.png"))
    
    # Show file count
    st.info(f"Found {len(image_files)} image files in {source_folder}")
    
    # Show file list in an expander
    with st.expander("View Files"):
        for file in image_files:
            st.text(os.path.basename(file))
    
    # Create output folder
    output_folder = "data/results"
    os.makedirs(output_folder, exist_ok=True)
    
    # Process settings
    st.markdown("#### Processing Settings")
    
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
        save_visualizations = st.checkbox(
            "Save Visualizations",
            value=True,
            help="Save images with bounding boxes"
        )
    
    # Add database option if available
    save_to_database = False
    if DATABASE_AVAILABLE:
        save_to_database = st.checkbox(
            "Save to Database",
            value=True,
            help="Store detection results in the database"
        )
    
    # Process button
    if st.button("Process Images", type="primary", disabled=len(image_files) == 0):
        # Progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Results container
        results_container = st.container()
        
        # Process each file
        batch_results = []
        
        for i, file_path in enumerate(image_files):
            # Update progress
            progress = (i + 1) / len(image_files)
            progress_bar.progress(progress)
            status_text.text(f"Processing {i+1}/{len(image_files)}: {os.path.basename(file_path)}")
            
            try:
                # Process the image
                processed_image, detections, metadata = detector.detect_potholes(
                    file_path, 
                    conf_threshold=confidence_threshold
                )
                
                # Save visualization if requested
                if save_visualizations:
                    detector.save_results(
                        processed_image,
                        detections,
                        metadata,
                        os.path.basename(file_path),
                        output_dir=output_folder
                    )
                
                # Save to database if requested
                if save_to_database and DATABASE_AVAILABLE:
                    try:
                        image_id = save_detection_to_db(file_path, detections, metadata)
                        status_text.text(f"Saved to database (ID: {image_id}): {os.path.basename(file_path)}")
                    except Exception as e:
                        st.warning(f"Database error: {e}")
                
                # Add to batch results
                batch_results.append((file_path, detections, metadata))
                
                # Short delay to allow UI to update
                time.sleep(0.1)
                
            except Exception as e:
                st.error(f"Error processing {os.path.basename(file_path)}: {e}")
        
        # Complete
        progress_bar.progress(1.0)
        status_text.text("Processing complete!")
        
        # Store results in session state
        if batch_results:
            st.session_state.batch_results = batch_results
            st.session_state.last_batch_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Summary
            with results_container:
                st.success(f"Processed {len(batch_results)} images successfully")
                
                # Show basic stats
                total_detections = sum(len(d) for _, d, _ in batch_results)
                avg_detections = total_detections / len(batch_results) if batch_results else 0
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Images", len(batch_results))
                with col2:
                    st.metric("Total Detections", total_detections)
                with col3:
                    st.metric("Avg. Detections per Image", f"{avg_detections:.2f}")
                
                # Option to view detailed results
                st.info("Switch to the Results tab to view detailed results")
            
            # Tutorial completion for this step
            if tutorial_manager.is_active() and tutorial_manager.get_current_step()['page'] == 'Batch':
                st.success("✅ Congratulations! You've completed the tutorial for batch processing.")
                # Add a button to complete the tutorial
                if st.button("Complete Tutorial"):
                    tutorial_manager.complete_tutorial()
                    st.rerun()
        else:
            st.warning("No results were generated. Please check the input files and try again.")
    
    # Upload new images
    st.markdown("---")
    st.subheader("Upload New Images for Batch Processing")
    
    uploaded_files = st.file_uploader(
        "Upload images",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        # Create upload folder if it doesn't exist
        upload_folder = "data/uploads"
        os.makedirs(upload_folder, exist_ok=True)
        
        # Save each uploaded file
        for uploaded_file in uploaded_files:
            file_path = os.path.join(upload_folder, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
        
        st.success(f"Uploaded {len(uploaded_files)} files to {upload_folder}")
        st.info("Please select the 'data/uploads' folder from the dropdown above to process these files")
        
        # Select the uploads folder automatically
        st.session_state.selected_folder = "data/uploads"
        st.rerun()

with tab2:
    st.subheader("Batch Processing Results")
    
    # Check if we have results
    if 'batch_results' in st.session_state and st.session_state.batch_results:
        # Get results from session state
        batch_results = st.session_state.batch_results
        last_batch_time = st.session_state.get('last_batch_time', 'Unknown')
        
        st.info(f"Showing results from last batch ({last_batch_time})")
        
        # Prepare results for display
        results_df = prepare_batch_results(batch_results)
        
        # Display as table
        st.dataframe(results_df, use_container_width=True)
        
        # Display summary visualizations
        st.subheader("Summary")
        
        # Bar chart of detections per image
        if len(results_df) > 0:
            import plotly.express as px
            
            # Create bar chart
            fig = px.bar(
                results_df,
                x='filename',
                y='detections',
                title='Detections Per Image',
                labels={'detections': 'Number of Potholes', 'filename': 'Image File'},
                color='confidence',
                color_continuous_scale='Viridis'
            )
            
            fig.update_layout(
                xaxis_title="Image",
                yaxis_title="Number of Potholes",
                xaxis_tickangle=-45,
                height=400,
                margin=dict(l=40, r=40, t=40, b=80)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Export options
            st.subheader("Export Results")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("Export as CSV"):
                    # Export to CSV
                    csv_data = results_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "Download CSV",
                        csv_data,
                        "pothole_detection_results.csv",
                        "text/csv",
                        key='download-csv'
                    )
            
            with col2:
                if st.button("Export as Excel"):
                    # Export to Excel
                    excel_file = "data/export/pothole_detection_results.xlsx"
                    os.makedirs(os.path.dirname(excel_file), exist_ok=True)
                    results_df.to_excel(excel_file, index=False)
                    
                    # Read the file for download
                    with open(excel_file, "rb") as file:
                        st.download_button(
                            "Download Excel",
                            file,
                            "pothole_detection_results.xlsx",
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key='download-excel'
                        )
            
            with col3:
                if st.button("Export as JSON"):
                    # Export to JSON
                    import json
                    json_data = results_df.to_json(orient="records")
                    st.download_button(
                        "Download JSON",
                        json_data,
                        "pothole_detection_results.json",
                        "application/json",
                        key='download-json'
                    )
            
            # Clear results button
            if st.button("Clear Results"):
                if 'batch_results' in st.session_state:
                    del st.session_state.batch_results
                if 'last_batch_time' in st.session_state:
                    del st.session_state.last_batch_time
                st.rerun()
    else:
        st.info("No batch results available. Process some images in the Folder Processing tab first.")
        
        # Tutorial hint for empty results
        if tutorial_manager.is_active() and tutorial_manager.get_current_step()['page'] == 'Batch':
            st.success("✅ This is the Batch Processing page where you can process multiple images at once.")
            st.info("Process some images in the Folder Processing tab to complete the tutorial.")

# Tutorial completion message if completed
if tutorial_manager.is_completed():
    st.sidebar.success("✅ Tutorial completed! You're now ready to use the Pothole Detection System.")
    
    # Reset tutorial button
    if st.sidebar.button("Restart Tutorial"):
        tutorial_manager.restart_tutorial()
        st.rerun()