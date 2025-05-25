import cv2
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import base64
from PIL import Image, ImageDraw, ImageFont
import io
import random
import colorsys

def draw_bounding_boxes(image, detections, min_confidence=0.3):
    """
    Draw bounding boxes on an image based on detection results.
    
    Args:
        image: numpy array (RGB format)
        detections: list of detection dictionaries
        min_confidence: minimum confidence threshold for display
        
    Returns:
        image with bounding boxes
    """
    # Convert to PIL for easier text handling
    image_pil = Image.fromarray(image)
    draw = ImageDraw.Draw(image_pil)
    
    # Generate distinct colors for each class
    unique_classes = set(d['class_id'] for d in detections)
    colors = generate_colors(len(unique_classes))
    color_map = {class_id: colors[i] for i, class_id in enumerate(unique_classes)}
    
    # Try to get a font
    try:
        font = ImageFont.truetype("arial.ttf", 15)
    except IOError:
        font = ImageFont.load_default()
    
    # Draw each detection
    for detection in detections:
        if detection['confidence'] < min_confidence:
            continue
        
        bbox = detection['bbox']
        x1, y1, x2, y2 = bbox
        confidence = detection['confidence']
        class_id = detection['class_id']
        class_name = detection['class_name']
        
        # Get color
        color = color_map.get(class_id, (255, 0, 0))  # Default to red if class not found
        
        # Draw rectangle
        draw.rectangle([x1, y1, x2, y2], outline=color, width=2)
        
        # Draw label background
        label = f"{class_name}: {confidence:.2f}"
        label_size = draw.textbbox((0, 0), label, font=font)
        label_width = label_size[2] - label_size[0]
        label_height = label_size[3] - label_size[1]
        
        # Draw label background (slightly above the box)
        draw.rectangle(
            [x1, max(0, y1 - label_height - 5), x1 + label_width, y1],
            fill=color
        )
        
        # Draw text
        draw.text((x1, max(0, y1 - label_height - 5)), label, fill=(255, 255, 255), font=font)
    
    return np.array(image_pil)

def generate_colors(num_colors):
    """
    Generate a list of distinct colors.
    
    Args:
        num_colors: number of colors to generate
        
    Returns:
        list of RGB color tuples
    """
    colors = []
    for i in range(num_colors):
        # Use HSV color space to generate evenly spaced colors
        h = i / num_colors
        s = 0.8
        v = 0.9
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        colors.append((int(r * 255), int(g * 255), int(b * 255)))
    return colors

def encode_image_to_base64(image_array):
    """
    Convert a numpy image array to base64 encoded string.
    
    Args:
        image_array: numpy array image (RGB)
        
    Returns:
        base64 encoded string
    """
    # Convert from RGB to BGR for cv2
    if len(image_array.shape) == 3 and image_array.shape[2] == 3:
        img = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
    else:
        img = image_array
        
    success, buffer = cv2.imencode('.png', img)
    encoded_image = base64.b64encode(buffer).decode('utf-8')
    return encoded_image

def create_confidence_histogram(detections, bins=10):
    """
    Create a plotly histogram of detection confidences.
    
    Args:
        detections: list of detection dictionaries
        bins: number of bins for the histogram
        
    Returns:
        plotly figure object
    """
    if not detections:
        # Return empty figure if no detections
        fig = go.Figure()
        fig.add_annotation(
            text="No detections available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        fig.update_layout(
            title="Confidence Distribution",
            xaxis_title="Confidence",
            yaxis_title="Count"
        )
        return fig
    
    # Extract confidence values
    confidence_values = [d['confidence'] for d in detections]
    
    # Create histogram
    fig = px.histogram(
        x=confidence_values, 
        nbins=bins,
        labels={'x': 'Confidence Score'},
        title='Distribution of Detection Confidence Scores',
        color_discrete_sequence=['#FF4B4B'],
    )
    
    fig.update_layout(
        xaxis_title="Confidence Score",
        yaxis_title="Number of Detections",
        bargap=0.05
    )
    
    return fig

def create_detection_summary_chart(results_data):
    """
    Create a summary chart of detection statistics.
    
    Args:
        results_data: list of result dictionaries
        
    Returns:
        plotly figure object
    """
    if not results_data:
        # Return empty figure if no data
        fig = go.Figure()
        fig.add_annotation(
            text="No detection data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return fig
    
    # Extract data
    dates = []
    counts = []
    avg_confidences = []
    
    for result in results_data:
        # Extract timestamp and convert to date string
        timestamp = result.get('timestamp', 0)
        date_str = pd.to_datetime(timestamp, unit='s').strftime('%Y-%m-%d')
        
        detections = result.get('detections', [])
        count = len(detections)
        
        # Calculate average confidence
        if count > 0:
            avg_conf = sum(d['confidence'] for d in detections) / count
        else:
            avg_conf = 0
            
        dates.append(date_str)
        counts.append(count)
        avg_confidences.append(avg_conf)
    
    # Create DataFrame for plotting
    df = pd.DataFrame({
        'Date': dates,
        'Count': counts,
        'Average Confidence': avg_confidences
    })
    
    # Aggregate by date
    agg_df = df.groupby('Date').agg({'Count': 'sum', 'Average Confidence': 'mean'}).reset_index()
    
    # Create figure with dual y-axis
    fig = go.Figure()
    
    # Add bar chart for counts
    fig.add_trace(
        go.Bar(
            x=agg_df['Date'],
            y=agg_df['Count'],
            name='Number of Detections',
            marker_color='#FF4B4B'
        )
    )
    
    # Add line chart for average confidence
    fig.add_trace(
        go.Scatter(
            x=agg_df['Date'],
            y=agg_df['Average Confidence'],
            name='Average Confidence',
            yaxis='y2',
            line=dict(color='#1f77b4', width=3)
        )
    )
    
    # Update layout with dual y-axis
    fig.update_layout(
        title='Detection Summary Over Time',
        xaxis=dict(title='Date'),
        yaxis=dict(
            title='Number of Detections',
            titlefont=dict(color='#FF4B4B'),
            tickfont=dict(color='#FF4B4B')
        ),
        yaxis2=dict(
            title='Average Confidence',
            titlefont=dict(color='#1f77b4'),
            tickfont=dict(color='#1f77b4'),
            anchor='x',
            overlaying='y',
            side='right'
        ),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        )
    )
    
    return fig

def create_pothole_map(detection_data, default_lat=40.7128, default_lon=-74.0060):
    """
    Create a map visualization of pothole locations.
    
    Args:
        detection_data: list of dictionaries with geotagged detection data
        default_lat: default latitude if no data available
        default_lon: default longitude if no data available
        
    Returns:
        plotly figure object
    """
    # Filter valid data with coordinates
    valid_data = []
    for item in detection_data:
        metadata = item.get('metadata', {})
        if 'latitude' in metadata and 'longitude' in metadata:
            lat = metadata['latitude']
            lon = metadata['longitude']
            count = len(item.get('detections', []))
            if count > 0:
                valid_data.append({
                    'latitude': lat,
                    'longitude': lon,
                    'count': count,
                    'filename': item.get('filename', 'Unknown'),
                    'timestamp': item.get('timestamp', 0)
                })
    
    # Create DataFrame
    if valid_data:
        df = pd.DataFrame(valid_data)
        
        # Create map
        fig = px.scatter_mapbox(
            df,
            lat='latitude',
            lon='longitude',
            size='count',
            color='count',
            hover_name='filename',
            hover_data={
                'count': True,
                'timestamp': False,
                'latitude': False,
                'longitude': False
            },
            color_continuous_scale=px.colors.sequential.Reds,
            size_max=15,
            zoom=10,
            title='Pothole Detection Map'
        )
        
        fig.update_layout(
            mapbox_style="open-street-map",
            margin={"r": 0, "t": 30, "l": 0, "b": 0}
        )
    else:
        # Return empty map centered at default location
        fig = go.Figure(go.Scattermapbox(
            lat=[default_lat],
            lon=[default_lon],
            mode='markers',
            marker=go.scattermapbox.Marker(size=1, color='rgb(242, 242, 242)'),
            text=['No geotagged pothole data available'],
        ))
        
        fig.update_layout(
            mapbox={
                'style': "open-street-map",
                'center': {'lat': default_lat, 'lon': default_lon},
                'zoom': 10
            },
            margin={"r": 0, "t": 30, "l": 0, "b": 0},
            title='Pothole Detection Map (No Data)',
        )
    
    return fig
