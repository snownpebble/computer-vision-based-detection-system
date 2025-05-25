import streamlit as st
import os
import sys
import base64
import cv2
import pandas as pd
from datetime import datetime
import json
import numpy as np
from PIL import Image

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_processing import load_detection_results, get_image_preview, filter_results
from utils.visualization import draw_bounding_boxes, create_confidence_histogram
from utils.tutorial import get_tutorial_manager

st.set_page_config(
    page_title="Gallery - Pothole Detection System",
    page_icon="🖼️",
    layout="wide"
)

# Get tutorial manager
tutorial_manager = get_tutorial_manager()

# Render tutorial UI if active
if tutorial_manager.is_active():
    tutorial_manager.render_tutorial_ui("Gallery")

st.title("🖼️ Detection Gallery")
st.markdown("View previously processed images with pothole detections.")

# Load detection results
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_results():
    return load_detection_results()

results = load_results()

if not results:
    st.info("No processed images found. Please upload and process some images first.")
    
    # Tutorial controls for empty gallery
    if tutorial_manager.is_active() and tutorial_manager.get_current_step()['page'] == 'Gallery':
        st.success("✅ This is the Gallery page where you can view your processed images.")
        st.info("Since you don't have any processed images yet, let's continue with the tutorial.")
        
        if st.button("Continue to Next Tutorial Step"):
            tutorial_manager.next_step()
            # If next step is dashboard, navigate there
            next_step = tutorial_manager.get_current_step()
            if next_step and next_step['page'] == 'Dashboard':
                st.switch_page("pages/dashboard.py")
            else:
                st.rerun()
    
    st.stop()

# Filtering options
st.sidebar.header("Filter Options")

# Confidence threshold filter
min_confidence = st.sidebar.slider(
    "Minimum Confidence",
    min_value=0.0,
    max_value=1.0,
    value=0.0,
    step=0.05
)

# Date range filter
all_timestamps = [r.get('timestamp', 0) for r in results if 'timestamp' in r]
if all_timestamps:
    min_date = datetime.fromtimestamp(min(all_timestamps))
    max_date = datetime.fromtimestamp(max(all_timestamps))
    
    # Round dates to days
    min_date = min_date.replace(hour=0, minute=0, second=0, microsecond=0)
    max_date = max_date.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    date_range = st.sidebar.date_input(
        "Date Range",
        value=(min_date.date(), max_date.date()),
        min_value=min_date.date(),
        max_value=max_date.date()
    )
    
    # Convert to datetime objects
    if len(date_range) == 2:
        start_date = datetime.combine(date_range[0], datetime.min.time())
        end_date = datetime.combine(date_range[1], datetime.max.time())
        filter_date_range = (start_date, end_date)
    else:
        filter_date_range = None
else:
    filter_date_range = None

# Minimum detections filter
min_detections = st.sidebar.number_input(
    "Minimum Potholes",
    min_value=0,
    max_value=100,
    value=0,
    step=1
)

# Apply filters
filtered_results = filter_results(
    results,
    min_confidence=min_confidence,
    date_range=filter_date_range,
    min_detections=min_detections
)

if not filtered_results:
    st.warning("No results match the selected filters. Try adjusting your filter criteria.")
    st.stop()

# Sort options
sort_option = st.sidebar.selectbox(
    "Sort By",
    options=["Newest First", "Oldest First", "Most Detections", "Highest Confidence"],
    index=0
)

# Sort the results
if sort_option == "Newest First":
    filtered_results.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
elif sort_option == "Oldest First":
    filtered_results.sort(key=lambda x: x.get('timestamp', 0))
elif sort_option == "Most Detections":
    filtered_results.sort(key=lambda x: len(x.get('detections', [])), reverse=True)
elif sort_option == "Highest Confidence":
    # Sort by average confidence
    def avg_confidence(result):
        detections = result.get('detections', [])
        if not detections:
            return 0
        return sum(d.get('confidence', 0) for d in detections) / len(detections)
    
    filtered_results.sort(key=avg_confidence, reverse=True)

# Display the gallery
st.subheader(f"Gallery ({len(filtered_results)} images)")

# Create tabs for different views
tab1, tab2 = st.tabs(["Grid View", "Detail View"])

with tab1:
    # Grid view with 3 images per row
    cols_per_row = 3
    
    # Calculate how many rows we need
    num_results = len(filtered_results)
    num_rows = (num_results + cols_per_row - 1) // cols_per_row
    
    for row in range(num_rows):
        cols = st.columns(cols_per_row)
        
        # Process each column in the row
        for col_idx in range(cols_per_row):
            result_idx = row * cols_per_row + col_idx
            
            # Check if we still have results to display
            if result_idx < num_results:
                result = filtered_results[result_idx]
                
                with cols[col_idx]:
                    # Get image path
                    image_path = result.get('image_path')
                    
                    if image_path and os.path.exists(image_path):
                        # Get image preview
                        encoded_image = get_image_preview(image_path)
                        
                        if encoded_image:
                            # Display metadata
                            timestamp = result.get('timestamp', 0)
                            date_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
                            
                            # Count detections
                            detections = result.get('detections', [])
                            
                            # Display the image with HTML to allow overlay text
                            html = f"""
                            <div style="position: relative; text-align: center;">
                              <img src="data:image/jpeg;base64,{encoded_image}" style="width: 100%;">
                              <div style="position: absolute; bottom: 10px; right: 10px; background-color: rgba(0,0,0,0.7); color: white; padding: 5px 10px; border-radius: 5px;">
                                {len(detections)} potholes
                              </div>
                            </div>
                            <p style="font-size: 0.8em; margin-top: 5px;">{date_str}</p>
                            """
                            st.markdown(html, unsafe_allow_html=True)
                            
                            # Add a button to view details
                            if st.button(f"View Details", key=f"details_{result_idx}"):
                                st.session_state.selected_result = result
                                st.session_state.detail_view = True
                    else:
                        st.error(f"Image not found: {image_path}")

with tab2:
    # Detail view
    if 'selected_result' not in st.session_state:
        # If no image is selected, use the first one
        if filtered_results:
            st.session_state.selected_result = filtered_results[0]
    
    if 'selected_result' in st.session_state:
        result = st.session_state.selected_result
        
        # Display the image
        image_path = result.get('image_path')
        
        if image_path and os.path.exists(image_path):
            # Read image
            image = cv2.imread(image_path)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Display the image
            st.image(image, caption="Processed Image with Detections", use_column_width=True)
            
            # Get metadata
            timestamp = result.get('timestamp', 0)
            date_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
            filename = result.get('filename', 'Unknown')
            
            # Display metadata
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Detections", len(result.get('detections', [])))
            
            with col2:
                # Calculate average confidence
                detections = result.get('detections', [])
                if detections:
                    avg_conf = sum(d.get('confidence', 0) for d in detections) / len(detections)
                    st.metric("Avg. Confidence", f"{avg_conf:.2f}")
                else:
                    st.metric("Avg. Confidence", "N/A")
            
            with col3:
                st.metric("Date", date_str.split()[0])
            
            # Display detection details
            st.subheader("Detection Details")
            
            detections = result.get('detections', [])
            if detections:
                # Create a dataframe for the detections
                detection_data = []
                for i, det in enumerate(detections):
                    detection_data.append({
                        "ID": i+1,
                        "Confidence": f"{det['confidence']:.2f}",
                        "Position": f"({det['bbox'][0]}, {det['bbox'][1]}, {det['bbox'][2]}, {det['bbox'][3]})"
                    })
                
                df = pd.DataFrame(detection_data)
                st.dataframe(df)
                
                # Display confidence histogram
                st.subheader("Confidence Distribution")
                fig = create_confidence_histogram(detections)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No detections found in this image.")
        else:
            st.error(f"Image not found: {image_path}")
    else:
        st.info("Select an image from the grid view to see details.")

# Sidebar for pagination
if len(filtered_results) > 9:  # If we have more than one page of results
    st.sidebar.markdown("---")
    st.sidebar.subheader("Navigation")
    
    # Calculate total pages
    items_per_page = 9
    total_pages = (len(filtered_results) + items_per_page - 1) // items_per_page
    
    # Add page selector
    page_number = st.sidebar.number_input(
        f"Page (1-{total_pages})",
        min_value=1,
        max_value=total_pages,
        value=1
    )
    
    st.sidebar.write(f"Showing page {page_number} of {total_pages}")
    
    # Add a refresh button
    if st.sidebar.button("Refresh Gallery"):
        st.cache_data.clear()
        st.rerun()
