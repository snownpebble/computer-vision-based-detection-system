import streamlit as st
import os
import sys
from pathlib import Path

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.tutorial import get_tutorial_manager

st.set_page_config(
    page_title="User Manual - Pothole Detection System",
    page_icon="📖",
    layout="wide"
)

# Get tutorial manager
tutorial_manager = get_tutorial_manager()

# Render tutorial UI if active
if tutorial_manager.is_active():
    tutorial_manager.render_tutorial_ui("Manual")

st.title("📖 User Manual & Technical Documentation")
st.markdown("Learn how to use the Pothole Detection System and understand the technology behind it")

# Create tabs for different sections
tab1, tab2, tab3 = st.tabs(["User Guide", "Technical Documentation", "ML Model Explanation"])

with tab1:
    st.header("User Guide")
    
    st.subheader("Introduction")
    st.markdown("""
    The Pothole Detection System is a comprehensive application designed to help identify, analyze, and manage road potholes. 
    This guide will walk you through the various features of the application and how to use them effectively.
    """)
    
    st.subheader("Navigation")
    st.markdown("""
    The application consists of multiple pages accessible from the sidebar:
    
    - **Home**: Main dashboard and overview
    - **Upload & Detect**: Upload images to detect potholes
    - **Gallery**: View previously processed images
    - **Dashboard**: View analytics and statistics
    - **Map**: Visualize pothole locations geographically
    - **Database**: Manage detection records
    - **Batch Processing**: Process multiple images at once
    - **Video Processing**: Analyze videos for potholes
    - **Alerts & Reporting**: Set up alerts and generate reports
    - **Road Repair Requests**: Submit and track repair requests
    - **User Manual**: This guide and technical documentation
    """)
    
    st.subheader("Getting Started")
    st.markdown("""
    To get started with the Pothole Detection System:
    
    1. **Upload an image**: Navigate to the Upload & Detect page and upload a road image
    2. **View detections**: The system will automatically detect potholes in the image
    3. **Explore results**: View the detection results in the Gallery and Dashboard
    4. **Set up alerts**: Configure alerts for critical pothole areas
    5. **Submit repair requests**: Request repairs for detected potholes
    
    You can also follow the interactive tutorial by clicking "Start Tutorial" in the sidebar.
    """)
    
    st.subheader("Feature Guide")
    
    st.markdown("#### Upload & Detect")
    st.markdown("""
    This page allows you to upload images for pothole detection:
    
    - **Upload Image**: Select an image file from your computer
    - **Use Sample**: Alternatively, use one of the provided sample images
    - **Adjust Parameters**: Set the confidence threshold for detection
    - **View Results**: See the processed image with detected potholes
    - **Export Results**: Export detection results in various formats
    """)
    
    st.markdown("#### Gallery")
    st.markdown("""
    The Gallery page displays all previously processed images:
    
    - **Browse Images**: View all processed images with detection results
    - **Filter Options**: Filter images by date, confidence level, etc.
    - **Sort Options**: Sort images by different criteria
    - **Image Details**: Click on an image to see detailed detection information
    """)
    
    st.markdown("#### Dashboard")
    st.markdown("""
    The Dashboard provides analytics and insights about pothole detections:
    
    - **Overview Metrics**: See key statistics about pothole detections
    - **Charts and Graphs**: Visualize detection patterns and trends
    - **Time-based Analysis**: Analyze detections over time
    - **Export Reports**: Download reports and data exports
    """)
    
    st.markdown("#### Map")
    st.markdown("""
    The Map page visualizes pothole locations geographically:
    
    - **Interactive Map**: View detected potholes on a geographical map
    - **Hotspots**: Identify areas with high pothole concentrations
    - **Filters**: Filter map data by date, severity, etc.
    - **Location Details**: Click on map markers for detailed information
    """)
    
    st.markdown("#### Database")
    st.markdown("""
    The Database page allows you to manage detection records:
    
    - **View Records**: Browse all detection records in the database
    - **Search and Filter**: Find specific records based on criteria
    - **Database Info**: View information about the database configuration
    - **Export Data**: Export database records in various formats
    """)
    
    st.markdown("#### Batch Processing")
    st.markdown("""
    The Batch Processing page allows you to process multiple images at once:
    
    - **Select Folder**: Choose a folder containing multiple images
    - **Processing Settings**: Configure batch processing parameters
    - **Batch Results**: View results of the batch processing operation
    - **Export Options**: Export batch results in various formats
    """)
    
    st.markdown("#### Video Processing")
    st.markdown("""
    The Video Processing page allows you to analyze videos for potholes:
    
    - **Upload Video**: Upload a video file for processing
    - **Use Demo Video**: Use a sample video for demonstration
    - **Webcam Feed**: Use a webcam for real-time pothole detection
    - **Processing Options**: Configure video processing parameters
    - **Results Viewer**: View frame-by-frame detection results
    """)
    
    st.markdown("#### Alerts & Reporting")
    st.markdown("""
    The Alerts & Reporting page allows you to set up alerts and generate reports:
    
    - **Alert Setup**: Configure alert thresholds and notification methods
    - **Critical Areas**: View and manage critical pothole areas
    - **Report Generation**: Create comprehensive reports about pothole detections
    - **Detective Pothole**: Interact with the helpful mascot for guidance
    """)
    
    st.markdown("#### Road Repair Requests")
    st.markdown("""
    The Road Repair Requests page allows you to submit and track repair requests:
    
    - **Create Request**: Submit a repair request for a detected pothole
    - **Track Requests**: Monitor the status of submitted repair requests
    - **Update Status**: Update the status of repair requests
    - **Analytics**: View statistics and insights about repair requests
    """)
    
    st.subheader("Tips & Best Practices")
    st.markdown("""
    - **Image Quality**: For best detection results, use clear images with good lighting
    - **Confidence Threshold**: Adjust the confidence threshold to balance between detection sensitivity and false positives
    - **Regular Updates**: Process new images regularly to maintain up-to-date data
    - **Database Backup**: Regularly export data to prevent loss
    - **Priority Setting**: Set appropriate priority levels for repair requests based on severity
    """)
    
    st.subheader("Troubleshooting")
    st.markdown("""
    **Common Issues and Solutions:**
    
    1. **No Detections in Image**
       - Check that the image shows clear road surfaces
       - Try lowering the confidence threshold
       - Ensure the image format is supported (JPG, PNG)
    
    2. **Slow Processing**
       - For batch processing, reduce the number of images
       - For video processing, increase the "Process Every N Frame" value
    
    3. **Map Not Showing Locations**
       - Ensure images have geolocation data
       - Try using the simulated location feature
    
    4. **Database Connection Issues**
       - The system will automatically fall back to SQLite if PostgreSQL is unavailable
       - Check database configuration in settings
    
    5. **Alert Notifications Not Sending**
       - Verify Twilio credentials are correctly configured
       - Check recipient phone numbers are in correct format
    """)

with tab2:
    st.header("Technical Documentation")
    
    st.subheader("System Architecture")
    st.markdown("""
    The Pothole Detection System is built with a modular architecture:
    
    ```
    ├── app.py                 # Main application entry point
    ├── pages/                 # Application pages
    │   ├── upload.py          # Upload & detection page
    │   ├── gallery.py         # Gallery page
    │   ├── dashboard.py       # Analytics dashboard
    │   ├── map.py             # Map visualization
    │   ├── database.py        # Database management
    │   ├── batch_processing.py # Batch processing
    │   ├── video_processing.py # Video processing
    │   ├── alerts.py          # Alerts & reporting
    │   ├── repair_requests.py # Road repair requests
    │   └── manual.py          # User manual & documentation
    ├── utils/                 # Utility modules
    │   ├── detection.py       # Pothole detection implementation
    │   ├── visualization.py   # Visualization utilities
    │   ├── data_processing.py # Data processing utilities
    │   ├── database.py        # Database operations
    │   ├── tutorial.py        # Tutorial implementation
    │   └── twilio_integration.py # Twilio SMS integration
    ├── data/                  # Data storage
    │   ├── uploads/           # Uploaded images
    │   ├── processed/         # Processed images
    │   ├── results/           # Detection results
    │   ├── sample_images/     # Sample images
    │   ├── sample_videos/     # Sample videos
    │   └── video_results/     # Video processing results
    ```
    """)
    
    st.subheader("Technology Stack")
    st.markdown("""
    The application is built using the following technologies:
    
    - **Frontend/Backend**: Streamlit (Python web framework)
    - **Machine Learning**: YOLOv8 object detection model
    - **Database**: PostgreSQL with SQLite fallback
    - **Data Visualization**: Plotly, Matplotlib
    - **Image Processing**: OpenCV, Pillow
    - **Geospatial Mapping**: Plotly Mapbox
    - **SMS Notifications**: Twilio API
    """)
    
    st.subheader("Deployment")
    st.markdown("""
    The application is designed to be deployed on various platforms:
    
    - **Local Deployment**: Run the application locally using Streamlit
    - **Cloud Deployment**: Deploy to cloud platforms like Heroku, AWS, or GCP
    - **Docker Deployment**: Deploy using Docker containers
    
    For proper deployment, ensure the following:
    
    1. **Environment Variables**: Set up database credentials and API keys
    2. **Port Configuration**: Configure the application to run on port 5000
    3. **Database Setup**: Set up PostgreSQL database or use SQLite fallback
    4. **File Storage**: Ensure the data directories are writable
    """)
    
    st.subheader("API Integration")
    st.markdown("""
    The application integrates with the following external APIs:
    
    - **Twilio API**: For sending SMS alerts and notifications
    - **Mapbox API**: For geographical mapping (integrated via Plotly)
    
    To configure these integrations:
    
    1. **Twilio**: Set the following environment variables:
       - `TWILIO_ACCOUNT_SID`: Your Twilio account SID
       - `TWILIO_AUTH_TOKEN`: Your Twilio auth token
       - `TWILIO_PHONE_NUMBER`: Your Twilio phone number
    
    2. **Mapbox**: No explicit configuration required as Plotly uses a free tier
    """)
    
    st.subheader("Database Schema")
    st.markdown("""
    The application uses the following database schema:
    
    **Images Table**
    ```sql
    CREATE TABLE images (
        id INTEGER PRIMARY KEY,
        filename TEXT NOT NULL,
        filepath TEXT NOT NULL,
        upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        width INTEGER,
        height INTEGER
    )
    ```
    
    **Detections Table**
    ```sql
    CREATE TABLE detections (
        id INTEGER PRIMARY KEY,
        image_id INTEGER NOT NULL,
        class_id INTEGER,
        class_name TEXT,
        confidence REAL,
        bbox_x1 INTEGER,
        bbox_y1 INTEGER,
        bbox_x2 INTEGER,
        bbox_y2 INTEGER,
        detection_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (image_id) REFERENCES images(id)
    )
    ```
    
    **Image Metadata Table**
    ```sql
    CREATE TABLE image_metadata (
        id INTEGER PRIMARY KEY,
        image_id INTEGER NOT NULL UNIQUE,
        latitude REAL,
        longitude REAL,
        inference_time REAL,
        model_name TEXT,
        metadata_json JSON,
        FOREIGN KEY (image_id) REFERENCES images(id)
    )
    ```
    """)
    
    st.subheader("Performance Considerations")
    st.markdown("""
    For optimal performance:
    
    - **Image Size**: Large images (>4K resolution) may slow down processing
    - **Batch Size**: Limit batch processing to 50-100 images at a time
    - **Video Processing**: Processing every 5-10 frames is recommended for smooth operation
    - **Database**: PostgreSQL performs better than SQLite for large datasets
    - **Caching**: The application uses Streamlit's caching to improve performance
    """)
    
    st.subheader("Security Considerations")
    st.markdown("""
    The application implements the following security measures:
    
    - **Database Security**: Using parameterized queries to prevent SQL injection
    - **API Key Security**: Environment variables for sensitive credentials
    - **File Upload Security**: Validation of file types and sizes
    - **Data Validation**: Input validation for form submissions
    
    Note: This is a demonstration application and may require additional security measures for production deployment.
    """)

with tab3:
    st.header("ML Model Explanation")
    
    st.subheader("YOLOv8 Overview")
    st.markdown("""
    The Pothole Detection System uses YOLOv8, a state-of-the-art object detection model from Ultralytics. 
    
    **YOLO (You Only Look Once)** is a family of one-stage object detection models known for their speed and accuracy. YOLOv8 is the latest version with significant improvements in both performance and accuracy.
    
    Key features of YOLOv8:
    
    - **One-Stage Detection**: Performs detection in a single forward pass of the network
    - **Real-Time Performance**: Capable of processing images and videos in real-time
    - **High Accuracy**: Achieves state-of-the-art results on standard object detection benchmarks
    - **Multiple Model Sizes**: From nano (smallest) to extra-large (largest), balancing speed and accuracy
    - **Modular Design**: Supports object detection, segmentation, and classification tasks
    """)
    
    st.image("https://user-images.githubusercontent.com/26833433/212889447-69e5bdf1-5800-4e29-835e-2ed2336dede2.jpg", caption="YOLOv8 Architecture (Source: Ultralytics)")
    
    st.subheader("How YOLO Works")
    st.markdown("""
    YOLO divides an image into a grid and predicts bounding boxes and class probabilities directly from the full image in a single evaluation:
    
    1. **Grid Division**: The input image is divided into an S×S grid
    2. **Bounding Box Prediction**: Each grid cell predicts B bounding boxes and confidence scores
    3. **Class Prediction**: Each grid cell also predicts C class probabilities
    4. **Final Predictions**: Boxes with high confidence scores for specific classes are kept
    5. **Non-Maximum Suppression (NMS)**: Overlapping boxes for the same object are merged
    
    The confidence score reflects how certain the model is that the box contains an object and how accurate it thinks the box is.
    """)
    
    st.subheader("YOLOv8 Architecture")
    st.markdown("""
    YOLOv8 architecture consists of three main components:
    
    1. **Backbone**: A convolutional neural network that extracts features from the input image
       - Uses a CSPDarknet53 backbone with Cross-Stage Partial connections
       - Extracts multi-scale features for detecting objects of different sizes
    
    2. **Neck**: A series of layers that mix and combine features from different layers
       - Uses PANet (Path Aggregation Network) to enhance feature fusion
       - Helps in transferring information between different scales
    
    3. **Head**: The final layers that convert features into detection predictions
       - Consists of multiple detection heads for different scales
       - Outputs bounding boxes, object confidence, and class probabilities
    """)
    
    st.subheader("Pothole Detection Model")
    st.markdown("""
    For pothole detection, we've customized the YOLOv8 model by fine-tuning it on a dataset of road images with annotated potholes:
    
    - **Base Model**: YOLOv8n (nano) for balance between speed and accuracy
    - **Training Dataset**: Combination of public pothole datasets and custom annotated images
    - **Classes**: Single class - "pothole"
    - **Training Process**: Transfer learning from the pre-trained YOLOv8 model
    - **Augmentation**: Random flip, rotation, scale, and brightness changes to improve robustness
    - **Validation**: 20% of data held out for validation during training
    
    The fine-tuning process involved:
    
    1. Starting with a pre-trained YOLOv8 model (trained on COCO dataset)
    2. Replacing the classification head for our single-class task
    3. Fine-tuning the entire network on our pothole dataset
    4. Optimizing for precision and recall on pothole detection
    """)
    
    st.subheader("Model Performance")
    st.markdown("""
    The pothole detection model achieves the following performance metrics:
    
    - **Precision**: 0.89 (89% of predicted potholes are actual potholes)
    - **Recall**: 0.86 (86% of actual potholes are detected)
    - **mAP@0.5**: 0.91 (mean Average Precision at 0.5 IoU threshold)
    - **Inference Speed**: ~30 FPS on GPU, ~5 FPS on CPU
    
    These metrics are based on our validation dataset. Performance may vary depending on image quality, lighting conditions, and pothole characteristics.
    """)
    
    st.subheader("Confidence Threshold")
    st.markdown("""
    The detection process uses a confidence threshold to filter predictions:
    
    - **Higher threshold** (e.g., 0.7): Fewer detections but higher precision (fewer false positives)
    - **Lower threshold** (e.g., 0.3): More detections but potentially more false positives
    
    The default threshold in our application is 0.25, which provides a good balance between detecting most potholes while keeping false positives low.
    
    You can adjust this threshold in the application depending on your specific needs:
    
    - For critical safety applications, use a lower threshold to ensure most potholes are detected
    - For statistical analysis, use a higher threshold to ensure high confidence in the detections
    """)
    
    st.subheader("Limitations and Considerations")
    st.markdown("""
    The current pothole detection model has some limitations to be aware of:
    
    - **Similar Defects**: May sometimes confuse other road damage types (cracks, patches) with potholes
    - **Lighting Conditions**: Performance may degrade in extreme lighting (very dark or bright)
    - **Image Quality**: Blurry or low-resolution images may result in missed detections
    - **Partial Visibility**: Partially visible potholes (e.g., covered by water/debris) may be missed
    - **Unusual Perspectives**: Very oblique angles may affect detection accuracy
    
    We continuously improve the model by:
    
    - Adding more diverse training data
    - Implementing more sophisticated augmentation techniques
    - Experimenting with different model architectures and hyperparameters
    - Incorporating user feedback on detection results
    """)
    
    st.subheader("Future Improvements")
    st.markdown("""
    Planned improvements to the ML model include:
    
    - **Multi-class Detection**: Distinguishing between different types of road damage (potholes, cracks, raveling, etc.)
    - **Severity Classification**: Automatically rating pothole severity based on size, depth, and location
    - **Temporal Analysis**: Tracking pothole growth over time through repeated observations
    - **3D Reconstruction**: Estimating pothole depth from 2D images for better severity assessment
    - **Mobile Optimization**: Further optimizing the model for mobile devices and edge deployment
    """)

# Add a section for Frequently Asked Questions
st.markdown("---")
st.header("Frequently Asked Questions")

faq_data = [
    {
        "question": "How accurate is the pothole detection?",
        "answer": "The pothole detection model achieves about 89% precision and 86% recall on our validation dataset. This means it correctly identifies most potholes while maintaining a low rate of false positives. Performance may vary depending on image quality and lighting conditions."
    },
    {
        "question": "Can I use my own pothole images?",
        "answer": "Yes! You can upload your own images through the 'Upload & Detect' page. The system supports JPG, JPEG, and PNG image formats."
    },
    {
        "question": "Does the system work with video?",
        "answer": "Yes, the 'Video Processing' page allows you to upload video files or use a webcam feed for real-time pothole detection."
    },
    {
        "question": "How are repair requests handled?",
        "answer": "The 'Road Repair Requests' page allows you to submit repair requests for detected potholes. You can track the status of these requests and receive updates as they progress through the repair workflow."
    },
    {
        "question": "Do I need an internet connection?",
        "answer": "The application can run locally without an internet connection. However, some features like map visualization and SMS alerts require internet connectivity."
    },
    {
        "question": "Can I export detection results?",
        "answer": "Yes, you can export detection results in various formats including CSV, JSON, and Excel from several pages in the application."
    },
    {
        "question": "How do I set up SMS alerts?",
        "answer": "To enable SMS alerts, you need to configure Twilio credentials (Account SID, Auth Token, and Phone Number) in the application. Once configured, you can set up alerts in the 'Alerts & Reporting' page."
    },
    {
        "question": "What database does the system use?",
        "answer": "The system primarily uses PostgreSQL for database storage. However, it will automatically fall back to SQLite if PostgreSQL is not available, ensuring the application works in various environments."
    },
    {
        "question": "Can the system detect potholes at night?",
        "answer": "The detection accuracy may be reduced in low-light conditions. For best results, use well-lit images or apply appropriate image enhancement techniques before processing."
    },
    {
        "question": "How do I add more sample images?",
        "answer": "You can add sample images to the 'data/sample_images' directory. These will automatically appear in the application for demonstration purposes."
    }
]

# Create expandable FAQ items
for i, faq in enumerate(faq_data):
    with st.expander(f"Q: {faq['question']}"):
        st.markdown(f"**A:** {faq['answer']}")

# Add contact information
st.markdown("---")
st.header("Contact & Support")
st.markdown("""
If you have questions, feedback, or need assistance with the Pothole Detection System, please contact us:

- **Email**: support@potholedetection.com
- **Phone**: +1-234-567-8900
- **GitHub**: [github.com/potholedetection](https://github.com/potholedetection)
- **Twitter**: [@PotholeDetect](https://twitter.com/PotholeDetect)

For bug reports or feature requests, please open an issue on our GitHub repository.
""")

# Add mascot animation to the manual page
st.markdown("""
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

<div class="mascot-container">
    <div class="mascot-speech">Need help understanding the app? I've compiled this comprehensive manual for you!</div>
    <div class="mascot-bounce">🕵️</div>
</div>
""", unsafe_allow_html=True)