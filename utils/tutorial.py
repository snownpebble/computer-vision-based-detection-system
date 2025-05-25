"""
Tutorial module for the Pothole Detection System.
Provides interactive onboarding steps for new users.
"""
import streamlit as st
import time
import os
from pathlib import Path

class TutorialManager:
    """
    Manages the onboarding tutorial for the Pothole Detection System.
    Provides step-by-step guidance for new users.
    """
    def __init__(self):
        # Initialize tutorial state if not already present
        if 'tutorial_state' not in st.session_state:
            st.session_state.tutorial_state = {
                'active': False,
                'current_step': 0,
                'completed': False,
                'steps_completed': set()
            }
        
        # Define tutorial steps
        self.steps = [
            {
                'title': 'Welcome to Pothole Detection System',
                'description': 'This tutorial will guide you through the main features of the application.',
                'action': 'Continue to start the tutorial or Skip to explore on your own.',
                'page': 'Home'
            },
            {
                'title': 'Upload & Detect',
                'description': 'Upload images to detect potholes using our advanced detection model.',
                'action': 'Try uploading an image to see pothole detection in action.',
                'page': 'Upload'
            },
            {
                'title': 'Gallery View',
                'description': 'View all your processed images with detection results.',
                'action': 'Browse through previously processed images.',
                'page': 'Gallery'
            },
            {
                'title': 'Analytics Dashboard',
                'description': 'Analyze pothole detection statistics and trends.',
                'action': 'Explore detection metrics and visualizations.',
                'page': 'Dashboard'
            },
            {
                'title': 'Map Visualization',
                'description': 'View geographical distribution of detected potholes.',
                'action': 'Explore pothole locations on the interactive map.',
                'page': 'Map'
            },
            {
                'title': 'Database Management',
                'description': 'Access and manage your detection records in the database.',
                'action': 'View detection records stored in the database.',
                'page': 'Database'
            },
            {
                'title': 'Batch Processing',
                'description': 'Process multiple images at once for efficient analysis.',
                'action': 'Try batch processing for multiple image analysis.',
                'page': 'Batch'
            },
            {
                'title': 'Video Processing',
                'description': 'Process video files or webcam feed to detect potholes in real-time.',
                'action': 'Try real-time video analysis for dynamic pothole detection.',
                'page': 'Video'
            },
            {
                'title': 'Alerts & Reporting',
                'description': 'Configure alerts for critical pothole areas and generate comprehensive reports.',
                'action': 'Set up alerts and explore report generation features with Detective Pothole.',
                'page': 'Alerts'
            },
            {
                'title': 'Road Repair Requests',
                'description': 'Submit and track repair requests for detected potholes with one click.',
                'action': 'Try the one-click repair request system to efficiently manage road repairs.',
                'page': 'Repairs'
            },
            {
                'title': 'User Manual',
                'description': 'Learn how to use the app and understand the ML model technology behind it.',
                'action': 'Explore the comprehensive user guide and technical documentation.',
                'page': 'Manual'
            },
            {
                'title': 'Tutorial Completed!',
                'description': 'You\'ve completed the tutorial and are ready to use the Pothole Detection System.',
                'action': 'Start using the application or restart the tutorial anytime from the Help menu.',
                'page': 'Home'
            }
        ]

    def get_current_step(self):
        """Get the current tutorial step."""
        if not self.is_active():
            # Return a default step with empty values to avoid None errors
            return {
                'title': '',
                'description': '',
                'action': '',
                'page': ''
            }
        
        current_step = st.session_state.tutorial_state['current_step']
        if current_step < len(self.steps):
            return self.steps[current_step]
        
        # Return the last step if we're out of bounds
        return self.steps[-1] if self.steps else {
            'title': '',
            'description': '',
            'action': '',
            'page': ''
        }

    def start_tutorial(self):
        """Start the onboarding tutorial."""
        st.session_state.tutorial_state['active'] = True
        st.session_state.tutorial_state['current_step'] = 0
        st.session_state.tutorial_state['completed'] = False
        st.session_state.tutorial_state['steps_completed'] = set()

    def next_step(self):
        """Advance to the next tutorial step."""
        if self.is_active():
            current_step = st.session_state.tutorial_state['current_step']
            # Mark current step as completed
            st.session_state.tutorial_state['steps_completed'].add(current_step)
            
            # Move to next step
            next_step = current_step + 1
            if next_step >= len(self.steps):
                self.complete_tutorial()
            else:
                st.session_state.tutorial_state['current_step'] = next_step

    def previous_step(self):
        """Go back to the previous tutorial step."""
        if self.is_active():
            current_step = st.session_state.tutorial_state['current_step']
            if current_step > 0:
                st.session_state.tutorial_state['current_step'] = current_step - 1

    def skip_tutorial(self):
        """Skip the tutorial."""
        st.session_state.tutorial_state['active'] = False
        st.session_state.tutorial_state['completed'] = True

    def complete_tutorial(self):
        """Mark the tutorial as completed."""
        st.session_state.tutorial_state['active'] = False
        st.session_state.tutorial_state['completed'] = True
        st.session_state.tutorial_state['current_step'] = len(self.steps) - 1

    def restart_tutorial(self):
        """Restart the tutorial from the beginning."""
        self.start_tutorial()

    def is_active(self):
        """Check if the tutorial is active."""
        return st.session_state.tutorial_state['active']

    def is_completed(self):
        """Check if the tutorial has been completed."""
        return st.session_state.tutorial_state['completed']
    
    def get_step_for_page(self, page_name):
        """Get the tutorial step for a specific page."""
        # Map common page names to step pages
        page_mapping = {
            'Upload & Detect': 'Upload',
            'Gallery': 'Gallery',
            'Dashboard': 'Dashboard',
            'Map': 'Map',
            'Database': 'Database',
            'Batch Processing': 'Batch',
            'Video Processing': 'Video',
            'Alerts & Reporting': 'Alerts',
            'Road Repair Requests': 'Repairs',
            'User Manual': 'Manual',
            'Code Viewer': 'Code Viewer',
        }
        
        # Try to get the page from the mapping
        normalized_page = page_mapping.get(page_name, page_name)
        
        for i, step in enumerate(self.steps):
            if step['page'].lower() == normalized_page.lower():
                return i
        return 0
    
    def navigate_to_step_page(self):
        """Navigate to the page associated with the current step."""
        current_step = self.get_current_step()
        if current_step:
            # This is handled by the main app, we just return the page name
            return current_step['page']
        return None
    
    def render_tutorial_ui(self, current_page=None):
        """
        Render the tutorial UI components.
        
        Args:
            current_page (str): The name of the current page
        """
        if not self.is_active():
            return
        
        current_step = self.get_current_step()
        if not current_step:
            return
        
        # Create a container for the tutorial
        with st.container():
            # Add some spacing
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Create a styled box for the tutorial with improved design
            st.markdown("""
            <style>
            @keyframes glow {
                0% { box-shadow: 0 0 5px rgba(75, 121, 255, 0.5); }
                50% { box-shadow: 0 0 15px rgba(75, 121, 255, 0.8); }
                100% { box-shadow: 0 0 5px rgba(75, 121, 255, 0.5); }
            }
            
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            .tutorial-box {
                background-color: #f0f7ff;
                border-left: 5px solid #4b79ff;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 20px;
                box-shadow: 0 3px 10px rgba(0,0,0,0.1);
                animation: glow 3s infinite, fadeIn 0.5s ease-out;
                transition: all 0.3s ease;
            }
            
            .tutorial-box:hover {
                background-color: #e6f0ff;
                transform: translateY(-2px);
            }
            
            .tutorial-title {
                font-size: 20px;
                font-weight: bold;
                color: #2b59df;
                margin-bottom: 10px;
                display: flex;
                align-items: center;
            }
            
            .tutorial-title-icon {
                margin-right: 10px;
                font-size: 24px;
            }
            
            .tutorial-description {
                font-size: 16px;
                margin: 12px 0;
                line-height: 1.5;
            }
            
            .tutorial-action {
                font-size: 16px;
                font-style: italic;
                color: #333;
                background-color: #e1eaff;
                padding: 10px;
                border-radius: 5px;
                margin: 10px 0;
                border-left: 3px solid #4b79ff;
            }
            
            .tutorial-step-indicator {
                font-size: 14px;
                color: #555;
                margin-top: 12px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .tutorial-progress-dots {
                display: flex;
                gap: 5px;
            }
            
            .dot {
                height: 8px;
                width: 8px;
                border-radius: 50%;
                background-color: #ccc;
            }
            
            .dot.active {
                background-color: #4b79ff;
            }
            
            .tutorial-navigation {
                display: flex;
                justify-content: space-between;
                margin-top: 15px;
            }
            
            .mascot-tip {
                background-color: #fff8e1;
                border-left: 3px solid #ffb300;
                padding: 10px;
                margin-top: 15px;
                border-radius: 5px;
                font-size: 14px;
                display: flex;
                align-items: center;
            }
            
            .mascot-icon {
                font-size: 20px;
                margin-right: 10px;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Generate progress dots
            progress_dots = ""
            for i in range(len(self.steps)-1):  # Exclude the final "completed" step
                if i == st.session_state.tutorial_state['current_step']:
                    progress_dots += '<div class="dot active"></div>'
                elif i in st.session_state.tutorial_state['steps_completed']:
                    progress_dots += '<div class="dot completed"></div>'
                else:
                    progress_dots += '<div class="dot"></div>'
            
            # Create the tutorial box with enhanced content
            st.markdown(f"""
            <div class="tutorial-box">
                <div class="tutorial-title">
                    <span class="tutorial-title-icon">🎓</span>
                    <span>{current_step['title']}</span>
                </div>
                <div class="tutorial-description">{current_step['description']}</div>
                <div class="tutorial-action">✨ {current_step['action']}</div>
                <div class="tutorial-step-indicator">
                    <span>Step {st.session_state.tutorial_state['current_step'] + 1} of {len(self.steps)-1}</span>
                    <div class="tutorial-progress-dots">
                        {progress_dots}
                    </div>
                </div>
                
                <div class="mascot-tip">
                    <span class="mascot-icon">🕵️</span>
                    <span>Detective Pothole's Tip: {self._get_step_tip(current_step['page'])}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Navigation buttons with better layout
            col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
            with col1:
                if st.session_state.tutorial_state['current_step'] > 0:
                    if st.button("⬅️ Previous", key="prev_tutorial_btn"):
                        self.previous_step()
                        st.rerun()
            
            with col2:
                if st.button("➡️ Next", key="next_tutorial_btn"):
                    self.next_step()
                    st.rerun()
            
            with col3:
                if st.button("⏩ Skip", key="skip_tutorial_btn"):
                    self.skip_tutorial()
                    st.rerun()
                    
            # If we're on the wrong page for this step, offer to navigate
            if current_page and current_step['page'].lower() != current_page.lower() and current_step['page'] != 'Home':
                with col4:
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
                    
                    if st.button(f"🔍 Go to {current_step['page']} Page", key="nav_tutorial_btn"):
                        # Direct navigation to the proper page
                        if current_step['page'] in page_map:
                            st.switch_page(page_map[current_step['page']])
                        st.rerun()
    
    def _get_step_tip(self, page_name):
        """Get a helpful tip for the current tutorial step."""
        tips = {
            'Home': "The home page gives you an overview of all available features. Click on the sidebar to navigate!",
            'Upload': "You can upload your own images or use our sample images to test the detection system.",
            'Gallery': "Filter and sort your processed images to quickly find what you're looking for.",
            'Dashboard': "Hover over charts to see detailed information about pothole detections.",
            'Map': "Zoom in and out to explore pothole locations in different areas.",
            'Database': "All your detection records are stored in the database for easy retrieval.",
            'Batch': "Process multiple images at once to save time when working with large datasets.",
            'Video': "Use the frame control to navigate through video detections frame by frame.",
            'Alerts': "Set up SMS alerts to be notified about critical pothole areas.",
            'Repairs': "Track the status of repair requests from submission to completion.",
            'Manual': "The user manual contains detailed information about all app features.",
            'Code Viewer': "Explore the source code to understand how the application works."
        }
        
        return tips.get(page_name, "Explore each feature thoroughly to get the most out of the application!")

    def create_sample_data(self):
        """Create sample data for the tutorial if needed."""
        # Check if we need to create sample data
        if not os.path.exists("data/sample_images"):
            os.makedirs("data/sample_images", exist_ok=True)
        
        # Copy sample images if needed
        sample_images_path = Path("data/sample_images")
        if not list(sample_images_path.glob("*.jpg")):
            # If no sample images exist, create a placeholder text file
            with open(sample_images_path / "PLACEHOLDER.txt", "w") as f:
                f.write("Please upload sample images for the tutorial.")


# Helper function to get tutorial manager instance
def get_tutorial_manager():
    """Get or create a tutorial manager instance."""
    if 'tutorial_manager' not in st.session_state:
        st.session_state.tutorial_manager = TutorialManager()
    return st.session_state.tutorial_manager