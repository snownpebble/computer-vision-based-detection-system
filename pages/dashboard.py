import streamlit as st
import sys
import os
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_processing import load_detection_results, calculate_statistics, DATABASE_AVAILABLE
from utils.visualization import create_detection_summary_chart, create_confidence_histogram
from utils.tutorial import get_tutorial_manager

# Try to import database functions if available
if DATABASE_AVAILABLE:
    from utils.database import get_detection_statistics

st.set_page_config(
    page_title="Dashboard - Pothole Detection System",
    page_icon="📊",
    layout="wide"
)

# Get tutorial manager
tutorial_manager = get_tutorial_manager()

# Render tutorial UI if active
if tutorial_manager.is_active():
    tutorial_manager.render_tutorial_ui("Dashboard")

st.title("📊 Analytics Dashboard")
st.markdown("View statistics and insights about detected potholes.")

# Load detection results
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_results_and_stats():
    # Try to use database first if available
    if DATABASE_AVAILABLE:
        try:
            db_stats = get_detection_statistics()
            # If we got valid stats from the database, use those
            if db_stats and db_stats["total_images"] > 0:
                st.sidebar.success("Using database statistics")
                # Still load results from files for backward compatibility
                results = load_detection_results()
                return results, db_stats
        except Exception as e:
            st.sidebar.warning(f"Database error: {e}")
    
    # Fallback to file-based results
    st.sidebar.info("Using file-based statistics")
    results = load_detection_results()
    stats = calculate_statistics(results)
    return results, stats

results, stats = get_results_and_stats()

if not results:
    st.info("No detection data available. Please process some images first.")
    
    # Tutorial controls for empty dashboard
    if tutorial_manager.is_active() and tutorial_manager.get_current_step()['page'] == 'Dashboard':
        st.success("✅ This is the Analytics Dashboard where you can view statistics about detected potholes.")
        st.info("Since you don't have any detection data yet, let's continue with the tutorial.")
        
        if st.button("Continue to Next Tutorial Step"):
            tutorial_manager.next_step()
            # If next step is map, navigate there
            next_step = tutorial_manager.get_current_step()
            if next_step and next_step['page'] == 'Map':
                st.switch_page("pages/map.py")
            else:
                st.rerun()
    
    st.stop()

# Display overview metrics
st.header("Overview")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Images", stats["total_images"])
    
with col2:
    st.metric("Total Potholes", stats["total_detections"])

with col3:
    st.metric("Avg. Potholes per Image", f"{stats['avg_potholes_per_image']:.2f}")

with col4:
    st.metric("Detection Rate", f"{stats['detection_rate']:.1f}%")

# Create time period selector
st.subheader("Time Period")
time_period = st.radio(
    "Select time period:",
    ["All Time", "Last 7 Days", "Last 30 Days", "Custom Range"],
    horizontal=True
)

# Filter results based on time period
filtered_results = results.copy()

if time_period == "Last 7 Days":
    cutoff_date = datetime.now() - timedelta(days=7)
    filtered_results = [r for r in results if datetime.fromtimestamp(r.get('timestamp', 0)) >= cutoff_date]
elif time_period == "Last 30 Days":
    cutoff_date = datetime.now() - timedelta(days=30)
    filtered_results = [r for r in results if datetime.fromtimestamp(r.get('timestamp', 0)) >= cutoff_date]
elif time_period == "Custom Range":
    # Get all timestamps
    all_timestamps = [r.get('timestamp', 0) for r in results if 'timestamp' in r]
    
    if all_timestamps:
        min_date = datetime.fromtimestamp(min(all_timestamps))
        max_date = datetime.fromtimestamp(max(all_timestamps))
        
        # Round dates to days
        min_date = min_date.replace(hour=0, minute=0, second=0, microsecond=0)
        max_date = max_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        date_range = st.date_input(
            "Select date range:",
            value=(min_date.date(), max_date.date()),
            min_value=min_date.date(),
            max_value=max_date.date()
        )
        
        if len(date_range) == 2:
            start_date = datetime.combine(date_range[0], datetime.min.time())
            end_date = datetime.combine(date_range[1], datetime.max.time())
            
            filtered_results = [
                r for r in results 
                if start_date <= datetime.fromtimestamp(r.get('timestamp', 0)) <= end_date
            ]

# Recalculate stats for filtered results
filtered_stats = calculate_statistics(filtered_results)

if not filtered_results:
    st.warning("No data available for the selected time period.")
else:
    # Create detection summary chart
    st.subheader("Detection Trend")
    trend_chart = create_detection_summary_chart(filtered_results)
    st.plotly_chart(trend_chart, use_container_width=True)
    
    # Create detection distribution chart (pie chart of images with 0, 1, 2, 3+ potholes)
    st.subheader("Detection Distribution")
    
    # Group images by number of potholes
    detection_counts = {}
    for r in filtered_results:
        count = len(r.get('detections', []))
        # Group 3 or more together
        if count >= 3:
            category = "3+"
        else:
            category = str(count)
            
        if category not in detection_counts:
            detection_counts[category] = 0
        detection_counts[category] += 1
    
    # Ensure we have all categories
    for category in ['0', '1', '2', '3+']:
        if category not in detection_counts:
            detection_counts[category] = 0
    
    # Create dataframe for plotting
    detection_df = pd.DataFrame({
        'Category': list(detection_counts.keys()),
        'Count': list(detection_counts.values())
    })
    
    # Sort categories
    category_order = ['0', '1', '2', '3+']
    detection_df['Category'] = pd.Categorical(detection_df['Category'], categories=category_order, ordered=True)
    detection_df = detection_df.sort_values('Category')
    
    # Create pie chart
    fig = px.pie(
        detection_df,
        values='Count',
        names='Category',
        title='Distribution of Pothole Counts per Image',
        color_discrete_sequence=px.colors.sequential.Reds
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    
    # Display the chart in a smaller column
    col1, col2 = st.columns([2, 3])
    with col1:
        st.plotly_chart(fig, use_container_width=True)
    
    # In the second column, show confidence distribution
    with col2:
        # Extract all confidences
        all_confidences = []
        for r in filtered_results:
            all_confidences.extend([d.get('confidence', 0) for d in r.get('detections', [])])
        
        if all_confidences:
            # Create confidence histogram
            st.subheader("Confidence Distribution")
            
            # Create fake detections list for the histogram function
            fake_detections = [{'confidence': conf} for conf in all_confidences]
            conf_hist = create_confidence_histogram(fake_detections, bins=15)
            st.plotly_chart(conf_hist, use_container_width=True)
        else:
            st.info("No detections available to show confidence distribution.")
    
    # Create detection hotspots by time of day
    st.subheader("Detection Hotspots")
    
    # Extract hour of day for each detection
    hourly_data = {}
    for r in filtered_results:
        timestamp = r.get('timestamp', 0)
        hour = datetime.fromtimestamp(timestamp).hour
        
        detections = r.get('detections', [])
        if hour not in hourly_data:
            hourly_data[hour] = 0
        
        hourly_data[hour] += len(detections)
    
    # Create dataframe with all hours
    hours = list(range(24))
    counts = [hourly_data.get(hour, 0) for hour in hours]
    
    hourly_df = pd.DataFrame({
        'Hour': hours,
        'Count': counts
    })
    
    # Create bar chart
    fig = px.bar(
        hourly_df,
        x='Hour',
        y='Count',
        title='Potholes Detected by Hour of Day',
        color='Count',
        color_continuous_scale='Reds'
    )
    
    fig.update_layout(
        xaxis=dict(
            tickmode='array',
            tickvals=list(range(0, 24, 2)),
            ticktext=[f"{h:02d}:00" for h in range(0, 24, 2)]
        ),
        xaxis_title="Time of Day",
        yaxis_title="Number of Potholes"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Detection hotspots by image dimensions
    st.subheader("Detection Efficiency")
    
    # Extract image dimensions and detection counts
    dimension_data = []
    for r in filtered_results:
        metadata = r.get('metadata', {})
        if 'image_width' in metadata and 'image_height' in metadata:
            width = metadata['image_width']
            height = metadata['image_height']
            area = width * height / 1000000  # Convert to megapixels
            
            # Get detection count
            count = len(r.get('detections', []))
            
            # Get inference time
            inference_time = metadata.get('inference_time', 0)
            
            dimension_data.append({
                'area': area,
                'count': count,
                'inference_time': inference_time
            })
    
    if dimension_data:
        # Create dataframe
        dim_df = pd.DataFrame(dimension_data)
        
        # Create scatter plot
        fig = px.scatter(
            dim_df,
            x='area',
            y='count',
            size='inference_time',
            color='count',
            title='Potholes vs. Image Size',
            labels={
                'area': 'Image Area (Megapixels)',
                'count': 'Number of Potholes',
                'inference_time': 'Inference Time (s)'
            },
            color_continuous_scale='Reds'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Not enough metadata available to show detection efficiency chart.")

# Add a refresh button
if st.button("Refresh Dashboard"):
    st.cache_data.clear()
    st.rerun()
