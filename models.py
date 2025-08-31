from application import db
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import json

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    total_chapters = db.Column(db.Integer, nullable=False)
    difficulty_level = db.Column(db.String(20), default='medium')  # easy, medium, hard
    exam_date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with chapters
    chapters = db.relationship('Chapter', backref='subject', lazy=True, cascade='all, delete-orphan')

class Chapter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    estimated_hours = db.Column(db.Float, default=2.0)
    difficulty = db.Column(db.String(20), default='medium')
    is_completed = db.Column(db.Boolean, default=False)
    summary = db.Column(db.Text, nullable=True)  # AI-generated summary
    wikipedia_content = db.Column(db.Text, nullable=True)  # Fetched content
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with study sessions
    sessions = db.relationship('StudySession', backref='chapter', lazy=True, cascade='all, delete-orphan')

class StudySession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id'), nullable=False)
    scheduled_date = db.Column(db.DateTime, nullable=False)
    duration_hours = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='scheduled')  # scheduled, completed, missed, rescheduled
    actual_start_time = db.Column(db.DateTime, nullable=True)
    actual_end_time = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class StudyPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    total_study_hours_per_day = db.Column(db.Float, default=6.0)
    preferred_study_times = db.Column(db.Text)  # JSON string of preferred time slots
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_preferred_times(self):
        """Return preferred study times as a list"""
        if self.preferred_study_times:
            return json.loads(self.preferred_study_times)
        return ["09:00-12:00", "14:00-17:00", "19:00-22:00"]  # Default slots
    
    def set_preferred_times(self, times_list):
        """Set preferred study times from a list"""
        self.preferred_study_times = json.dumps(times_list)

class ScheduleAdaptation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_session_id = db.Column(db.Integer, db.ForeignKey('study_session.id'), nullable=False)
    adaptation_reason = db.Column(db.String(100), nullable=False)  # missed_session, difficulty_adjustment, etc.
    ai_reasoning = db.Column(db.Text)  # AI's explanation for the adaptation
    changes_made = db.Column(db.Text)  # JSON string describing what was changed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    original_session = db.relationship('StudySession', backref='adaptations')
    