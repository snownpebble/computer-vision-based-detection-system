import streamlit as st
import sys
import os
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_processing import load_detection_results, DATABASE_AVAILABLE
from utils.visualization import create_pothole_map
from utils.tutorial import get_tutorial_manager

# Try to import database functions if available
if DATABASE_AVAILABLE:
    from utils.database import get_map_data

st.set_page_config(
    page_title="Map View - Pothole Detection System",
    page_icon="🗺️",
    layout="wide"
)

# Get tutorial manager
tutorial_manager = get_tutorial_manager()

# Render tutorial UI if active
if tutorial_manager.is_active():
    tutorial_manager.render_tutorial_ui("Map")

st.title("🗺️ Pothole Map Visualization")
st.markdown("View geographical distribution of detected potholes.")

# Load detection results
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_results():
    # Try to use database first if available
    if DATABASE_AVAILABLE:
        try:
            db_map_data = get_map_data()
            if db_map_data:
                st.sidebar.success("Using database map data")
                return db_map_data
        except Exception as e:
            st.sidebar.warning(f"Database error: {e}")
    
    # Fallback to file-based results
    st.sidebar.info("Using file-based map data")
    return load_detection_results()

results = get_results()

if not results:
    st.info("No detection data available. Please process some images first.")
    
    # Tutorial controls for empty map
    if tutorial_manager.is_active() and tutorial_manager.get_current_step()['page'] == 'Map':
        st.success("✅ This is the Map page where you can visualize pothole locations geographically.")
        st.info("Since you don't have any geotagged detection data yet, let's continue with the tutorial.")
        
        if st.button("Continue to Next Tutorial Step"):
            tutorial_manager.next_step()
            # If next step is Database, navigate there
            next_step = tutorial_manager.get_current_step()
            if next_step and next_step['page'] == 'Database':
                st.switch_page("pages/database.py")
            else:
                st.rerun()
    
    st.stop()

# Check if any results have geolocation data
has_geo_data = any('metadata' in r and 'latitude' in r.get('metadata', {}) and 'longitude' in r.get('metadata', {}) for r in results)

if not has_geo_data:
    st.warning("No geotagged images found in your data. For demonstration purposes, we'll show a simulated map.")
    st.markdown("""
    To use the map feature, your images need to contain geolocation metadata. Most smartphone photos include this automatically.
    
    For this demonstration, we'll generate random locations around a central point.
    """)
    
    # Allow user to select a central location
    st.subheader("Select a Central Location")
    
    # Default to New York City
    default_lat = 40.7128
    default_lon = -74.0060
    default_zoom = 10
    
    # Let user select a preset location
    location_preset = st.selectbox(
        "Select a preset location:",
        ["New York City, USA", "London, UK", "Tokyo, Japan", "Sydney, Australia", "Custom Location"]
    )
    
    if location_preset == "New York City, USA":
        center_lat, center_lon = 40.7128, -74.0060
    elif location_preset == "London, UK":
        center_lat, center_lon = 51.5074, -0.1278
    elif location_preset == "Tokyo, Japan":
        center_lat, center_lon = 35.6762, 139.6503
    elif location_preset == "Sydney, Australia":
        center_lat, center_lon = -33.8688, 151.2093
    else:  # Custom Location
        col1, col2 = st.columns(2)
        with col1:
            center_lat = st.number_input("Latitude", value=default_lat, format="%.4f")
        with col2:
            center_lon = st.number_input("Longitude", value=default_lon, format="%.4f")
    
    # Generate simulated geolocation data
    for r in results:
        # Add random offset (up to 0.05 degrees ~ 5km)
        lat_offset = (random.random() - 0.5) * 0.05
        lon_offset = (random.random() - 0.5) * 0.05
        
        # Store in metadata
        if 'metadata' not in r:
            r['metadata'] = {}
        
        r['metadata']['latitude'] = center_lat + lat_offset
        r['metadata']['longitude'] = center_lon + lon_offset
    
    st.info("Simulated geolocation data has been generated for demonstration.")

# Create the map
st.subheader("Pothole Detection Map")

# Create the map visualization
pothole_map = create_pothole_map(results)
st.plotly_chart(pothole_map, use_container_width=True)

# Map filters
st.sidebar.header("Map Filters")

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
    
    if len(date_range) == 2:
        start_date = datetime.combine(date_range[0], datetime.min.time())
        end_date = datetime.combine(date_range[1], datetime.max.time())
        
        # Filter results by date
        filtered_results = [
            r for r in results 
            if start_date <= datetime.fromtimestamp(r.get('timestamp', 0)) <= end_date
        ]
        
        if filtered_results:
            st.sidebar.info(f"Showing {len(filtered_results)} of {len(results)} images")
            
            # Update the map
            filtered_map = create_pothole_map(filtered_results)
            st.plotly_chart(filtered_map, use_container_width=True)

# Show statistics about the geographical distribution
st.subheader("Geographical Insights")

# Extract coordinates and counts
geo_data = []
for r in results:
    metadata = r.get('metadata', {})
    if 'latitude' in metadata and 'longitude' in metadata:
        lat = metadata['latitude']
        lon = metadata['longitude']
        count = len(r.get('detections', []))
        
        if count > 0:
            geo_data.append({
                'latitude': lat,
                'longitude': lon,
                'detections': count
            })

if geo_data:
    # Create dataframe
    geo_df = pd.DataFrame(geo_data)
    
    # Calculate statistics
    total_locations = len(geo_df)
    total_potholes = geo_df['detections'].sum()
    avg_per_location = total_potholes / total_locations if total_locations > 0 else 0
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Locations", total_locations)
    with col2:
        st.metric("Total Potholes", int(total_potholes))
    with col3:
        st.metric("Avg. Potholes per Location", f"{avg_per_location:.2f}")
    
    # Group by location and count potholes
    # For demonstration, we'll create artificial clusters
    # In a real app, you would use a clustering algorithm like DBSCAN
    
    # Create artificial clusters based on latitude/longitude grid
    geo_df['lat_cluster'] = (geo_df['latitude'] * 10).astype(int) / 10
    geo_df['lon_cluster'] = (geo_df['longitude'] * 10).astype(int) / 10
    
    # Group by cluster
    clusters = geo_df.groupby(['lat_cluster', 'lon_cluster']).agg({
        'detections': 'sum',
        'latitude': 'mean',
        'longitude': 'mean'
    }).reset_index()
    
    # Display hotspots table
    st.subheader("Pothole Hotspots")
    
    # Sort by number of detections
    clusters = clusters.sort_values('detections', ascending=False)
    
    # Add rank column
    clusters['rank'] = range(1, len(clusters) + 1)
    
    # Keep only top 10
    top_clusters = clusters.head(10)
    
    # Format table for display
    display_df = pd.DataFrame({
        'Rank': top_clusters['rank'],
        'Latitude': top_clusters['latitude'].round(4),
        'Longitude': top_clusters['longitude'].round(4),
        'Potholes Detected': top_clusters['detections']
    })
    
    st.table(display_df)
else:
    st.info("Not enough data to show geographical insights.")

# Add a refresh button
if st.sidebar.button("Refresh Map"):
    st.cache_data.clear()
    st.rerun()
