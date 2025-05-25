import streamlit as st
import os
import sys
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import random
import base64
import time
from pathlib import Path
import uuid

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_processing import load_detection_results, DATABASE_AVAILABLE
from utils.tutorial import get_tutorial_manager
from utils.twilio_integration import send_alert, check_twilio_credentials

# Try to import database functions if available
if DATABASE_AVAILABLE:
    from utils.database import get_map_data, get_all_detections, get_detection_statistics

st.set_page_config(
    page_title="Road Repair Requests - Pothole Detection System",
    page_icon="🛠️",
    layout="wide"
)

# Get tutorial manager
tutorial_manager = get_tutorial_manager()

# Render tutorial UI if active
if tutorial_manager.is_active():
    tutorial_manager.render_tutorial_ui("Repairs")

st.title("🛠️ Road Repair Requests")
st.markdown("Submit and track repair requests for detected potholes with one click")

# Function to load mascot animation
def load_mascot_animation():
    # Create simple CSS animation for the mascot
    return """
    <style>
    @keyframes bounce {
        0%, 20%, 50%, 80%, 100% {transform: translateY(0);}
        40% {transform: translateY(-30px);}
        60% {transform: translateY(-15px);}
    }
    
    @keyframes float {
        0% {transform: translateY(0px) rotate(0deg);}
        50% {transform: translateY(-10px) rotate(5deg);}
        100% {transform: translateY(0px) rotate(0deg);}
    }
    
    .mascot-container {
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 1000;
        animation: float 3s ease-in-out infinite;
        text-align: center;
    }
    
    .mascot-bounce {
        animation: bounce 2s ease infinite;
    }
    
    .mascot-image {
        width: 100px;
        height: 100px;
        cursor: pointer;
    }
    
    .mascot-speech {
        background-color: white;
        border: 2px solid #4b79ff;
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 10px;
        max-width: 200px;
        position: relative;
    }
    
    .mascot-speech:after {
        content: '';
        position: absolute;
        bottom: -10px;
        right: 20px;
        border-width: 10px 10px 0;
        border-style: solid;
        border-color: #4b79ff transparent;
    }
    
    .repair-btn {
        background-color: #FF4B4B;
        color: white;
        font-weight: bold;
        border: none;
        border-radius: 4px;
        padding: 10px 15px;
        cursor: pointer;
        transition: background-color 0.3s;
    }
    
    .repair-btn:hover {
        background-color: #FF2E2E;
    }
    
    .success-message {
        background-color: #4CAF50;
        color: white;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
        animation: fadeIn 0.5s;
    }
    
    @keyframes fadeIn {
        from {opacity: 0;}
        to {opacity: 1;}
    }
    
    .status-badge {
        display: inline-block;
        padding: 5px 10px;
        border-radius: 20px;
        font-size: 0.8em;
        font-weight: bold;
        text-align: center;
        min-width: 100px;
    }
    
    .status-new {
        background-color: #4b79ff;
        color: white;
    }
    
    .status-processing {
        background-color: #FFA500;
        color: white;
    }
    
    .status-scheduled {
        background-color: #9932CC;
        color: white;
    }
    
    .status-completed {
        background-color: #4CAF50;
        color: white;
    }
    
    .status-rejected {
        background-color: #FF4B4B;
        color: white;
    }
    
    .repair-card {
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 15px;
        margin-bottom: 15px;
        transition: box-shadow 0.3s;
    }
    
    .repair-card:hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    </style>
    """

# Create session state for repair requests if it doesn't exist
if 'repair_requests' not in st.session_state:
    st.session_state.repair_requests = []

# Load saved repair requests if available
repair_requests_file = "data/repair_requests.json"
if os.path.exists(repair_requests_file):
    try:
        with open(repair_requests_file, 'r') as f:
            st.session_state.repair_requests = json.load(f)
    except Exception as e:
        st.error(f"Error loading repair requests: {e}")

# Create tabs for different sections
tab1, tab2, tab3 = st.tabs(["Create Request", "Track Requests", "Analytics"])

with tab1:
    st.subheader("Submit Repair Request")
    
    # Explanation of the one-click repair system
    st.markdown("""
    Quickly submit repair requests for pothole locations detected by the system.
    Simply select a pothole location and submit a repair request with one click.
    """)
    
    # Get critical areas data
    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def get_pothole_locations():
        if DATABASE_AVAILABLE:
            try:
                # Try to get data from database
                geo_data = get_map_data()
                if geo_data:
                    return geo_data
            except Exception:
                pass
        
        # Fallback to file-based results
        results = load_detection_results()
        
        # Extract locations
        locations = []
        
        for result in results:
            detections = result.get('detections', [])
            if detections:
                metadata = result.get('metadata', {})
                
                # Generate random coordinates if none exist (for demonstration)
                if 'latitude' not in metadata or 'longitude' not in metadata:
                    metadata['latitude'] = random.uniform(40.7, 40.8)  # NYC area
                    metadata['longitude'] = random.uniform(-74.0, -73.9)
                
                locations.append({
                    'id': str(uuid.uuid4())[:8],
                    'image': result.get('image_path', 'unknown'),
                    'latitude': metadata.get('latitude'),
                    'longitude': metadata.get('longitude'),
                    'count': len(detections),
                    'severity': min(10, len(detections) * 2),  # Scale from 1-10
                    'timestamp': result.get('timestamp', datetime.now().timestamp()),
                    'confidence': sum(d.get('confidence', 0) for d in detections) / len(detections) if detections else 0
                })
        
        # If no real data, create some demo data
        if not locations:
            # Create 10 random locations
            for i in range(10):
                locations.append({
                    'id': f"DEMO{i+1:03d}",
                    'image': f"demo_image_{i+1}.jpg",
                    'latitude': 40.7 + random.uniform(-0.1, 0.1),
                    'longitude': -74.0 + random.uniform(-0.1, 0.1),
                    'count': random.randint(1, 5),
                    'severity': random.randint(3, 10),
                    'timestamp': (datetime.now() - timedelta(days=random.randint(0, 30))).timestamp(),
                    'confidence': random.uniform(0.5, 0.95)
                })
        
        return locations
    
    pothole_locations = get_pothole_locations()
    
    if not pothole_locations:
        st.info("No pothole locations found. Process some images or check the database connection.")
        st.stop()
    
    # Display map of pothole locations
    st.subheader("Pothole Locations Map")
    
    # Convert to DataFrame for plotting
    df = pd.DataFrame(pothole_locations)
    
    # Add a column for hover text
    df['hover_text'] = df.apply(lambda row: f"ID: {row['id']}<br>Severity: {row['severity']:.1f}/10<br>Potholes: {row['count']}", axis=1)
    
    # Create map
    fig = px.scatter_mapbox(
        df,
        lat="latitude",
        lon="longitude",
        size="count",
        color="severity",
        color_continuous_scale=px.colors.sequential.Reds,
        size_max=15,
        zoom=10,
        hover_name="id",
        hover_data={
            "hover_text": True,
            "count": False,
            "severity": False,
            "latitude": False,
            "longitude": False,
            "id": False
        },
        title="Pothole Locations"
    )
    
    fig.update_layout(
        mapbox_style="open-street-map",
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Form for selecting a pothole location and submitting a repair request
    st.subheader("Submit a Repair Request")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Select pothole location
        location_options = [f"ID: {loc['id']} - Severity: {loc['severity']:.1f}/10 - Location: ({loc['latitude']:.4f}, {loc['longitude']:.4f})" for loc in pothole_locations]
        selected_location = st.selectbox("Select Pothole Location", options=location_options)
        
        # Get the selected location index
        location_idx = location_options.index(selected_location)
        selected_pothole = pothole_locations[location_idx]
        
        # Display selected pothole details
        st.markdown(f"""
        **Selected Pothole Details:**
        - ID: {selected_pothole['id']}
        - Location: ({selected_pothole['latitude']:.4f}, {selected_pothole['longitude']:.4f})
        - Severity: {selected_pothole['severity']:.1f}/10
        - Number of Potholes: {selected_pothole['count']}
        - Detection Date: {datetime.fromtimestamp(selected_pothole['timestamp']).strftime('%Y-%m-%d')}
        """)
    
    with col2:
        # Additional request details
        priority_options = ["High", "Medium", "Low"]
        priority = st.selectbox("Priority", options=priority_options, index=0 if selected_pothole['severity'] >= 7 else 1 if selected_pothole['severity'] >= 4 else 2)
        
        repair_types = ["Patching", "Full Resurfacing", "Crack Sealing", "Pothole Filling"]
        repair_type = st.selectbox("Repair Type", options=repair_types, index=0 if selected_pothole['severity'] >= 7 else 3)
        
        additional_notes = st.text_area("Additional Notes", placeholder="Enter any additional information about this repair request...")
    
    # Check if this pothole location already has a repair request
    existing_request = next((req for req in st.session_state.repair_requests 
                           if req.get('pothole_id') == selected_pothole['id']), None)
    
    if existing_request:
        st.warning(f"This pothole location already has a repair request (ID: {existing_request['request_id']}) with status: {existing_request['status']}")
        
        # Option to update the existing request
        if st.button("Update Existing Request"):
            # Update the existing request
            existing_request.update({
                'priority': priority,
                'repair_type': repair_type,
                'notes': additional_notes,
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
            
            # Save to file
            with open(repair_requests_file, 'w') as f:
                json.dump(st.session_state.repair_requests, f)
            
            st.success("Repair request updated successfully!")
            
            # Show the mascot
            st.markdown(load_mascot_animation(), unsafe_allow_html=True)
            st.markdown(f"""
            <div class="mascot-container">
                <div class="mascot-speech">Request updated! I'll make sure this pothole gets fixed ASAP!</div>
                <div class="mascot-bounce">🕵️</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        # One-Click Repair Request button
        st.markdown(load_mascot_animation(), unsafe_allow_html=True)
        if st.button("🛠️ Submit Repair Request", type="primary"):
            # Create a new repair request
            request_id = f"REQ-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
            
            new_request = {
                'request_id': request_id,
                'pothole_id': selected_pothole['id'],
                'latitude': selected_pothole['latitude'],
                'longitude': selected_pothole['longitude'],
                'severity': selected_pothole['severity'],
                'count': selected_pothole['count'],
                'priority': priority,
                'repair_type': repair_type,
                'notes': additional_notes,
                'status': 'New',
                'submission_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'expected_completion': (datetime.now() + timedelta(days=7 if priority == "High" else 14 if priority == "Medium" else 30)).strftime('%Y-%m-%d')
            }
            
            # Add to session state
            st.session_state.repair_requests.append(new_request)
            
            # Save to file
            os.makedirs(os.path.dirname(repair_requests_file), exist_ok=True)
            with open(repair_requests_file, 'w') as f:
                json.dump(st.session_state.repair_requests, f)
            
            # Show success message
            st.markdown(f"""
            <div class="success-message">
                <h3>✅ Repair Request Submitted Successfully!</h3>
                <p>Request ID: {request_id}</p>
                <p>Expected Completion: {new_request['expected_completion']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Show the mascot
            st.markdown(f"""
            <div class="mascot-container">
                <div class="mascot-speech">Great job! I've submitted your repair request. Let's make those roads smooth again!</div>
                <div class="mascot-bounce">🕵️</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Send notification
            twilio_available = check_twilio_credentials()
            if "SMS" in st.session_state.get('alert_settings', {}).get('notify_method', []) and \
               st.session_state.get('alert_settings', {}).get('phone_recipients'):
                
                first_number = st.session_state['alert_settings']['phone_recipients'][0].strip()
                alert_msg = f"Repair Request {request_id} submitted for pothole ID: {selected_pothole['id']} with {priority} priority. Expected completion: {new_request['expected_completion']}"
                
                if twilio_available:
                    success = send_alert(first_number, alert_msg)
                    if success:
                        st.success(f"SMS notification sent to {first_number}")
                    else:
                        st.error("Failed to send SMS notification")
                else:
                    st.info(f"SIMULATED SMS to {first_number}: {alert_msg}")

with tab2:
    st.subheader("Track Repair Requests")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.multiselect(
            "Filter by Status",
            options=["All", "New", "Processing", "Scheduled", "Completed", "Rejected"],
            default=["All"]
        )
    
    with col2:
        priority_filter = st.multiselect(
            "Filter by Priority",
            options=["All", "High", "Medium", "Low"],
            default=["All"]
        )
    
    with col3:
        sort_by = st.selectbox(
            "Sort by",
            options=["Submission Date (Newest)", "Submission Date (Oldest)", "Priority (Highest)", "Priority (Lowest)", "Status"],
            index=0
        )
    
    # Function to sort and filter requests
    def sort_and_filter_requests(requests, status_filter, priority_filter, sort_by):
        # Make a copy to avoid modifying the original
        filtered_requests = requests.copy()
        
        # Apply status filter
        if "All" not in status_filter:
            filtered_requests = [req for req in filtered_requests if req.get('status') in status_filter]
        
        # Apply priority filter
        if "All" not in priority_filter:
            filtered_requests = [req for req in filtered_requests if req.get('priority') in priority_filter]
        
        # Apply sorting
        if sort_by == "Submission Date (Newest)":
            filtered_requests.sort(key=lambda x: x.get('submission_date', ''), reverse=True)
        elif sort_by == "Submission Date (Oldest)":
            filtered_requests.sort(key=lambda x: x.get('submission_date', ''))
        elif sort_by == "Priority (Highest)":
            priority_map = {"High": 3, "Medium": 2, "Low": 1}
            filtered_requests.sort(key=lambda x: priority_map.get(x.get('priority'), 0), reverse=True)
        elif sort_by == "Priority (Lowest)":
            priority_map = {"High": 3, "Medium": 2, "Low": 1}
            filtered_requests.sort(key=lambda x: priority_map.get(x.get('priority'), 0))
        elif sort_by == "Status":
            status_map = {"New": 1, "Processing": 2, "Scheduled": 3, "Completed": 4, "Rejected": 5}
            filtered_requests.sort(key=lambda x: status_map.get(x.get('status'), 0))
        
        return filtered_requests
    
    # Get filtered and sorted requests
    filtered_requests = sort_and_filter_requests(
        st.session_state.repair_requests,
        status_filter,
        priority_filter,
        sort_by
    )
    
    # Display request count
    st.info(f"Showing {len(filtered_requests)} of {len(st.session_state.repair_requests)} repair requests")
    
    # Check if there are any requests
    if not filtered_requests:
        st.warning("No repair requests found matching the selected filters.")
    else:
        # Display repair requests
        for i, request in enumerate(filtered_requests):
            # Create a card for each request
            st.markdown(f"""
            <div class="repair-card">
                <h3>Request ID: {request.get('request_id', 'Unknown')}</h3>
                <span class="status-badge status-{request.get('status', 'New').lower()}">{request.get('status', 'New')}</span>
                <p><strong>Pothole ID:</strong> {request.get('pothole_id', 'Unknown')}</p>
                <p><strong>Location:</strong> ({request.get('latitude', 0):.4f}, {request.get('longitude', 0):.4f})</p>
                <p><strong>Priority:</strong> {request.get('priority', 'Unknown')}</p>
                <p><strong>Repair Type:</strong> {request.get('repair_type', 'Unknown')}</p>
                <p><strong>Submitted:</strong> {request.get('submission_date', 'Unknown')}</p>
                <p><strong>Expected Completion:</strong> {request.get('expected_completion', 'Unknown')}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Create columns for actions
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                # View details button
                if st.button(f"View Details", key=f"view_{i}"):
                    st.session_state.selected_request = request
            
            with col2:
                # Status update button
                if request.get('status') != 'Completed' and request.get('status') != 'Rejected':
                    if st.button(f"Update Status", key=f"update_{i}"):
                        st.session_state.update_request = request
            
            # Add a separator
            st.markdown("---")
    
    # Handle selected request for details
    if 'selected_request' in st.session_state:
        request = st.session_state.selected_request
        
        # Create a modal-like UI
        st.subheader(f"Request Details: {request.get('request_id')}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            **Pothole Information:**
            - Pothole ID: {request.get('pothole_id')}
            - Location: ({request.get('latitude', 0):.4f}, {request.get('longitude', 0):.4f})
            - Severity: {request.get('severity', 0):.1f}/10
            - Potholes Count: {request.get('count', 0)}
            
            **Request Information:**
            - Status: {request.get('status', 'New')}
            - Priority: {request.get('priority', 'Unknown')}
            - Repair Type: {request.get('repair_type', 'Unknown')}
            - Submission Date: {request.get('submission_date', 'Unknown')}
            - Last Updated: {request.get('last_updated', 'Unknown')}
            - Expected Completion: {request.get('expected_completion', 'Unknown')}
            """)
            
            if request.get('notes'):
                st.markdown(f"""
                **Additional Notes:**
                {request.get('notes')}
                """)
        
        with col2:
            # Show a map with the pothole location
            if 'latitude' in request and 'longitude' in request:
                location_df = pd.DataFrame([{
                    'latitude': request['latitude'],
                    'longitude': request['longitude'],
                    'request_id': request['request_id']
                }])
                
                location_map = px.scatter_mapbox(
                    location_df,
                    lat="latitude",
                    lon="longitude",
                    hover_name="request_id",
                    zoom=15,
                    size=[10],
                    color_discrete_sequence=["#FF4B4B"]
                )
                
                location_map.update_layout(
                    mapbox_style="open-street-map",
                    margin={"r": 0, "t": 0, "l": 0, "b": 0},
                    height=300
                )
                
                st.plotly_chart(location_map, use_container_width=True)
        
        # Status update form
        if request.get('status') != 'Completed' and request.get('status') != 'Rejected':
            st.subheader("Update Status")
            
            # Status options based on current status
            current_status = request.get('status', 'New')
            if current_status == 'New':
                status_options = ['New', 'Processing', 'Rejected']
            elif current_status == 'Processing':
                status_options = ['Processing', 'Scheduled', 'Rejected']
            elif current_status == 'Scheduled':
                status_options = ['Scheduled', 'Completed', 'Rejected']
            else:
                status_options = ['New', 'Processing', 'Scheduled', 'Completed', 'Rejected']
            
            new_status = st.selectbox("New Status", options=status_options, index=status_options.index(current_status))
            
            update_notes = st.text_area("Update Notes", placeholder="Enter notes about this status update...")
            
            if new_status == 'Scheduled' and (current_status != 'Scheduled' or not request.get('scheduled_date')):
                scheduled_date = st.date_input("Scheduled Date", value=datetime.now() + timedelta(days=3))
                schedule_notes = st.text_input("Schedule Notes", placeholder="Enter any notes about the schedule...")
            
            if st.button("Save Status Update"):
                # Update the request
                for req in st.session_state.repair_requests:
                    if req.get('request_id') == request.get('request_id'):
                        req['status'] = new_status
                        req['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        
                        # Add update notes
                        if update_notes:
                            if 'update_history' not in req:
                                req['update_history'] = []
                            req['update_history'].append({
                                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                'from_status': current_status,
                                'to_status': new_status,
                                'notes': update_notes
                            })
                        
                        # Add scheduled date if applicable
                        if new_status == 'Scheduled' and (current_status != 'Scheduled' or not req.get('scheduled_date')):
                            req['scheduled_date'] = scheduled_date.strftime('%Y-%m-%d')
                            if schedule_notes:
                                req['schedule_notes'] = schedule_notes
                        
                        # Update expected completion date based on status
                        if new_status == 'Processing':
                            req['expected_completion'] = (datetime.now() + timedelta(days=5 if req.get('priority') == 'High' else 10 if req.get('priority') == 'Medium' else 20)).strftime('%Y-%m-%d')
                        elif new_status == 'Scheduled':
                            req['expected_completion'] = (datetime.strptime(req['scheduled_date'], '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
                        elif new_status == 'Completed':
                            req['completion_date'] = datetime.now().strftime('%Y-%m-%d')
                
                # Save to file
                with open(repair_requests_file, 'w') as f:
                    json.dump(st.session_state.repair_requests, f)
                
                st.success(f"Status updated to {new_status}")
                
                # Clear the selected request to refresh the view
                st.session_state.pop('selected_request', None)
                st.rerun()
        
        # Close details button
        if st.button("Close Details"):
            st.session_state.pop('selected_request', None)
            st.rerun()
    
    # Handle request for status update
    if 'update_request' in st.session_state:
        request = st.session_state.update_request
        
        st.subheader(f"Update Status for Request: {request.get('request_id')}")
        
        # Status options based on current status
        current_status = request.get('status', 'New')
        if current_status == 'New':
            status_options = ['New', 'Processing', 'Rejected']
        elif current_status == 'Processing':
            status_options = ['Processing', 'Scheduled', 'Rejected']
        elif current_status == 'Scheduled':
            status_options = ['Scheduled', 'Completed', 'Rejected']
        else:
            status_options = ['New', 'Processing', 'Scheduled', 'Completed', 'Rejected']
        
        new_status = st.selectbox("New Status", options=status_options, index=status_options.index(current_status), key="update_status_select")
        
        update_notes = st.text_area("Update Notes", placeholder="Enter notes about this status update...", key="update_notes_area")
        
        if new_status == 'Scheduled' and (current_status != 'Scheduled' or not request.get('scheduled_date')):
            scheduled_date = st.date_input("Scheduled Date", value=datetime.now() + timedelta(days=3), key="update_scheduled_date")
            schedule_notes = st.text_input("Schedule Notes", placeholder="Enter any notes about the schedule...", key="update_schedule_notes")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Save Status", key="save_status_update_btn"):
                # Update the request
                for req in st.session_state.repair_requests:
                    if req.get('request_id') == request.get('request_id'):
                        req['status'] = new_status
                        req['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        
                        # Add update notes
                        if update_notes:
                            if 'update_history' not in req:
                                req['update_history'] = []
                            req['update_history'].append({
                                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                'from_status': current_status,
                                'to_status': new_status,
                                'notes': update_notes
                            })
                        
                        # Add scheduled date if applicable
                        if new_status == 'Scheduled' and (current_status != 'Scheduled' or not req.get('scheduled_date')):
                            req['scheduled_date'] = scheduled_date.strftime('%Y-%m-%d')
                            if 'schedule_notes' in locals() and schedule_notes:
                                req['schedule_notes'] = schedule_notes
                        
                        # Update expected completion date based on status
                        if new_status == 'Processing':
                            req['expected_completion'] = (datetime.now() + timedelta(days=5 if req.get('priority') == 'High' else 10 if req.get('priority') == 'Medium' else 20)).strftime('%Y-%m-%d')
                        elif new_status == 'Scheduled':
                            scheduled_date_str = req.get('scheduled_date', datetime.now().strftime('%Y-%m-%d'))
                            req['expected_completion'] = (datetime.strptime(scheduled_date_str, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
                        elif new_status == 'Completed':
                            req['completion_date'] = datetime.now().strftime('%Y-%m-%d')
                
                # Save to file
                with open(repair_requests_file, 'w') as f:
                    json.dump(st.session_state.repair_requests, f)
                
                st.success(f"Status updated to {new_status}")
                
                # Clear the update request to refresh the view
                st.session_state.pop('update_request', None)
                st.rerun()
        
        with col2:
            if st.button("Cancel", key="cancel_update_btn"):
                st.session_state.pop('update_request', None)
                st.rerun()

with tab3:
    st.subheader("Repair Request Analytics")
    
    # Check if there are any requests
    if not st.session_state.repair_requests:
        st.warning("No repair requests available for analysis.")
        st.stop()
    
    # Create a DataFrame from the repair requests
    requests_df = pd.DataFrame(st.session_state.repair_requests)
    
    # Display summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_requests = len(requests_df)
        st.metric("Total Requests", total_requests)
    
    with col2:
        if 'status' in requests_df.columns:
            completed = len(requests_df[requests_df['status'] == 'Completed'])
            completion_rate = (completed / total_requests) * 100 if total_requests > 0 else 0
            st.metric("Completion Rate", f"{completion_rate:.1f}%")
    
    with col3:
        if 'priority' in requests_df.columns:
            high_priority = len(requests_df[requests_df['priority'] == 'High'])
            high_priority_pct = (high_priority / total_requests) * 100 if total_requests > 0 else 0
            st.metric("High Priority", f"{high_priority} ({high_priority_pct:.1f}%)")
    
    with col4:
        if 'submission_date' in requests_df.columns:
            # Convert to datetime
            requests_df['submission_datetime'] = pd.to_datetime(requests_df['submission_date'])
            
            # Calculate average age of open requests
            open_requests = requests_df[~requests_df['status'].isin(['Completed', 'Rejected'])]
            if not open_requests.empty:
                current_time = datetime.now()
                open_requests['age_days'] = (current_time - open_requests['submission_datetime']).dt.days
                avg_age = open_requests['age_days'].mean()
                st.metric("Avg Request Age", f"{avg_age:.1f} days")
            else:
                st.metric("Avg Request Age", "0 days")
    
    # Status breakdown
    st.subheader("Request Status Breakdown")
    
    if 'status' in requests_df.columns:
        status_counts = requests_df['status'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Count']
        
        # Create pie chart
        fig = px.pie(
            status_counts,
            values='Count',
            names='Status',
            title='Request Status Distribution',
            color='Status',
            color_discrete_map={
                'New': '#4b79ff',
                'Processing': '#FFA500',
                'Scheduled': '#9932CC',
                'Completed': '#4CAF50',
                'Rejected': '#FF4B4B'
            }
        )
        
        fig.update_layout(
            legend_title="Status",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Priority vs Status
    st.subheader("Priority vs Status")
    
    if 'status' in requests_df.columns and 'priority' in requests_df.columns:
        # Create a cross-tabulation
        priority_status = pd.crosstab(requests_df['priority'], requests_df['status'])
        
        # Convert to long format for plotting
        priority_status_long = priority_status.reset_index().melt(
            id_vars=['priority'],
            var_name='status',
            value_name='count'
        )
        
        # Create grouped bar chart
        fig = px.bar(
            priority_status_long,
            x='priority',
            y='count',
            color='status',
            title='Request Status by Priority',
            labels={'priority': 'Priority', 'count': 'Number of Requests', 'status': 'Status'},
            color_discrete_map={
                'New': '#4b79ff',
                'Processing': '#FFA500',
                'Scheduled': '#9932CC',
                'Completed': '#4CAF50',
                'Rejected': '#FF4B4B'
            },
            category_orders={"priority": ["High", "Medium", "Low"]}
        )
        
        fig.update_layout(
            xaxis_title="Priority",
            yaxis_title="Number of Requests",
            legend_title="Status",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Time-based analysis
    st.subheader("Request Timeline Analysis")
    
    if 'submission_date' in requests_df.columns:
        # Ensure submission_datetime column exists
        if 'submission_datetime' not in requests_df.columns:
            requests_df['submission_datetime'] = pd.to_datetime(requests_df['submission_date'])
        
        # Extract date only
        requests_df['submission_date_only'] = requests_df['submission_datetime'].dt.date
        
        # Group by date and count
        daily_counts = requests_df.groupby('submission_date_only').size().reset_index(name='count')
        
        # Create time series chart
        fig = px.line(
            daily_counts,
            x='submission_date_only',
            y='count',
            title='Repair Requests Over Time',
            labels={'submission_date_only': 'Date', 'count': 'Number of Requests'},
            markers=True
        )
        
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Number of Requests",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Repair type breakdown
    st.subheader("Repair Type Analysis")
    
    if 'repair_type' in requests_df.columns:
        repair_counts = requests_df['repair_type'].value_counts().reset_index()
        repair_counts.columns = ['Repair Type', 'Count']
        
        # Create bar chart
        fig = px.bar(
            repair_counts,
            x='Repair Type',
            y='Count',
            title='Repair Types Requested',
            color='Repair Type',
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        
        fig.update_layout(
            xaxis_title="Repair Type",
            yaxis_title="Number of Requests",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Geographical analysis
    st.subheader("Geographical Analysis")
    
    if 'latitude' in requests_df.columns and 'longitude' in requests_df.columns:
        # Create map with repair requests colored by status
        map_df = requests_df.copy()
        
        # Create a color map for status
        status_color_map = {
            'New': '#4b79ff',
            'Processing': '#FFA500',
            'Scheduled': '#9932CC',
            'Completed': '#4CAF50',
            'Rejected': '#FF4B4B'
        }
        
        # Create map
        fig = px.scatter_mapbox(
            map_df,
            lat="latitude",
            lon="longitude",
            color="status" if 'status' in map_df.columns else None,
            color_discrete_map=status_color_map,
            size=[10] * len(map_df),
            zoom=10,
            hover_name="request_id",
            hover_data={
                "priority": True,
                "status": True,
                "repair_type": True,
                "submission_date": True,
                "latitude": False,
                "longitude": False
            },
            title="Repair Request Map"
        )
        
        fig.update_layout(
            mapbox_style="open-street-map",
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            height=500,
            legend_title="Status"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Expected vs actual completion time
    st.subheader("Completion Time Analysis")
    
    if 'status' in requests_df.columns and 'expected_completion' in requests_df.columns:
        completed_requests = requests_df[requests_df['status'] == 'Completed'].copy()
        
        if not completed_requests.empty and 'completion_date' in completed_requests.columns:
            # Convert dates to datetime
            completed_requests['expected_completion_dt'] = pd.to_datetime(completed_requests['expected_completion'])
            completed_requests['completion_date_dt'] = pd.to_datetime(completed_requests['completion_date'])
            
            # Calculate days difference
            completed_requests['days_difference'] = (completed_requests['completion_date_dt'] - completed_requests['expected_completion_dt']).dt.days
            
            # Categorize as early, on time, or late
            completed_requests['completion_status'] = pd.cut(
                completed_requests['days_difference'],
                bins=[-float('inf'), -1, 1, float('inf')],
                labels=['Early', 'On Time', 'Late']
            )
            
            # Count by completion status
            completion_counts = completed_requests['completion_status'].value_counts().reset_index()
            completion_counts.columns = ['Completion Status', 'Count']
            
            # Create bar chart
            fig = px.bar(
                completion_counts,
                x='Completion Status',
                y='Count',
                title='Repair Completion Time Performance',
                color='Completion Status',
                color_discrete_map={
                    'Early': '#4CAF50',
                    'On Time': '#FFA500',
                    'Late': '#FF4B4B'
                },
                category_orders={"Completion Status": ["Early", "On Time", "Late"]}
            )
            
            fig.update_layout(
                xaxis_title="Completion Status",
                yaxis_title="Number of Requests",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Calculate average days difference by priority
            if 'priority' in completed_requests.columns:
                avg_days_by_priority = completed_requests.groupby('priority')['days_difference'].mean().reset_index()
                avg_days_by_priority.columns = ['Priority', 'Average Days Difference']
                
                # Create bar chart
                fig = px.bar(
                    avg_days_by_priority,
                    x='Priority',
                    y='Average Days Difference',
                    title='Average Completion Time Difference by Priority',
                    color='Priority',
                    color_discrete_sequence=px.colors.qualitative.Pastel,
                    category_orders={"Priority": ["High", "Medium", "Low"]}
                )
                
                fig.update_layout(
                    xaxis_title="Priority",
                    yaxis_title="Average Days Difference (Negative = Early)",
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No completed requests with completion dates available for analysis.")

# Add a section about one-click repair requests
st.markdown("---")
st.markdown("""
## One-Click Road Repair Requests

The One-Click Road Repair Request system allows you to:

1. **Quickly submit repair requests** for detected potholes
2. **Track the status** of all submitted requests
3. **Analyze repair performance** with detailed analytics
4. **Prioritize critical areas** based on severity and impact
5. **Coordinate with maintenance teams** for efficient repairs

This system streamlines the process from detection to repair, helping make roads safer for everyone.
""")

# Show animated mascot
st.markdown(load_mascot_animation(), unsafe_allow_html=True)
st.markdown("""
<div class="mascot-container">
    <div class="mascot-speech">Need help with road repairs? I'm here to assist! Just let me know which potholes need fixing.</div>
    <div class="mascot-bounce">🕵️</div>
</div>
""", unsafe_allow_html=True)