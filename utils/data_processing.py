import os
import json
import glob
import pandas as pd
import numpy as np
from datetime import datetime
import base64
import cv2
from pathlib import Path
import io
from PIL import Image
import sys

# Import database utilities if possible
try:
    from utils.database import get_detection_statistics, get_all_detections, get_map_data
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False

def load_detection_results(results_dir="data/results"):
    """
    Load all detection results from the results directory.
    
    Args:
        results_dir: Directory containing JSON result files
        
    Returns:
        list of result dictionaries
    """
    results = []
    
    # Find all JSON files
    json_files = glob.glob(os.path.join(results_dir, "*.json"))
    
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                result_data = json.load(f)
                
            # Add file path to the data
            result_data['file_path'] = json_file
            
            # Find corresponding image
            base_name = os.path.splitext(os.path.basename(json_file))[0]
            image_path = os.path.join(results_dir, f"{base_name}.jpg")
            if os.path.exists(image_path):
                result_data['image_path'] = image_path
                
            results.append(result_data)
        except Exception as e:
            print(f"Error loading {json_file}: {e}")
    
    # Sort by timestamp (newest first)
    results.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
    
    return results

def get_image_preview(image_path, max_width=800):
    """
    Get a base64 encoded preview of an image.
    
    Args:
        image_path: Path to the image file
        max_width: Maximum width for the preview
        
    Returns:
        base64 encoded image string
    """
    try:
        image = cv2.imread(image_path)
        if image is None:
            return None
            
        # Resize while maintaining aspect ratio
        height, width = image.shape[:2]
        if width > max_width:
            scale = max_width / width
            new_width = int(width * scale)
            new_height = int(height * scale)
            image = cv2.resize(image, (new_width, new_height))
            
        # Convert to base64
        success, buffer = cv2.imencode('.jpg', image)
        encoded_image = base64.b64encode(buffer).decode('utf-8')
        return encoded_image
    except Exception as e:
        print(f"Error creating preview for {image_path}: {e}")
        return None

def calculate_statistics(results):
    """
    Calculate statistics from detection results.
    
    Args:
        results: List of result dictionaries
        
    Returns:
        Dictionary of statistics
    """
    if not results:
        return {
            "total_images": 0,
            "total_detections": 0,
            "avg_potholes_per_image": 0,
            "avg_confidence": 0,
            "detection_rate": 0,
            "dates": [],
            "daily_counts": []
        }
    
    total_images = len(results)
    total_detections = sum(len(r.get('detections', [])) for r in results)
    
    # Calculate average potholes per image
    avg_potholes = total_detections / total_images if total_images > 0 else 0
    
    # Calculate average confidence
    all_confidences = []
    for r in results:
        all_confidences.extend([d.get('confidence', 0) for d in r.get('detections', [])])
    avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0
    
    # Calculate detection rate (percentage of images with at least one detection)
    images_with_detections = sum(1 for r in results if len(r.get('detections', [])) > 0)
    detection_rate = (images_with_detections / total_images) * 100 if total_images > 0 else 0
    
    # Get daily counts for time series
    daily_data = {}
    for r in results:
        timestamp = r.get('timestamp', 0)
        date_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
        
        if date_str not in daily_data:
            daily_data[date_str] = 0
            
        daily_data[date_str] += len(r.get('detections', []))
    
    # Sort dates
    sorted_dates = sorted(daily_data.keys())
    daily_counts = [daily_data[date] for date in sorted_dates]
    
    return {
        "total_images": total_images,
        "total_detections": total_detections,
        "avg_potholes_per_image": avg_potholes,
        "avg_confidence": avg_confidence,
        "detection_rate": detection_rate,
        "dates": sorted_dates,
        "daily_counts": daily_counts
    }

def filter_results(results, min_confidence=0.0, date_range=None, min_detections=0):
    """
    Filter detection results based on criteria.
    
    Args:
        results: List of result dictionaries
        min_confidence: Minimum confidence threshold
        date_range: Tuple of (start_date, end_date) as datetime objects
        min_detections: Minimum number of detections required
        
    Returns:
        Filtered list of result dictionaries
    """
    filtered_results = []
    
    for result in results:
        # Filter by number of detections
        detections = result.get('detections', [])
        if len(detections) < min_detections:
            continue
            
        # Filter by confidence
        if min_confidence > 0:
            # Filter detections by confidence
            filtered_detections = [d for d in detections if d.get('confidence', 0) >= min_confidence]
            
            # Skip if no detections remain after filtering
            if not filtered_detections:
                continue
                
            # Update the detections list
            result = result.copy()
            result['detections'] = filtered_detections
            
        # Filter by date range
        if date_range:
            start_date, end_date = date_range
            timestamp = result.get('timestamp', 0)
            result_date = datetime.fromtimestamp(timestamp)
            
            if result_date < start_date or result_date > end_date:
                continue
                
        filtered_results.append(result)
    
    return filtered_results

def save_processed_image(image, filename, output_dir="data/processed"):
    """
    Save a processed image to the specified directory.
    
    Args:
        image: numpy array (BGR format)
        filename: desired filename
        output_dir: output directory
        
    Returns:
        Path to saved image
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Ensure filename has proper extension
    if not filename.lower().endswith(('.jpg', '.jpeg', '.png')):
        filename = f"{filename}.jpg"
        
    # Create complete path
    output_path = os.path.join(output_dir, filename)
    
    # Save the image
    cv2.imwrite(output_path, image)
    
    return output_path

def prepare_batch_results(batch_results):
    """
    Prepare batch processing results for display.
    
    Args:
        batch_results: List of (image_path, detections, metadata) tuples
        
    Returns:
        DataFrame with summarized results
    """
    results_data = []
    
    for image_path, detections, metadata in batch_results:
        # Get filename from path
        filename = os.path.basename(image_path)
        
        # Count detections
        detection_count = len(detections)
        
        # Calculate average confidence
        avg_confidence = 0
        if detection_count > 0:
            avg_confidence = sum(d.get('confidence', 0) for d in detections) / detection_count
            
        # Add to results
        results_data.append({
            'filename': filename,
            'detections': detection_count,
            'avg_confidence': avg_confidence,
            'image_width': metadata.get('image_width', 0),
            'image_height': metadata.get('image_height', 0),
            'inference_time': metadata.get('inference_time', 0)
        })
    
    # Create DataFrame
    if results_data:
        df = pd.DataFrame(results_data)
    else:
        df = pd.DataFrame(columns=[
            'filename', 'detections', 'avg_confidence', 
            'image_width', 'image_height', 'inference_time'
        ])
        
    return df
