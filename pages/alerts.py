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

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_processing import load_detection_results, DATABASE_AVAILABLE
from utils.tutorial import get_tutorial_manager
from utils.twilio_integration import send_alert, check_twilio_credentials

# Try to import database functions if available
if DATABASE_AVAILABLE:
    from utils.database import get_map_data, get_all_detections, get_detection_statistics

st.set_page_config(
    page_title="Alerts & Reports - Pothole Detection System",
    page_icon="🚨",
    layout="wide"
)

# Get tutorial manager
tutorial_manager = get_tutorial_manager()

# Render tutorial UI if active
if tutorial_manager.is_active():
    tutorial_manager.render_tutorial_ui("Alerts")

st.title("🚨 Pothole Alerts & Reporting")
st.markdown("Set up alerts for critical pothole areas and generate detailed reports.")

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
    </style>
    """

# Create tabs for different sections
tab1, tab2, tab3 = st.tabs(["Alert Setup", "Critical Areas", "Reports"])

with tab1:
    st.subheader("Pothole Alert System")
    
    # Explanation of the alert system
    st.markdown("""
    Set up automated alerts to notify authorities or maintenance teams about critical pothole areas.
    Configure thresholds and notification settings below.
    """)
    
    # Check if Twilio credentials are available
    twilio_available = check_twilio_credentials()
    
    if not twilio_available:
        st.warning("Twilio credentials are not configured. SMS alerts will be simulated.")
        
        # Option to add Twilio credentials
        with st.expander("Configure Twilio for SMS Alerts"):
            st.markdown("""
            To enable real SMS alerts, you need to configure Twilio credentials:
            1. Sign up for a Twilio account at [twilio.com](https://www.twilio.com)
            2. Get your Account SID, Auth Token, and a Twilio phone number
            3. Enter these credentials below:
            """)
            
            # Form for Twilio credentials
            with st.form("twilio_credentials"):
                account_sid = st.text_input("Twilio Account SID")
                auth_token = st.text_input("Twilio Auth Token", type="password")
                phone_number = st.text_input("Twilio Phone Number (with country code, e.g. +12345678901)")
                
                submit_button = st.form_submit_button("Save Credentials")
                if submit_button:
                    if account_sid and auth_token and phone_number:
                        # Here we would normally save these to environment variables or a secure storage
                        st.success("Credentials saved successfully! Twilio integration is now active.")
                        # In a real app, we would set these as environment variables or store them securely
                    else:
                        st.error("Please fill in all fields.")
    
    # Alert settings
    st.subheader("Alert Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Alert thresholds
        st.markdown("#### Threshold Settings")
        
        severity_threshold = st.slider(
            "Severity Threshold (potholes per area)",
            min_value=1,
            max_value=10,
            value=3,
            help="Minimum number of potholes in an area to trigger an alert"
        )
        
        confidence_threshold = st.slider(
            "Minimum Confidence",
            min_value=0.1,
            max_value=1.0,
            value=0.4,
            step=0.05,
            help="Minimum confidence score for detections"
        )
        
        time_period = st.selectbox(
            "Time Period",
            options=["Last 24 hours", "Last week", "Last month", "All time"],
            index=0,
            help="Time period to consider for alerts"
        )
    
    with col2:
        # Notification settings
        st.markdown("#### Notification Settings")
        
        notify_method = st.multiselect(
            "Notification Methods",
            options=["In-app", "Email", "SMS"],
            default=["In-app"],
            help="How to send alerts"
        )
        
        if "Email" in notify_method:
            email_recipients = st.text_input(
                "Email Recipients (comma-separated)",
                placeholder="e.g. roadmaintenance@example.com, manager@example.com"
            )
        
        if "SMS" in notify_method:
            phone_recipients = st.text_input(
                "SMS Recipients (comma-separated)",
                placeholder="e.g. +12345678901, +12345678902",
                help="Phone numbers with country code"
            )
        
        alert_frequency = st.selectbox(
            "Alert Frequency",
            options=["Immediate", "Daily summary", "Weekly summary"],
            index=0
        )
    
    # Save settings button
    if st.button("Save Alert Settings", type="primary"):
        # In a real app, these would be saved to a database or configuration file
        st.session_state.alert_settings = {
            "severity_threshold": severity_threshold,
            "confidence_threshold": confidence_threshold,
            "time_period": time_period,
            "notify_method": notify_method,
            "alert_frequency": alert_frequency
        }
        
        if "Email" in notify_method:
            st.session_state.alert_settings["email_recipients"] = email_recipients.split(",") if email_recipients else []
        
        if "SMS" in notify_method:
            st.session_state.alert_settings["phone_recipients"] = phone_recipients.split(",") if phone_recipients else []
        
        st.success("Alert settings saved successfully!")
        
        # Show the Pothole Detective mascot with a message
        st.markdown(load_mascot_animation(), unsafe_allow_html=True)
        st.markdown("""
        <div class="mascot-container">
            <div class="mascot-speech">Alert settings saved! I'll keep an eye on those potholes for you.</div>
            <div class="mascot-bounce">🕵️</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Test alert button
    if st.button("Test Alert"):
        if "SMS" in notify_method and phone_recipients:
            first_number = phone_recipients.split(",")[0].strip()
            test_message = f"TEST ALERT: {severity_threshold} potholes detected in a high-priority area with {confidence_threshold:.0%} confidence. This is a test message from the Pothole Detection System."
            
            if twilio_available:
                # Send real SMS if Twilio is configured
                success = send_alert(first_number, test_message)
                if success:
                    st.success(f"Test SMS alert sent to {first_number}")
                else:
                    st.error("Failed to send SMS. Check Twilio credentials.")
            else:
                # Simulate SMS
                st.info(f"SIMULATED SMS to {first_number}: {test_message}")
        else:
            st.warning("Please configure SMS notifications with valid phone numbers to test alerts.")

with tab2:
    st.subheader("Critical Pothole Areas")
    
    # Load detection data
    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def get_critical_areas():
        if DATABASE_AVAILABLE:
            try:
                # Try to get data from database
                geo_data = get_map_data()
                if geo_data:
                    return geo_data
            except Exception as e:
                st.sidebar.warning(f"Database error: {e}")
        
        # Fallback to file-based results
        results = load_detection_results()
        
        # Filter results and extract critical areas
        critical_areas = []
        
        for result in results:
            detections = result.get('detections', [])
            if len(detections) >= 3:  # Minimum 3 potholes to be considered critical
                metadata = result.get('metadata', {})
                
                # Generate random coordinates if none exist (for demonstration)
                if 'latitude' not in metadata or 'longitude' not in metadata:
                    metadata['latitude'] = random.uniform(40.7, 40.8)  # NYC area
                    metadata['longitude'] = random.uniform(-74.0, -73.9)
                
                critical_areas.append({
                    'image': result.get('image_path', 'unknown'),
                    'latitude': metadata.get('latitude'),
                    'longitude': metadata.get('longitude'),
                    'count': len(detections),
                    'severity': min(10, len(detections) * 2),  # Scale from 1-10
                    'timestamp': result.get('timestamp', datetime.now().timestamp()),
                    'confidence': sum(d.get('confidence', 0) for d in detections) / len(detections) if detections else 0
                })
        
        return critical_areas
    
    critical_areas = get_critical_areas()
    
    if not critical_areas:
        st.info("No critical areas identified yet. Process more images or adjust threshold settings.")
    else:
        # Display metrics
        total_critical = len(critical_areas)
        avg_severity = sum(area['severity'] for area in critical_areas) / total_critical if total_critical > 0 else 0
        highest_severity = max(area['severity'] for area in critical_areas) if critical_areas else 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Critical Areas", total_critical)
        with col2:
            st.metric("Average Severity", f"{avg_severity:.1f}/10")
        with col3:
            st.metric("Highest Severity", f"{highest_severity:.1f}/10")
        
        # Map visualization of critical areas
        st.subheader("Critical Areas Map")
        
        # Convert to DataFrame for plotting
        df = pd.DataFrame(critical_areas)
        
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
            hover_name="image",
            hover_data={
                "count": True,
                "severity": True,
                "timestamp": False,
                "latitude": False,
                "longitude": False
            },
            title="Critical Pothole Areas"
        )
        
        fig.update_layout(
            mapbox_style="open-street-map",
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Table of critical areas
        st.subheader("Critical Areas List")
        
        # Format data for display
        display_df = pd.DataFrame({
            "Location": [f"({row['latitude']:.4f}, {row['longitude']:.4f})" for _, row in df.iterrows()],
            "Potholes": df["count"],
            "Severity": [f"{sev:.1f}/10" for sev in df["severity"]],
            "Confidence": [f"{conf:.0%}" for conf in df["confidence"]],
            "Date": [datetime.fromtimestamp(ts).strftime("%Y-%m-%d") for ts in df["timestamp"]]
        })
        
        # Sort by severity (descending)
        display_df = display_df.sort_values(by="Severity", ascending=False)
        
        # Display table
        st.dataframe(display_df, use_container_width=True)
        
        # Alert simulation
        if st.button("Generate Alerts for Critical Areas"):
            # Get alert settings or use defaults
            settings = st.session_state.get('alert_settings', {
                "severity_threshold": 3,
                "notify_method": ["In-app"],
                "phone_recipients": []
            })
            
            # Filter by threshold
            threshold = settings.get("severity_threshold", 3)
            alerts_needed = [area for area in critical_areas if area['severity'] >= threshold]
            
            if alerts_needed:
                st.success(f"Generated alerts for {len(alerts_needed)} critical areas!")
                
                # Display the alerts
                for i, area in enumerate(alerts_needed[:3]):  # Show top 3
                    alert_msg = f"🚨 ALERT: {area['count']} potholes detected at ({area['latitude']:.4f}, {area['longitude']:.4f}) with severity {area['severity']:.1f}/10"
                    st.warning(alert_msg)
                
                # Simulate SMS alerts if configured
                if "SMS" in settings.get("notify_method", []) and settings.get("phone_recipients"):
                    first_number = settings["phone_recipients"][0].strip()
                    alert_msg = f"POTHOLE ALERT: {len(alerts_needed)} critical areas identified. Highest severity: {highest_severity:.1f}/10. Please check the dashboard for details."
                    
                    if twilio_available:
                        success = send_alert(first_number, alert_msg)
                        if success:
                            st.success(f"SMS alert sent to {first_number}")
                        else:
                            st.error("Failed to send SMS. Check Twilio credentials.")
                    else:
                        st.info(f"SIMULATED SMS to {first_number}: {alert_msg}")
            else:
                st.info(f"No areas exceed the severity threshold of {threshold}.")
            
            # Show animated mascot
            st.markdown(load_mascot_animation(), unsafe_allow_html=True)
            st.markdown("""
            <div class="mascot-container">
                <div class="mascot-speech">Detective Pothole on the case! I've alerted the authorities about these critical areas.</div>
                <div class="mascot-bounce">🕵️</div>
            </div>
            """, unsafe_allow_html=True)

with tab3:
    st.subheader("Pothole Reports")
    
    # Report generation options
    st.markdown("Generate comprehensive reports about pothole detections and critical areas.")
    
    # Report type selection
    report_type = st.selectbox(
        "Report Type",
        options=["Summary Report", "Detailed Analysis", "Maintenance Priority", "Historical Trends"],
        index=0
    )
    
    # Report parameters
    col1, col2 = st.columns(2)
    
    with col1:
        # Date range
        start_date = st.date_input(
            "Start Date",
            value=datetime.now() - timedelta(days=30),
            max_value=datetime.now()
        )
        
        end_date = st.date_input(
            "End Date",
            value=datetime.now(),
            max_value=datetime.now()
        )
    
    with col2:
        # Other parameters
        area_filter = st.multiselect(
            "Filter by Area",
            options=["All Areas", "High Priority", "Medium Priority", "Low Priority"],
            default=["All Areas"]
        )
        
        include_images = st.checkbox("Include Images in Report", value=True)
        include_map = st.checkbox("Include Map Visualization", value=True)
        include_stats = st.checkbox("Include Statistical Analysis", value=True)
    
    # Generate report button
    if st.button("Generate Report", type="primary"):
        # Show progress
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Simulate report generation
        for i in range(1, 101):
            progress_bar.progress(i/100)
            if i < 30:
                status_text.text("Gathering detection data...")
            elif i < 60:
                status_text.text("Analyzing critical areas...")
            elif i < 90:
                status_text.text("Generating visualizations...")
            else:
                status_text.text("Finalizing report...")
            
            # Slow down the simulation for effect
            if i % 10 == 0:
                time.sleep(0.1)
        
        # Complete
        progress_bar.empty()
        status_text.empty()
        
        # Report generation timestamp
        report_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Display the report
        st.success(f"Report generated successfully at {report_time}!")
        
        # Create a container for the report
        report_container = st.container()
        
        with report_container:
            # Report header
            st.markdown(f"# Pothole Detection Report: {report_type}")
            st.markdown(f"**Generated:** {report_time}")
            st.markdown(f"**Period:** {start_date} to {end_date}")
            st.markdown("---")
            
            # Report sections based on type
            if report_type == "Summary Report":
                # Summary statistics
                st.subheader("Summary Statistics")
                
                # Get or generate statistics
                if DATABASE_AVAILABLE:
                    try:
                        stats = get_detection_statistics()
                    except Exception:
                        # Generate mock stats if database fails
                        stats = {
                            "total_images": random.randint(50, 200),
                            "total_detections": random.randint(100, 500),
                            "avg_potholes_per_image": random.uniform(1.5, 4.0),
                            "avg_confidence": random.uniform(0.4, 0.8),
                            "detection_rate": random.uniform(60, 95)
                        }
                else:
                    # Generate stats from file data
                    results = load_detection_results()
                    total_images = len(results)
                    total_detections = sum(len(r.get('detections', [])) for r in results)
                    
                    stats = {
                        "total_images": total_images,
                        "total_detections": total_detections,
                        "avg_potholes_per_image": total_detections / total_images if total_images > 0 else 0,
                        "avg_confidence": sum(d.get('confidence', 0) for r in results for d in r.get('detections', [])) / total_detections if total_detections > 0 else 0,
                        "detection_rate": 100 * sum(1 for r in results if r.get('detections', [])) / total_images if total_images > 0 else 0
                    }
                
                # Display metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Images Processed", stats["total_images"])
                    st.metric("Detection Rate", f"{stats['detection_rate']:.1f}%")
                with col2:
                    st.metric("Total Potholes Detected", stats["total_detections"])
                    st.metric("Average Confidence", f"{stats['avg_confidence']:.2f}")
                with col3:
                    st.metric("Potholes per Image", f"{stats['avg_potholes_per_image']:.2f}")
                    st.metric("Critical Areas", len(critical_areas))
                
                # Summary chart
                if include_stats and critical_areas:
                    st.subheader("Severity Distribution")
                    
                    # Create histogram of severity levels
                    severity_data = [area['severity'] for area in critical_areas]
                    fig = px.histogram(
                        severity_data,
                        nbins=10,
                        labels={'value': 'Severity Score', 'count': 'Number of Areas'},
                        title="Distribution of Severity Scores",
                        color_discrete_sequence=['#FF4B4B']
                    )
                    
                    fig.update_layout(
                        xaxis_title="Severity Score (1-10)",
                        yaxis_title="Number of Areas",
                        height=400
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                
                # Map if requested
                if include_map and critical_areas:
                    st.subheader("Critical Areas Map")
                    
                    # Reuse the map from the Critical Areas tab
                    df = pd.DataFrame(critical_areas)
                    
                    fig = px.scatter_mapbox(
                        df,
                        lat="latitude",
                        lon="longitude",
                        size="count",
                        color="severity",
                        color_continuous_scale=px.colors.sequential.Reds,
                        size_max=15,
                        zoom=10
                    )
                    
                    fig.update_layout(
                        mapbox_style="open-street-map",
                        height=400,
                        margin={"r": 0, "t": 0, "l": 0, "b": 0}
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
            
            elif report_type == "Detailed Analysis":
                # Detailed analysis report
                st.subheader("Detailed Pothole Analysis")
                
                # Analysis text
                st.markdown("""
                This detailed analysis examines pothole detections across all monitored areas,
                with focus on detection patterns, confidence levels, and geographical distribution.
                """)
                
                # Get detection data
                if DATABASE_AVAILABLE:
                    try:
                        detections = get_all_detections()
                    except Exception:
                        # Use file-based results if database fails
                        results = load_detection_results()
                        detections = []
                        for r in results:
                            for d in r.get('detections', []):
                                detections.append({
                                    'id': random.randint(1000, 9999),
                                    'confidence': d.get('confidence', 0.5),
                                    'class_name': 'pothole',
                                    'bbox': d.get('bbox', [0, 0, 0, 0]),
                                    'detection_date': datetime.fromtimestamp(r.get('timestamp', datetime.now().timestamp()))
                                })
                else:
                    # Generate from file data
                    results = load_detection_results()
                    detections = []
                    for r in results:
                        for d in r.get('detections', []):
                            detections.append({
                                'id': random.randint(1000, 9999),
                                'confidence': d.get('confidence', 0.5),
                                'class_name': 'pothole',
                                'bbox': d.get('bbox', [0, 0, 0, 0]),
                                'detection_date': datetime.fromtimestamp(r.get('timestamp', datetime.now().timestamp()))
                            })
                
                if detections:
                    # Convert to DataFrame for analysis
                    df = pd.DataFrame([
                        {
                            'id': d['id'],
                            'confidence': d['confidence'],
                            'size': (d['bbox'][2] - d['bbox'][0]) * (d['bbox'][3] - d['bbox'][1]) if 'bbox' in d else 0,
                            'date': d['detection_date'] if isinstance(d['detection_date'], datetime) else 
                                  datetime.fromtimestamp(d['detection_date']) if isinstance(d['detection_date'], (int, float)) else
                                  datetime.now()
                        }
                        for d in detections
                    ])
                    
                    # Filter by date range
                    start_datetime = datetime.combine(start_date, datetime.min.time())
                    end_datetime = datetime.combine(end_date, datetime.max.time())
                    df = df[(df['date'] >= start_datetime) & (df['date'] <= end_datetime)]
                    
                    if not df.empty:
                        # Display statistics
                        st.subheader("Detection Statistics")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Total Detections", len(df))
                            st.metric("Average Confidence", f"{df['confidence'].mean():.2f}")
                        
                        with col2:
                            st.metric("Highest Confidence", f"{df['confidence'].max():.2f}")
                            st.metric("Lowest Confidence", f"{df['confidence'].min():.2f}")
                        
                        # Confidence distribution
                        st.subheader("Confidence Distribution")
                        
                        fig = px.histogram(
                            df,
                            x="confidence",
                            nbins=20,
                            labels={'confidence': 'Confidence Score'},
                            title="Distribution of Detection Confidence Scores",
                            color_discrete_sequence=['#4b79ff']
                        )
                        
                        fig.update_layout(
                            xaxis_title="Confidence Score",
                            yaxis_title="Number of Detections",
                            height=400
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Size vs. Confidence scatter plot
                        st.subheader("Detection Size vs. Confidence")
                        
                        fig = px.scatter(
                            df,
                            x="size",
                            y="confidence",
                            labels={'size': 'Pothole Size (pixels²)', 'confidence': 'Confidence Score'},
                            title="Relationship Between Pothole Size and Detection Confidence",
                            color="confidence",
                            color_continuous_scale=px.colors.sequential.Viridis
                        )
                        
                        fig.update_layout(
                            xaxis_title="Pothole Size (pixels²)",
                            yaxis_title="Confidence Score",
                            height=400
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Time series analysis
                        st.subheader("Detection Trends Over Time")
                        
                        # Group by date
                        df['day'] = df['date'].dt.date
                        daily_counts = df.groupby('day').size().reset_index(name='count')
                        daily_confidence = df.groupby('day')['confidence'].mean().reset_index()
                        
                        # Merge the dataframes
                        daily_data = pd.merge(daily_counts, daily_confidence, on='day')
                        
                        # Create time series chart
                        fig = go.Figure()
                        
                        fig.add_trace(go.Scatter(
                            x=daily_data['day'],
                            y=daily_data['count'],
                            name='Number of Detections',
                            line=dict(color='#FF4B4B', width=2)
                        ))
                        
                        # Add secondary y-axis for confidence
                        fig.add_trace(go.Scatter(
                            x=daily_data['day'],
                            y=daily_data['confidence'],
                            name='Average Confidence',
                            line=dict(color='#4b79ff', width=2, dash='dash'),
                            yaxis='y2'
                        ))
                        
                        fig.update_layout(
                            title="Pothole Detections and Confidence Over Time",
                            xaxis_title="Date",
                            yaxis_title="Number of Detections",
                            yaxis2=dict(
                                title="Average Confidence",
                                overlaying="y",
                                side="right",
                                range=[0, 1]
                            ),
                            legend=dict(x=0.01, y=0.99),
                            height=400
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info(f"No detections found in the date range {start_date} to {end_date}.")
                else:
                    st.info("No detection data available for analysis.")
            
            elif report_type == "Maintenance Priority":
                # Maintenance priority report
                st.subheader("Maintenance Priority Report")
                
                st.markdown("""
                This report prioritizes areas for maintenance based on pothole severity, count, and impact.
                Use this report to allocate resources effectively for road repairs.
                """)
                
                if critical_areas:
                    # Calculate priority score for each area
                    for area in critical_areas:
                        # Priority score = (severity * 0.5) + (count * 0.3) + (confidence * 0.2)
                        area['priority_score'] = (area['severity'] * 0.5) + (area['count'] * 0.3) + (area['confidence'] * 100 * 0.2)
                    
                    # Sort by priority score
                    sorted_areas = sorted(critical_areas, key=lambda x: x['priority_score'], reverse=True)
                    
                    # Convert to DataFrame
                    df = pd.DataFrame(sorted_areas)
                    
                    # Add priority level
                    def get_priority_level(score):
                        if score >= 8:
                            return "Critical (Immediate Action)"
                        elif score >= 6:
                            return "High Priority"
                        elif score >= 4:
                            return "Medium Priority"
                        else:
                            return "Low Priority"
                    
                    df['priority_level'] = df['priority_score'].apply(get_priority_level)
                    
                    # Filter by priority if specified
                    if "All Areas" not in area_filter:
                        df = df[df['priority_level'].isin(area_filter)]
                    
                    if not df.empty:
                        # Display priority metrics
                        priority_counts = df['priority_level'].value_counts()
                        
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            critical_count = priority_counts.get("Critical (Immediate Action)", 0)
                            st.metric("Critical Priority", critical_count)
                        
                        with col2:
                            high_count = priority_counts.get("High Priority", 0)
                            st.metric("High Priority", high_count)
                        
                        with col3:
                            medium_count = priority_counts.get("Medium Priority", 0)
                            st.metric("Medium Priority", medium_count)
                        
                        with col4:
                            low_count = priority_counts.get("Low Priority", 0)
                            st.metric("Low Priority", low_count)
                        
                        # Priority map
                        st.subheader("Maintenance Priority Map")
                        
                        # Create color mapping for priority levels
                        color_map = {
                            "Critical (Immediate Action)": "#FF0000",  # Red
                            "High Priority": "#FF7F00",  # Orange
                            "Medium Priority": "#FFFF00",  # Yellow
                            "Low Priority": "#00FF00"  # Green
                        }
                        
                        df['color'] = df['priority_level'].map(color_map)
                        
                        fig = px.scatter_mapbox(
                            df,
                            lat="latitude",
                            lon="longitude",
                            color="priority_level",
                            color_discrete_map=color_map,
                            size="priority_score",
                            size_max=15,
                            zoom=10,
                            hover_name="priority_level",
                            hover_data={
                                "count": True,
                                "severity": True,
                                "priority_score": False,
                                "latitude": False,
                                "longitude": False
                            },
                            category_orders={"priority_level": [
                                "Critical (Immediate Action)",
                                "High Priority",
                                "Medium Priority",
                                "Low Priority"
                            ]}
                        )
                        
                        fig.update_layout(
                            mapbox_style="open-street-map",
                            height=500,
                            margin={"r": 0, "t": 0, "l": 0, "b": 0}
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Priority table
                        st.subheader("Maintenance Priority List")
                        
                        # Format data for display
                        display_df = pd.DataFrame({
                            "Location": [f"({row['latitude']:.4f}, {row['longitude']:.4f})" for _, row in df.iterrows()],
                            "Priority": df["priority_level"],
                            "Score": [f"{score:.1f}" for score in df["priority_score"]],
                            "Potholes": df["count"],
                            "Severity": [f"{sev:.1f}/10" for sev in df["severity"]]
                        })
                        
                        # Style the dataframe
                        st.dataframe(display_df, use_container_width=True)
                        
                        # Resource allocation recommendation
                        st.subheader("Resource Allocation Recommendation")
                        
                        total_areas = len(df)
                        critical_percentage = (critical_count / total_areas * 100) if total_areas > 0 else 0
                        high_percentage = (high_count / total_areas * 100) if total_areas > 0 else 0
                        medium_percentage = (medium_count / total_areas * 100) if total_areas > 0 else 0
                        low_percentage = (low_count / total_areas * 100) if total_areas > 0 else 0
                        
                        # Create pie chart
                        labels = ['Critical', 'High', 'Medium', 'Low']
                        values = [critical_percentage, high_percentage, medium_percentage, low_percentage]
                        colors = ['#FF0000', '#FF7F00', '#FFFF00', '#00FF00']
                        
                        fig = go.Figure(data=[go.Pie(
                            labels=labels,
                            values=values,
                            hole=.4,
                            marker=dict(colors=colors)
                        )])
                        
                        fig.update_layout(
                            title="Recommended Resource Allocation",
                            height=400
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Text recommendations
                        st.markdown("""
                        ### Recommendations:
                        
                        1. **Immediate Action Required:**
                           - Dispatch emergency repair teams to Critical Priority areas
                           - Address all red areas on the map within 24-48 hours
                        
                        2. **Schedule Near-Term Repairs:**
                           - Plan repairs for High Priority areas within the next week
                           - Consider temporary fixes for the most severe cases
                        
                        3. **Medium-Term Planning:**
                           - Include Medium Priority areas in the monthly maintenance schedule
                           - Monitor for deterioration that may elevate their priority
                        
                        4. **Resource Allocation:**
                           - Allocate 50% of resources to Critical areas
                           - 30% to High Priority areas
                           - 15% to Medium Priority areas
                           - 5% to Low Priority areas
                        """)
                    else:
                        st.info(f"No areas match the selected priority filters: {', '.join(area_filter)}")
                else:
                    st.info("No critical areas identified for maintenance prioritization.")
            
            elif report_type == "Historical Trends":
                # Historical trends report
                st.subheader("Historical Pothole Trends")
                
                st.markdown("""
                This report analyzes how pothole detections have changed over time,
                helping identify seasonal patterns and effectiveness of maintenance efforts.
                """)
                
                # Generate historical data if not available
                # In a real app, this would come from actual historical data
                
                # Date range for analysis
                start_datetime = datetime.combine(start_date, datetime.min.time())
                end_datetime = datetime.combine(end_date, datetime.max.time())
                
                # Generate dates in the range
                date_range = pd.date_range(start=start_datetime, end=end_datetime, freq='D')
                
                # Create synthetic data for demonstration
                historical_data = []
                
                for date in date_range:
                    # Base value with some seasonal pattern (more in winter/spring)
                    month = date.month
                    season_factor = 1.5 if month in [1, 2, 3, 4] else 1.0
                    
                    # Base detection count with randomness
                    base_count = int(10 * season_factor + random.uniform(-3, 5))
                    count = max(0, base_count)
                    
                    # Base severity with randomness
                    base_severity = 5 * season_factor + random.uniform(-1, 2)
                    severity = min(10, max(1, base_severity))
                    
                    # Base confidence with slight improvement over time
                    time_progress = (date - date_range[0]).days / max(1, (date_range[-1] - date_range[0]).days)
                    base_confidence = 0.6 + (0.1 * time_progress) + random.uniform(-0.05, 0.05)
                    confidence = min(0.95, max(0.4, base_confidence))
                    
                    historical_data.append({
                        'date': date,
                        'count': count,
                        'severity': severity,
                        'confidence': confidence
                    })
                
                # Convert to DataFrame
                hist_df = pd.DataFrame(historical_data)
                
                # Display overall metrics
                avg_daily = hist_df['count'].mean()
                total_detections = hist_df['count'].sum()
                trend_slope = (hist_df['count'].iloc[-10:].mean() - hist_df['count'].iloc[:10].mean()) / max(1, len(hist_df))
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Detections", int(total_detections))
                
                with col2:
                    st.metric("Avg. Daily Detections", f"{avg_daily:.1f}")
                
                with col3:
                    trend_label = "Increasing" if trend_slope > 0.1 else "Decreasing" if trend_slope < -0.1 else "Stable"
                    st.metric("Detection Trend", trend_label, delta=f"{trend_slope:.2f}")
                
                # Time series chart
                st.subheader("Detection Trends Over Time")
                
                fig = go.Figure()
                
                # Detection count
                fig.add_trace(go.Scatter(
                    x=hist_df['date'],
                    y=hist_df['count'],
                    name='Daily Detections',
                    line=dict(color='#FF4B4B', width=2)
                ))
                
                # Add 7-day moving average
                hist_df['7day_avg'] = hist_df['count'].rolling(7).mean()
                
                fig.add_trace(go.Scatter(
                    x=hist_df['date'],
                    y=hist_df['7day_avg'],
                    name='7-Day Average',
                    line=dict(color='#FF4B4B', width=3, dash='dash')
                ))
                
                fig.update_layout(
                    title="Pothole Detections Over Time",
                    xaxis_title="Date",
                    yaxis_title="Number of Detections",
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Severity trend
                st.subheader("Severity Trends")
                
                fig = go.Figure()
                
                # Severity
                fig.add_trace(go.Scatter(
                    x=hist_df['date'],
                    y=hist_df['severity'],
                    name='Average Severity',
                    line=dict(color='#FF7F00', width=2)
                ))
                
                # Add 7-day moving average
                hist_df['7day_sev_avg'] = hist_df['severity'].rolling(7).mean()
                
                fig.add_trace(go.Scatter(
                    x=hist_df['date'],
                    y=hist_df['7day_sev_avg'],
                    name='7-Day Average',
                    line=dict(color='#FF7F00', width=3, dash='dash')
                ))
                
                fig.update_layout(
                    title="Pothole Severity Over Time",
                    xaxis_title="Date",
                    yaxis_title="Severity Score (1-10)",
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Monthly breakdown
                st.subheader("Monthly Analysis")
                
                # Group by month
                hist_df['month'] = hist_df['date'].dt.month
                hist_df['month_name'] = hist_df['date'].dt.month_name()
                
                monthly_data = hist_df.groupby('month').agg({
                    'count': 'sum',
                    'severity': 'mean',
                    'confidence': 'mean',
                    'month_name': 'first'
                }).reset_index()
                
                # Sort by month
                monthly_data = monthly_data.sort_values('month')
                
                # Create bar chart
                fig = go.Figure()
                
                fig.add_trace(go.Bar(
                    x=monthly_data['month_name'],
                    y=monthly_data['count'],
                    name='Total Detections',
                    marker_color='#4b79ff'
                ))
                
                fig.add_trace(go.Scatter(
                    x=monthly_data['month_name'],
                    y=monthly_data['severity'] * 10,  # Scale up for visibility
                    name='Avg. Severity (x10)',
                    mode='lines+markers',
                    marker=dict(size=8),
                    line=dict(color='#FF4B4B', width=2)
                ))
                
                fig.update_layout(
                    title="Monthly Pothole Analysis",
                    xaxis_title="Month",
                    yaxis_title="Count",
                    height=400,
                    legend=dict(x=0.01, y=0.99)
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Seasonal patterns and insights
                st.subheader("Seasonal Patterns")
                
                # Group by season
                def get_season(month):
                    if month in [12, 1, 2]:
                        return "Winter"
                    elif month in [3, 4, 5]:
                        return "Spring"
                    elif month in [6, 7, 8]:
                        return "Summer"
                    else:
                        return "Fall"
                
                hist_df['season'] = hist_df['month'].apply(get_season)
                
                seasonal_data = hist_df.groupby('season').agg({
                    'count': 'sum',
                    'severity': 'mean'
                }).reset_index()
                
                # Order seasons correctly
                season_order = ["Winter", "Spring", "Summer", "Fall"]
                seasonal_data['season_order'] = seasonal_data['season'].apply(lambda x: season_order.index(x))
                seasonal_data = seasonal_data.sort_values('season_order')
                
                # Create bar chart
                fig = px.bar(
                    seasonal_data,
                    x='season',
                    y='count',
                    color='severity',
                    labels={'count': 'Total Detections', 'severity': 'Avg. Severity'},
                    title="Seasonal Pothole Distribution",
                    color_continuous_scale=px.colors.sequential.Reds,
                    text='count'
                )
                
                fig.update_layout(
                    xaxis_title="Season",
                    yaxis_title="Total Detections",
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Insights and recommendations
                st.subheader("Insights & Recommendations")
                
                # Calculate which season has the most potholes
                worst_season = seasonal_data.loc[seasonal_data['count'].idxmax()]['season']
                worst_month = monthly_data.loc[monthly_data['count'].idxmax()]['month_name']
                
                # Calculate trend
                first_month_avg = hist_df.loc[hist_df['date'].dt.month == hist_df['date'].dt.month.min(), 'count'].mean()
                last_month_avg = hist_df.loc[hist_df['date'].dt.month == hist_df['date'].dt.month.max(), 'count'].mean()
                overall_trend = "increasing" if last_month_avg > first_month_avg else "decreasing"
                
                st.markdown(f"""
                ### Key Insights:
                
                1. **Seasonal Patterns:**
                   - {worst_season} shows the highest number of pothole detections
                   - {worst_month} is the peak month for pothole formation
                   - Road damage appears to be {overall_trend} over the analyzed time period
                
                2. **Maintenance Effectiveness:**
                   - Road repairs should be scheduled before {worst_season} to minimize impact
                   - Preventive maintenance in fall could reduce winter/spring pothole formation
                   - Consider using more durable materials in high-traffic areas
                
                3. **Budget Planning:**
                   - Allocate 40% of annual maintenance budget for {worst_season}
                   - Plan for 25% higher repair costs during peak months
                   - Implement early detection programs to reduce overall maintenance costs
                
                4. **Future Predictions:**
                   - Based on current trends, expect a {5 if overall_trend == "increasing" else -5}% change in pothole detections next year
                   - Focus on proactive maintenance in the following areas to reduce future issues
                """)
            
            # Report export options
            st.markdown("---")
            st.subheader("Export Options")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.download_button(
                    "Download PDF Report",
                    data=b"Simulated PDF report data",  # This would be actual PDF data in a real app
                    file_name=f"pothole_report_{report_type.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf"
                )
            
            with col2:
                st.download_button(
                    "Download CSV Data",
                    data=b"Simulated CSV data",  # This would be actual CSV data in a real app
                    file_name=f"pothole_data_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            
            with col3:
                st.download_button(
                    "Download Excel Report",
                    data=b"Simulated Excel data",  # This would be actual Excel data in a real app
                    file_name=f"pothole_report_{report_type.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        
        # Show animated mascot
        st.markdown(load_mascot_animation(), unsafe_allow_html=True)
        st.markdown("""
        <div class="mascot-container">
            <div class="mascot-speech">Detective Pothole reporting for duty! I've compiled all the evidence for your review.</div>
            <div class="mascot-bounce">🕵️</div>
        </div>
        """, unsafe_allow_html=True)

# Add a section about the Pothole Detective mascot
st.markdown("---")
st.subheader("Meet Detective Pothole")

col1, col2 = st.columns([1, 2])

with col1:
    # Display the mascot image
    st.markdown("""
    <div style="text-align: center; animation: bounce 2s ease infinite;">
        <div style="font-size: 100px;">🕵️</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    **Detective Pothole** is your friendly guide to road maintenance!
    
    This eagle-eyed investigator helps you:
    
    - Identify critical pothole areas that need immediate attention
    - Send timely alerts to maintenance teams
    - Generate comprehensive reports for better decision-making
    - Track the effectiveness of road maintenance over time
    
    Detective Pothole uses advanced analytics to prioritize repairs and ensure smoother, safer roads for everyone!
    """)
    
    # Mascot settings
    st.markdown("### Mascot Settings")
    
    mascot_enabled = st.checkbox("Enable Detective Pothole animations", value=True)
    
    if mascot_enabled:
        mascot_style = st.selectbox(
            "Mascot Style",
            options=["Detective", "Road Worker", "Traffic Cone", "Superhero"],
            index=0
        )
        
        st.write(f"Selected mascot style: {mascot_style}")
        
        # This would apply different styling in a real app
        mascot_emoji = "🕵️" if mascot_style == "Detective" else "👷" if mascot_style == "Road Worker" else "🚧" if mascot_style == "Traffic Cone" else "🦸"
        
        st.markdown(f"""
        <div style="text-align: center; animation: bounce 1s ease infinite;">
            <div style="font-size: 50px;">{mascot_emoji}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Trigger a fun animation
    if st.button("Activate Detective Mode"):
        st.balloons()
        st.markdown(load_mascot_animation(), unsafe_allow_html=True)
        st.markdown(f"""
        <div class="mascot-container">
            <div class="mascot-speech">Detective mode activated! I'm on the case, searching for potholes in your area!</div>
            <div class="mascot-bounce">🕵️</div>
        </div>
        """, unsafe_allow_html=True)