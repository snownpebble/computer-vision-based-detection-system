import streamlit as st
import os
import sys
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.database import get_all_detections, get_detection_statistics, create_tables
from utils.visualization import create_detection_summary_chart
from utils.tutorial import get_tutorial_manager

st.set_page_config(
    page_title="Database - Pothole Detection System",
    page_icon="🗄️",
    layout="wide"
)

# Get tutorial manager
tutorial_manager = get_tutorial_manager()

# Render tutorial UI if active
if tutorial_manager.is_active():
    tutorial_manager.render_tutorial_ui("Database")

st.title("🗄️ Database Management")
st.markdown("View and manage detection records stored in the database.")

# Initialize the database if needed
create_tables()

# Create tabs for different views
tab1, tab2 = st.tabs(["Records", "Statistics"])

with tab1:
    st.subheader("Detection Records")
    
    # Get all detections from the database
    try:
        detections = get_all_detections()
        if detections:
            # Convert to DataFrame for display
            df_detections = pd.DataFrame([
                {
                    'ID': d['id'],
                    'Image': d['filename'],
                    'Class': d['class_name'],
                    'Confidence': f"{d['confidence']:.2f}",
                    'Position': f"({d['bbox'][0]}, {d['bbox'][1]}, {d['bbox'][2]}, {d['bbox'][3]})",
                    'Date': d['detection_date'].strftime('%Y-%m-%d %H:%M:%S') if hasattr(d['detection_date'], 'strftime') else str(d['detection_date'])
                }
                for d in detections
            ])
            
            # Display the DataFrame
            st.dataframe(df_detections, use_container_width=True)
            
            # Show summary
            st.info(f"Total records: {len(detections)}")
            
            # Add filtering options in the sidebar
            st.sidebar.subheader("Filter Options")
            
            # Add a refresh button
            if st.sidebar.button("Refresh Data"):
                st.rerun()

            # Tutorial completion for this step
            if tutorial_manager.is_active() and tutorial_manager.get_current_step()['page'] == 'Database':
                st.success("✅ Great job! You've learned about the Database management features.")
                # Add a button to continue the tutorial
                if st.button("Continue to Next Tutorial Step"):
                    tutorial_manager.next_step()
                    # If next step is Batch, navigate there
                    next_step = tutorial_manager.get_current_step()
                    if next_step and next_step['page'] == 'Batch':
                        st.switch_page("pages/batch_processing.py")
                    else:
                        st.rerun()
        else:
            st.info("No detection records found in the database. Process some images to add records.")
            
            # Tutorial hint for empty database
            if tutorial_manager.is_active() and tutorial_manager.get_current_step()['page'] == 'Database':
                st.success("✅ This is the Database page where you can manage detection records.")
                st.info("Since you don't have any detection records yet, let's continue with the tutorial.")
                
                if st.button("Continue to Next Tutorial Step"):
                    tutorial_manager.next_step()
                    # If next step is Batch, navigate there
                    next_step = tutorial_manager.get_current_step()
                    if next_step and next_step['page'] == 'Batch':
                        st.switch_page("pages/batch_processing.py")
                    else:
                        st.rerun()
    except Exception as e:
        st.error(f"Error retrieving database records: {e}")
        st.info("Using SQLite fallback database. Detection records will be stored locally.")

with tab2:
    st.subheader("Detection Statistics")
    
    try:
        # Get statistics from the database
        stats = get_detection_statistics()
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Images", stats["total_images"])
        
        with col2:
            st.metric("Total Detections", stats["total_detections"])
        
        with col3:
            st.metric("Avg. Potholes per Image", f"{stats['avg_potholes_per_image']:.2f}")
        
        with col4:
            st.metric("Avg. Confidence", f"{stats['avg_confidence']:.2f}")
        
        # Detection rate
        st.metric("Detection Rate", f"{stats['detection_rate']:.1f}%")
        
        # Time series chart
        if stats["dates"] and stats["daily_counts"]:
            st.subheader("Detections Over Time")
            
            # Create DataFrame for plotting
            df_time = pd.DataFrame({
                'Date': stats["dates"],
                'Detections': stats["daily_counts"]
            })
            
            # Create time series chart
            fig = px.bar(
                df_time,
                x='Date',
                y='Detections',
                title='Pothole Detections Over Time',
                labels={'Detections': 'Number of Detections'},
                color_discrete_sequence=['#FF4B4B']
            )
            
            fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Number of Detections",
                height=400,
                margin=dict(l=40, r=40, t=40, b=40)
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Not enough data to display time series charts.")
        
    except Exception as e:
        st.error(f"Error retrieving database statistics: {e}")
        st.info("Using SQLite fallback database. Process some images to generate statistics.")

# Information about database storage
st.markdown("---")
st.subheader("Database Information")

try:
    # Determine which database we're using
    from utils.database import engine
    db_type = engine.url.drivername
    
    if 'sqlite' in db_type:
        st.info("Using SQLite database (local storage)")
        st.markdown("""
        - Data is stored locally in `data/pothole_detection.db`
        - All detection results are saved in this database
        - Statistics are calculated from the local database
        """)
    else:
        st.success("Using PostgreSQL database (cloud storage)")
        st.markdown("""
        - Data is stored in a PostgreSQL database
        - All detection results are saved in the cloud
        - Statistics are calculated from the cloud database
        """)
        
except Exception as e:
    st.warning(f"Could not determine database type: {e}")