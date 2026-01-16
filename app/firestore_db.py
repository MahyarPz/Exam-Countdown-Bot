"""Firestore database operations for users and exams."""

import logging
from typing import Any, Dict, List, Optional
import firebase_admin
from firebase_admin import credentials, firestore
from app.config import Config

logger = logging.getLogger(__name__)

# Initialize Firebase
_db = None


def init_firestore() -> None:
    """Initialize Firestore connection."""
    global _db
    
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate(Config.GOOGLE_APPLICATION_CREDENTIALS)
            firebase_admin.initialize_app(cred, {
                'projectId': Config.FIREBASE_PROJECT_ID
            })
        
        _db = firestore.client()
        logger.info("Firestore initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing Firestore: {e}")
        raise


def get_firestore() -> Any:
    """Get Firestore client."""
    global _db
    if _db is None:
        init_firestore()
    return _db


def get_or_create_user(user_id: int) -> Dict[str, Any]:
    """Get user or create with defaults."""
    db = get_firestore()
    user_ref = db.collection('users').document(str(user_id))
    user_doc = user_ref.get()
    
    if user_doc.exists:
        return user_doc.to_dict()
    else:
        user_data = {
            'user_id': user_id,
            'timezone': Config.DEFAULT_TIMEZONE,
            'notify_time': Config.DEFAULT_NOTIFY_TIME
        }
        user_ref.set(user_data)
        logger.info(f"Created new user: {user_id}")
        return user_data


def update_user_timezone(user_id: int, timezone: str) -> None:
    """Update user's timezone."""
    db = get_firestore()
    db.collection('users').document(str(user_id)).update({
        'timezone': timezone
    })


def update_user_notify_time(user_id: int, notify_time: str) -> None:
    """Update user's notification time."""
    db = get_firestore()
    db.collection('users').document(str(user_id)).update({
        'notify_time': notify_time
    })


def add_exam(user_id: int, title: str, exam_datetime_iso: str) -> int:
    """Add exam and return per-user exam ID."""
    db = get_firestore()
    
    # Get next user_exam_id
    user_ref = db.collection('users').document(str(user_id))
    exams = user_ref.collection('exams').stream()
    max_id = 0
    for exam in exams:
        exam_data = exam.to_dict()
        if 'user_exam_id' in exam_data and exam_data['user_exam_id'] > max_id:
            max_id = exam_data['user_exam_id']
    
    user_exam_id = max_id + 1
    
    # Add exam
    exam_data = {
        'user_id': user_id,
        'user_exam_id': user_exam_id,
        'title': title,
        'exam_datetime_iso': exam_datetime_iso
    }
    
    user_ref.collection('exams').document(str(user_exam_id)).set(exam_data)
    logger.info(f"Added exam for user {user_id}: {title} (ID: {user_exam_id})")
    
    return user_exam_id


def get_user_exams(user_id: int) -> List[Dict[str, Any]]:
    """Get all exams for a user ordered by exam date."""
    db = get_firestore()
    exams = []
    
    docs = db.collection('users').document(str(user_id)).collection('exams').order_by('exam_datetime_iso').stream()
    
    for doc in docs:
        exam = doc.to_dict()
        exam['id'] = doc.id  # Add document ID
        exams.append(exam)
    
    return exams


def get_all_users() -> List[Dict[str, Any]]:
    """Get all users."""
    db = get_firestore()
    users = []
    
    docs = db.collection('users').stream()
    
    for doc in docs:
        user = doc.to_dict()
        users.append(user)
    
    return users


def delete_exam(user_exam_id: int, user_id: int) -> bool:
    """Delete an exam."""
    db = get_firestore()
    
    try:
        db.collection('users').document(str(user_id)).collection('exams').document(str(user_exam_id)).delete()
        logger.info(f"Deleted exam {user_exam_id} for user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Error deleting exam: {e}")
        return False


def get_exam_by_id(user_exam_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    """Get a specific exam by per-user ID."""
    db = get_firestore()
    
    doc = db.collection('users').document(str(user_id)).collection('exams').document(str(user_exam_id)).get()
    
    if doc.exists:
        exam = doc.to_dict()
        exam['id'] = doc.id
        return exam
    
    return None


def update_exam(user_exam_id: int, user_id: int, title: str = None, exam_datetime_iso: str = None) -> bool:
    """Update an exam's title and/or datetime."""
    db = get_firestore()
    
    try:
        exam_ref = db.collection('users').document(str(user_id)).collection('exams').document(str(user_exam_id))
        doc = exam_ref.get()
        
        if not doc.exists:
            return False
        
        update_data = {}
        if title is not None:
            update_data['title'] = title
        if exam_datetime_iso is not None:
            update_data['exam_datetime_iso'] = exam_datetime_iso
        
        if update_data:
            exam_ref.update(update_data)
            logger.info(f"Updated exam {user_exam_id} for user {user_id}: {update_data}")
        
        return True
    except Exception as e:
        logger.error(f"Error updating exam: {e}")
        return False
