import cv2
import numpy as np
import os
import time
import json
from pathlib import Path
import pandas as pd
import io
import base64
from PIL import Image
import random
from utils.database import save_detection_to_db

class PotholeDetector:
    def __init__(self, model_path="yolov8n.pt"):
        """
        Initialize the pothole detector with a YOLOv8 model.
        This is a simulated version for demonstration purposes.
        
        Args:
            model_path (str): Path to the YOLOv8 model weights (not used in this simulation)
        """
        # Class names
        self.class_names = {0: 'pothole'}
        print(f"Initialized PotholeDetector (Simulation Mode)")
        
        # Create data directories if they don't exist
        os.makedirs("data/uploads", exist_ok=True)
        os.makedirs("data/processed", exist_ok=True)
        os.makedirs("data/results", exist_ok=True)
        
    def detect_potholes(self, image_path, conf_threshold=0.25):
        """
        Detect potholes in the given image (simulated).
        
        Args:
            image_path (str): Path to the input image
            conf_threshold (float): Confidence threshold for detection
            
        Returns:
            tuple: (processed_image, detections, metadata)
        """
        try:
            # Load image
            if isinstance(image_path, str):
                image = cv2.imread(image_path)
                image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            else:
                # For in-memory uploads
                img_array = np.array(Image.open(image_path))
                image_rgb = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                image = image_rgb

            # Get image dimensions
            height, width = image_rgb.shape[:2]
            
            # Simulate inference time
            start_time = time.time()
            time.sleep(0.5)  # Simulate detection delay
            inference_time = time.time() - start_time
            
            # Generate random detections for demonstration
            detections = []
            num_detections = random.randint(0, 4)  # Random number of "potholes"
            
            for i in range(num_detections):
                # Create random bounding box
                box_w = random.randint(width // 10, width // 3)
                box_h = random.randint(height // 10, height // 3)
                x1 = random.randint(0, width - box_w)
                y1 = random.randint(0, height - box_h)
                x2 = x1 + box_w
                y2 = y1 + box_h
                
                # Random confidence score higher than threshold
                conf = random.uniform(max(0.3, conf_threshold), 0.95)
                
                detection = {
                    'bbox': [int(x1), int(y1), int(x2), int(y2)],
                    'confidence': float(conf),
                    'class_id': 0,
                    'class_name': 'pothole'
                }
                detections.append(detection)
            
            # Create metadata
            metadata = {
                'image_width': width,
                'image_height': height,
                'inference_time': inference_time,
                'detection_count': len(detections),
                'model': "YOLOv8 (Simulation)",
                'timestamp': time.time()
            }
            
            # Add random geo coordinates for map demonstration
            if random.random() > 0.3:  # 70% chance to have geo data
                metadata['latitude'] = random.uniform(40.6, 40.8)  # NYC area
                metadata['longitude'] = random.uniform(-74.1, -73.9)
            
            return image_rgb, detections, metadata
            
        except Exception as e:
            print(f"Error in detection: {e}")
            return None, [], {'error': str(e)}
    
    def save_results(self, image, detections, metadata, original_filename, output_dir="data/results"):
        """
        Save detection results (image with bounding boxes and detection data).
        
        Args:
            image (np.ndarray): The processed image
            detections (list): List of detection dictionaries
            metadata (dict): Detection metadata
            original_filename (str): Original image filename
            output_dir (str): Directory to save results
            
        Returns:
            tuple: (image_path, json_path)
        """
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filenames
        base_name = os.path.splitext(os.path.basename(original_filename))[0]
        timestamp = int(time.time())
        image_filename = f"{base_name}_{timestamp}.jpg"
        json_filename = f"{base_name}_{timestamp}.json"
        
        # Save the image
        image_path = os.path.join(output_dir, image_filename)
        cv2.imwrite(image_path, cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
        
        # Save detection results as JSON
        result_data = {
            'filename': original_filename,
            'timestamp': timestamp,
            'detections': detections,
            'metadata': metadata
        }
        
        json_path = os.path.join(output_dir, json_filename)
        with open(json_path, 'w') as f:
            json.dump(result_data, f, indent=4)
        
        # Save to database (non-blocking)
        try:
            save_detection_to_db(image_path, detections, metadata)
        except Exception as e:
            print(f"Warning: Could not save to database: {e}")
        
        return image_path, json_path

    def export_results(self, detections, metadata, format_type="csv"):
        """
        Export detection results in various formats.
        
        Args:
            detections (list): List of detection dictionaries
            metadata (dict): Detection metadata
            format_type (str): Export format ('csv', 'json', 'txt')
            
        Returns:
            bytes: The exported data as bytes
        """
        # Create a DataFrame from detections
        if not detections:
            df = pd.DataFrame({
                'bbox_x1': [], 'bbox_y1': [], 'bbox_x2': [], 'bbox_y2': [],
                'confidence': [], 'class_id': [], 'class_name': []
            })
        else:
            rows = []
            for det in detections:
                row = {
                    'bbox_x1': det['bbox'][0],
                    'bbox_y1': det['bbox'][1],
                    'bbox_x2': det['bbox'][2],
                    'bbox_y2': det['bbox'][3],
                    'confidence': det['confidence'],
                    'class_id': det['class_id'],
                    'class_name': det['class_name']
                }
                rows.append(row)
            df = pd.DataFrame(rows)
        
        # Export based on format
        buffer = io.BytesIO()
        
        if format_type == "csv":
            df.to_csv(buffer, index=False)
            mime_type = "text/csv"
            file_ext = "csv"
        elif format_type == "json":
            result = {
                'detections': detections,
                'metadata': metadata
            }
            json_str = json.dumps(result, indent=4)
            buffer.write(json_str.encode('utf-8'))
            mime_type = "application/json"
            file_ext = "json"
        elif format_type == "txt":
            for i, det in enumerate(detections):
                buffer.write(f"Detection {i+1}: {det['class_name']} (Conf: {det['confidence']:.2f}) at {det['bbox']}\n".encode())
            mime_type = "text/plain"
            file_ext = "txt"
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
        
        buffer.seek(0)
        return buffer, mime_type, file_ext
