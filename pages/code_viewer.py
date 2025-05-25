import streamlit as st
import os
import sys
from pathlib import Path

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.tutorial import get_tutorial_manager

st.set_page_config(
    page_title="Code Viewer - Pothole Detection System",
    page_icon="💻",
    layout="wide"
)

# Get tutorial manager
tutorial_manager = get_tutorial_manager()

# Render tutorial UI if active
if tutorial_manager.is_active():
    tutorial_manager.render_tutorial_ui("Code Viewer")

st.title("💻 Complete App Code")
st.markdown("Explore the complete source code of the Pothole Detection System")

def get_all_python_files():
    """Get all Python files in the project."""
    python_files = []
    for root, dirs, files in os.walk('.'):
        # Skip hidden directories
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for file in files:
            if file.endswith('.py'):
                full_path = os.path.join(root, file)
                # Normalize path for display
                normalized_path = os.path.normpath(full_path)
                python_files.append(normalized_path)
    return sorted(python_files)

def get_file_content(file_path):
    """Get the content of a file."""
    with open(file_path, 'r') as file:
        return file.read()

# Get all Python files
python_files = get_all_python_files()

# Create a file tree in the sidebar
st.sidebar.header("File Explorer")
selected_file = st.sidebar.selectbox("Select a file to view", python_files)

# Display the selected file
if selected_file:
    st.header(f"File: {selected_file}")
    file_content = get_file_content(selected_file)
    
    # File info
    file_stats = os.stat(selected_file)
    file_size = file_stats.st_size / 1024  # Convert to KB
    file_modified = os.path.getmtime(selected_file)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("File Size", f"{file_size:.2f} KB")
    col2.metric("Lines of Code", file_content.count('\n') + 1)
    col3.metric("Last Modified", f"{os.path.getmtime(selected_file)}")
    
    # Show file content
    st.code(file_content, language="python")

# Directory structure viewer
st.sidebar.header("Directory Structure")
show_structure = st.sidebar.checkbox("Show Directory Structure")

if show_structure:
    st.header("Project Directory Structure")
    
    def get_directory_structure():
        """Get the directory structure of the project."""
        structure = []
        for root, dirs, files in os.walk('.'):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            level = root.count(os.sep)
            indent = ' ' * 4 * level
            structure.append(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 4 * (level + 1)
            for file in sorted(files):
                if file.endswith('.py'):
                    structure.append(f"{subindent}{file}")
        return structure
    
    directory_structure = get_directory_structure()
    st.code('\n'.join(directory_structure), language="plaintext")

# Code statistics
st.sidebar.header("Code Statistics")
show_statistics = st.sidebar.checkbox("Show Code Statistics")

if show_statistics:
    st.header("Code Statistics")
    
    # Calculate statistics
    total_files = len(python_files)
    total_lines = 0
    file_sizes = []
    file_lines = []
    
    for file_path in python_files:
        file_content = get_file_content(file_path)
        lines = file_content.count('\n') + 1
        total_lines += lines
        file_size = os.stat(file_path).st_size / 1024  # KB
        file_sizes.append((file_path, file_size))
        file_lines.append((file_path, lines))
    
    # Sort by size and lines
    file_sizes.sort(key=lambda x: x[1], reverse=True)
    file_lines.sort(key=lambda x: x[1], reverse=True)
    
    # Display statistics
    col1, col2 = st.columns(2)
    col1.metric("Total Python Files", total_files)
    col2.metric("Total Lines of Code", total_lines)
    
    # Top files by size
    st.subheader("Top 5 Files by Size")
    size_data = {
        "File": [os.path.basename(f[0]) for f in file_sizes[:5]],
        "Size (KB)": [f"{f[1]:.2f}" for f in file_sizes[:5]]
    }
    st.dataframe(size_data)
    
    # Top files by lines
    st.subheader("Top 5 Files by Lines of Code")
    lines_data = {
        "File": [os.path.basename(f[0]) for f in file_lines[:5]],
        "Lines": [f[1] for f in file_lines[:5]]
    }
    st.dataframe(lines_data)

# Download all code
st.sidebar.header("Download Options")

if st.sidebar.button("Generate Code Zip"):
    import io
    import zipfile
    
    # Create a zip file in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for file_path in python_files:
            zip_file.write(file_path)
    
    # Download button
    st.sidebar.download_button(
        label="Download Code as ZIP",
        data=zip_buffer.getvalue(),
        file_name="pothole_detection_app_code.zip",
        mime="application/zip"
    )
    
    st.sidebar.success("Zip file generated successfully! Click the download button above.")

# Mascot animation with speech bubble
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
    <div class="mascot-speech">Want to see how I work? Check out my code!</div>
    <div class="mascot-bounce">🕵️</div>
</div>
""", unsafe_allow_html=True)