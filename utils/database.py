"""
Database utilities for the pothole detection system.
"""
import os
import json
import time
import logging
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, JSON, Text, ForeignKey, func, distinct
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import pandas as pd
import sqlite3

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to use PostgreSQL, fallback to SQLite if not available
def get_database_engine():
    """Create a database engine with automatic fallback to SQLite."""
    sqlite_path = "data/pothole_detection.db"
    os.makedirs(os.path.dirname(sqlite_path), exist_ok=True)
    
    try:
        # Try PostgreSQL first
        DATABASE_URL = os.environ.get('DATABASE_URL')
        if DATABASE_URL:
            try:
                engine = create_engine(DATABASE_URL)
                # Test connection
                with engine.connect() as conn:
                    conn.execute("SELECT 1")
                logger.info("Using PostgreSQL database")
                return engine
            except Exception as e:
                logger.warning(f"PostgreSQL connection failed: {e}")
    except Exception as e:
        logger.warning(f"Error setting up PostgreSQL: {e}")
    
    # Fallback to SQLite
    logger.info("Using SQLite database")
    return create_engine(f"sqlite:///{sqlite_path}")

# Create database connection
engine = get_database_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define models
class Image(Base):
    """Model for storing uploaded images"""
    __tablename__ = "images"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    filepath = Column(String, nullable=False)
    upload_date = Column(DateTime, default=datetime.now)
    width = Column(Integer)
    height = Column(Integer)
    
    # Relationships
    detections = relationship("Detection", back_populates="image", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"Image(id={self.id}, filename={self.filename})"

class Detection(Base):
    """Model for storing pothole detections"""
    __tablename__ = "detections"
    
    id = Column(Integer, primary_key=True, index=True)
    image_id = Column(Integer, ForeignKey("images.id"), nullable=False)
    class_id = Column(Integer)
    class_name = Column(String)
    confidence = Column(Float)
    bbox_x1 = Column(Integer)
    bbox_y1 = Column(Integer)
    bbox_x2 = Column(Integer)
    bbox_y2 = Column(Integer)
    detection_date = Column(DateTime, default=datetime.now)
    
    # Relationships
    image = relationship("Image", back_populates="detections")
    
    def __repr__(self):
        return f"Detection(id={self.id}, confidence={self.confidence:.2f})"

class ImageMetadata(Base):
    """Model for storing image metadata"""
    __tablename__ = "image_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    image_id = Column(Integer, ForeignKey("images.id"), nullable=False, unique=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    inference_time = Column(Float, nullable=True)
    model_name = Column(String, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    
    def __repr__(self):
        return f"ImageMetadata(id={self.id}, image_id={self.image_id})"

# Create the tables
def create_tables():
    """Create all database tables if they don't exist"""
    Base.metadata.create_all(bind=engine)

# Get database session
def get_db():
    """Get a database session"""
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()

# Database operations
def save_detection_to_db(image_path, detections, metadata):
    """
    Save detection results to the database.
    
    Args:
        image_path (str): Path to the image file
        detections (list): List of detection dictionaries
        metadata (dict): Metadata for the image and detection process
        
    Returns:
        int: ID of the saved image
    """
    db = get_db()
    try:
        # Create image record
        filename = os.path.basename(image_path)
        image = Image(
            filename=filename,
            filepath=image_path,
            width=metadata.get('image_width'),
            height=metadata.get('image_height')
        )
        db.add(image)
        db.flush()  # Get the image ID
        
        # Create metadata record
        image_metadata = ImageMetadata(
            image_id=image.id,
            latitude=metadata.get('latitude'),
            longitude=metadata.get('longitude'),
            inference_time=metadata.get('inference_time'),
            model_name=metadata.get('model'),
            metadata_json=metadata
        )
        db.add(image_metadata)
        
        # Create detection records
        for det in detections:
            detection = Detection(
                image_id=image.id,
                class_id=det.get('class_id'),
                class_name=det.get('class_name'),
                confidence=det.get('confidence'),
                bbox_x1=det.get('bbox')[0],
                bbox_y1=det.get('bbox')[1],
                bbox_x2=det.get('bbox')[2],
                bbox_y2=det.get('bbox')[3]
            )
            db.add(detection)
        
        db.commit()
        return image.id
    except Exception as e:
        db.rollback()
        print(f"Error saving to database: {e}")
        return None
    finally:
        db.close()

def get_all_detections():
    """
    Get all detections from the database.
    
    Returns:
        list: List of detections with image information
    """
    db = get_db()
    try:
        # Join Image, Detection, and ImageMetadata
        query = db.query(
            Detection, Image, ImageMetadata
        ).join(
            Image, Detection.image_id == Image.id
        ).join(
            ImageMetadata, Image.id == ImageMetadata.image_id, isouter=True
        ).order_by(Detection.detection_date.desc())
        
        results = []
        for det, img, meta in query.all():
            result = {
                'id': det.id,
                'image_id': img.id,
                'image_path': img.filepath,
                'filename': img.filename,
                'class_name': det.class_name,
                'confidence': det.confidence,
                'bbox': [det.bbox_x1, det.bbox_y1, det.bbox_x2, det.bbox_y2],
                'detection_date': det.detection_date,
                'latitude': meta.latitude if meta else None,
                'longitude': meta.longitude if meta else None
            }
            results.append(result)
        
        return results
    finally:
        db.close()

def get_detection_statistics():
    """
    Get statistics about detections from the database.
    
    Returns:
        dict: Dictionary of statistics
    """
    db = get_db()
    try:
        # Get total images
        total_images = db.query(Image).count()
        
        # Get total detections
        total_detections = db.query(Detection).count()
        
        # Get average confidence
        avg_confidence_query = db.query(func.avg(Detection.confidence)).scalar()
        avg_confidence = float(avg_confidence_query) if avg_confidence_query else 0
        
        # Get images with detections
        images_with_detections = db.query(
            func.count(distinct(Detection.image_id))
        ).scalar()
        
        # Calculate detection rate
        detection_rate = (images_with_detections / total_images * 100) if total_images > 0 else 0
        
        # Get daily detection counts
        try:
            # This might work differently between SQLite and PostgreSQL
            daily_counts_query = db.query(
                func.date(Detection.detection_date).label('date'),
                func.count(Detection.id).label('count')
            ).group_by(
                func.date(Detection.detection_date)
            ).order_by(
                func.date(Detection.detection_date)
            )
            
            dates = []
            daily_counts = []
            for row in daily_counts_query:
                dates.append(row.date.strftime('%Y-%m-%d') if hasattr(row.date, 'strftime') else str(row.date))
                daily_counts.append(row.count)
        except Exception as e:
            logger.warning(f"Error getting daily counts: {e}")
            # Fallback to empty lists
            dates = []
            daily_counts = []
        
        return {
            "total_images": total_images,
            "total_detections": total_detections,
            "avg_potholes_per_image": total_detections / total_images if total_images > 0 else 0,
            "avg_confidence": avg_confidence,
            "detection_rate": detection_rate,
            "dates": dates,
            "daily_counts": daily_counts
        }
    except Exception as e:
        logger.error(f"Error getting detection statistics: {e}")
        # Return default values if there's an error
        return {
            "total_images": 0,
            "total_detections": 0,
            "avg_potholes_per_image": 0,
            "avg_confidence": 0,
            "detection_rate": 0,
            "dates": [],
            "daily_counts": []
        }
    finally:
        db.close()

def get_map_data():
    """
    Get data for map visualization.
    
    Returns:
        list: List of dictionaries with geotagged detection data
    """
    db = get_db()
    try:
        # Get geotagged images with detection counts
        try:
            query = db.query(
                Image.id,
                Image.filename,
                Image.filepath,
                ImageMetadata.latitude,
                ImageMetadata.longitude,
                func.count(Detection.id).label('detection_count')
            ).join(
                Detection, Image.id == Detection.image_id
            ).join(
                ImageMetadata, Image.id == ImageMetadata.image_id
            ).filter(
                ImageMetadata.latitude.isnot(None),
                ImageMetadata.longitude.isnot(None)
            ).group_by(
                Image.id,
                Image.filename,
                Image.filepath,
                ImageMetadata.latitude,
                ImageMetadata.longitude
            )
            
            results = []
            for img_id, filename, filepath, lat, lon, count in query.all():
                results.append({
                    'image_id': img_id,
                    'filename': filename,
                    'image_path': filepath,
                    'latitude': lat,
                    'longitude': lon,
                    'detection_count': count,
                    'timestamp': datetime.now().timestamp()  # Placeholder
                })
            
            return results
        except Exception as e:
            logger.warning(f"Error getting map data from database: {e}")
            # Return empty list if error
            return []
    finally:
        db.close()

# Initialize database
create_tables()