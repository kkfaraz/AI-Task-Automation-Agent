import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
from models import StudySession, StudyPlan, Chapter, ScheduleAdaptation
from application import db
import logging

logger = logging.getLogger(__name__)

class ScheduleManager:
    """Manages study schedules and handles adaptations"""
    
    def __init__(self):
        pass
    
    def create_sessions_from_ai_schedule(self, ai_schedule: Dict, study_plan_id: int) -> List[StudySession]:
        """Convert AI-generated schedule to database sessions"""
        sessions = []
        
        for day_schedule in ai_schedule.get('schedule', []):
            date_str = day_schedule['date']
            schedule_date = datetime.strptime(date_str, '%Y-%m-%d')
            
            for session_data in day_schedule.get('sessions', []):
                # Find the corresponding chapter
                chapter = Chapter.query.filter_by(title=session_data['chapter_title']).first()
                
                if chapter:
                    # Parse time
                    start_time = datetime.strptime(f"{date_str} {session_data['start_time']}", '%Y-%m-%d %H:%M')
                    
                    session = StudySession(
                        chapter_id=chapter.id,
                        scheduled_date=start_time,
                        duration_hours=session_data['duration_hours'],
                        status='scheduled'
                    )
                    
                    db.session.add(session)
                    sessions.append(session)
        
        db.session.commit()
        return sessions
    
    def get_current_schedule(self, days_ahead: int = 7) -> List[Dict]:
        """Get upcoming study sessions"""
        end_date = datetime.now() + timedelta(days=days_ahead)
        
        sessions = StudySession.query.filter(
            StudySession.scheduled_date >= datetime.now(),
            StudySession.scheduled_date <= end_date,
            StudySession.status.in_(['scheduled', 'rescheduled'])
        ).order_by(StudySession.scheduled_date).all()
        
        schedule_data = []
        for session in sessions:
            schedule_data.append({
                'id': session.id,
                'chapter_title': session.chapter.title,
                'subject_name': session.chapter.subject.name,
                'scheduled_date': session.scheduled_date.strftime('%Y-%m-%d'),
                'start_time': session.scheduled_date.strftime('%H:%M'),
                'duration_hours': session.duration_hours,
                'status': session.status,
                'difficulty': session.chapter.difficulty
            })
        
        return schedule_data
    
    def mark_session_completed(self, session_id: int, notes: str = None) -> bool:
        """Mark a study session as completed"""
        session = StudySession.query.get(session_id)
        if not session:
            return False
        
        session.status = 'completed'
        session.actual_start_time = datetime.now() - timedelta(hours=session.duration_hours)
        session.actual_end_time = datetime.now()
        session.notes = notes
        session.updated_at = datetime.now()
        
        # Mark chapter as completed if this was the last session
        chapter = session.chapter
        remaining_sessions = StudySession.query.filter_by(
            chapter_id=chapter.id, 
            status='scheduled'
        ).count()
        
        if remaining_sessions == 0:
            chapter.is_completed = True
        
        db.session.commit()
        return True
    
    def mark_session_missed(self, session_id: int, reason: str = None) -> bool:
        """Mark a study session as missed"""
        session = StudySession.query.get(session_id)
        if not session:
            return False
        
        session.status = 'missed'
        session.notes = f"Missed session. Reason: {reason or 'Not specified'}"
        session.updated_at = datetime.now()
        
        db.session.commit()
        return True
    
    def apply_schedule_adaptation(self, adaptation_plan: Dict, original_session_id: int, reason: str) -> bool:
        """Apply AI-generated schedule adaptation"""
        try:
            original_session = StudySession.query.get(original_session_id)
            if not original_session:
                return False
            
            # Record the adaptation
            adaptation = ScheduleAdaptation(
                original_session_id=original_session_id,
                adaptation_reason=reason,
                ai_reasoning=adaptation_plan.get('reasoning', ''),
                changes_made=json.dumps(adaptation_plan)
            )
            db.session.add(adaptation)
            
            # Reschedule the missed session
            reschedule_info = adaptation_plan.get('adaptation_plan', {}).get('reschedule_missed', {})
            if reschedule_info:
                new_date_str = reschedule_info['new_date']
                new_time_str = reschedule_info['new_time']
                new_datetime = datetime.strptime(f"{new_date_str} {new_time_str}", '%Y-%m-%d %H:%M')
                
                # Create new session for the rescheduled content
                new_session = StudySession(
                    chapter_id=original_session.chapter_id,
                    scheduled_date=new_datetime,
                    duration_hours=original_session.duration_hours + reschedule_info.get('duration_adjustment', 0),
                    status='rescheduled'
                )
                db.session.add(new_session)
            
            # Apply other schedule adjustments
            adjustments = adaptation_plan.get('adaptation_plan', {}).get('schedule_adjustments', [])
            for adjustment in adjustments:
                if adjustment['change_type'] == 'reschedule':
                    # Find and update the session
                    chapter = Chapter.query.filter_by(title=adjustment['original_session']).first()
                    if chapter:
                        session_to_adjust = StudySession.query.filter_by(
                            chapter_id=chapter.id,
                            status='scheduled'
                        ).first()
                        
                        if session_to_adjust:
                            new_datetime = datetime.strptime(
                                f"{adjustment['new_date']} {adjustment['new_time']}", 
                                '%Y-%m-%d %H:%M'
                            )
                            session_to_adjust.scheduled_date = new_datetime
                            session_to_adjust.status = 'rescheduled'
                            session_to_adjust.updated_at = datetime.now()
            
            db.session.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply schedule adaptation: {e}")
            db.session.rollback()
            return False
    
    def get_study_progress(self) -> Dict[str, Any]:
        """Calculate overall study progress"""
        total_sessions = StudySession.query.count()
        completed_sessions = StudySession.query.filter_by(status='completed').count()
        missed_sessions = StudySession.query.filter_by(status='missed').count()
        
        total_chapters = Chapter.query.count()
        completed_chapters = Chapter.query.filter_by(is_completed=True).count()
        
        # Get next upcoming session
        next_session = StudySession.query.filter(
            StudySession.scheduled_date >= datetime.now(),
            StudySession.status.in_(['scheduled', 'rescheduled'])
        ).order_by(StudySession.scheduled_date).first()
        
        # Calculate days remaining until first exam
        from models import Subject
        earliest_exam = Subject.query.order_by(Subject.exam_date).first()
        days_remaining = 0
        if earliest_exam:
            days_remaining = (earliest_exam.exam_date - datetime.now()).days
        
        completion_rate = (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0
        
        return {
            'total_sessions': total_sessions,
            'completed_sessions': completed_sessions,
            'missed_sessions': missed_sessions,
            'pending_sessions': total_sessions - completed_sessions - missed_sessions,
            'total_chapters': total_chapters,
            'completed_chapters': completed_chapters,
            'completion_rate': round(completion_rate, 1),
            'days_remaining': max(0, days_remaining),
            'next_session': {
                'chapter_title': next_session.chapter.title if next_session else None,
                'subject_name': next_session.chapter.subject.name if next_session else None,
                'scheduled_date': next_session.scheduled_date.strftime('%Y-%m-%d %H:%M') if next_session else None
            } if next_session else None,
            'avg_daily_progress': round(completion_rate / max(1, days_remaining), 2) if days_remaining > 0 else 0
        }
    
    def get_missed_sessions(self) -> List[Dict]:
        """Get all missed sessions that need rescheduling"""
        missed = StudySession.query.filter_by(status='missed').all()
        
        missed_data = []
        for session in missed:
            missed_data.append({
                'id': session.id,
                'chapter_title': session.chapter.title,
                'subject_name': session.chapter.subject.name,
                'scheduled_date': session.scheduled_date.strftime('%Y-%m-%d'),
                'start_time': session.scheduled_date.strftime('%H:%M'),
                'duration_hours': session.duration_hours,
                'notes': session.notes,
                'miss_reason': session.notes.replace('Missed session. Reason: ', '') if session.notes else 'Not specified'
            })
        
        return missed_data
    
    def get_adaptations_history(self, limit: int = 10) -> List[Dict]:
        """Get history of schedule adaptations"""
        adaptations = ScheduleAdaptation.query.order_by(
            ScheduleAdaptation.created_at.desc()
        ).limit(limit).all()
        
        history = []
        for adaptation in adaptations:
            original_session = StudySession.query.get(adaptation.original_session_id)
            changes_data = json.loads(adaptation.changes_made) if adaptation.changes_made else {}
            
            history.append({
                'id': adaptation.id,
                'date': adaptation.created_at.strftime('%Y-%m-%d %H:%M'),
                'reason': adaptation.adaptation_reason,
                'chapter_title': original_session.chapter.title if original_session else 'Unknown',
                'subject_name': original_session.chapter.subject.name if original_session else 'Unknown',
                'ai_reasoning': adaptation.ai_reasoning,
                'changes_summary': self._summarize_changes(changes_data)
            })
        
        return history
    
    def _summarize_changes(self, changes_data: Dict) -> str:
        """Create a human-readable summary of changes made"""
        summary_parts = []
        
        adaptation_plan = changes_data.get('adaptation_plan', {})
        reschedule = adaptation_plan.get('reschedule_missed', {})
        
        if reschedule:
            summary_parts.append(f"Rescheduled to {reschedule['new_date']} at {reschedule['new_time']}")
        
        adjustments = adaptation_plan.get('schedule_adjustments', [])
        if adjustments:
            summary_parts.append(f"{len(adjustments)} other sessions adjusted")
        
        return "; ".join(summary_parts) if summary_parts else "Schedule optimization applied"
