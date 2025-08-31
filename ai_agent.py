import os
import json
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class AIStudyAgent:
    """AI-powered study planning and adaptation agent using OpenRouter API"""
    
    def __init__(self):
        self.openrouter_api_key = os.environ.get("OPENROUTER_API_KEY", "")
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "openai/gpt-4o"
        
    def _make_api_request(self, messages: List[Dict], max_tokens: int = 1500) -> Dict:
        """Make a request to OpenRouter API"""
        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:5000",  # Required by OpenRouter
            "X-Title": "AI Study Planner"  # Optional, helps with usage tracking
        }
        
        data = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.7
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenRouter API request failed: {e}")
            raise Exception(f"AI service unavailable: {e}")
    
    def break_down_subjects(self, subjects_data: List[Dict]) -> Dict[str, Any]:
        """Break down subjects into manageable chapters using AI"""
        subjects_text = "\n".join([
            f"- {subj['name']}: {subj['total_chapters']} chapters, difficulty: {subj.get('difficulty', 'medium')}, exam date: {subj['exam_date']}"
            for subj in subjects_data
        ])
        
        messages = [
            {
                "role": "system",
                "content": """You are an expert study planner. Your task is to break down subjects into specific, manageable chapters with realistic time estimates. 
                
                Respond with a JSON object in this format:
                {
                  "breakdown": [
                    {
                      "subject_name": "Subject Name",
                      "chapters": [
                        {
                          "title": "Chapter Title",
                          "estimated_hours": 2.5,
                          "difficulty": "medium",
                          "key_topics": ["topic1", "topic2"],
                          "prerequisites": ["prerequisite_chapter"]
                        }
                      ]
                    }
                  ],
                  "study_tips": ["tip1", "tip2"],
                  "reasoning": "Explanation of the breakdown strategy"
                }"""
            },
            {
                "role": "user",
                "content": f"""Please break down these subjects for exam preparation:

{subjects_text}

Consider:
1. Logical progression of topics
2. Difficulty levels and time requirements
3. Dependencies between chapters
4. Optimal study order for retention"""
            }
        ]
        
        try:
            response = self._make_api_request(messages)
            content = response['choices'][0]['message']['content']
            
            # Try to parse JSON from the response
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # If direct JSON parsing fails, try to extract JSON from the response
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                else:
                    raise Exception("Could not parse AI response as JSON")
                    
        except Exception as e:
            logger.error(f"Subject breakdown failed: {e}")
            # Return a fallback structure
            return self._fallback_subject_breakdown(subjects_data)
    
    def create_study_schedule(self, chapters_data: List[Dict], plan_config: Dict) -> Dict[str, Any]:
        """Create an intelligent study schedule using AI"""
        chapters_text = "\n".join([
            f"- {ch['title']} ({ch['subject_name']}): {ch['estimated_hours']}h, difficulty: {ch['difficulty']}"
            for ch in chapters_data
        ])
        
        config_text = f"""
        Study Plan Configuration:
        - Start Date: {plan_config['start_date']}
        - End Date: {plan_config['end_date']}
        - Daily Study Hours: {plan_config['daily_hours']}
        - Preferred Time Slots: {plan_config.get('preferred_times', 'Not specified')}
        - Break Preferences: {plan_config.get('break_preferences', 'Standard breaks')}
        """
        
        messages = [
            {
                "role": "system", 
                "content": """You are an expert study scheduler. Create an optimal study schedule that maximizes learning efficiency and retention.

                Respond with JSON in this format:
                {
                  "schedule": [
                    {
                      "date": "2025-08-26",
                      "sessions": [
                        {
                          "chapter_title": "Chapter Name",
                          "subject": "Subject Name", 
                          "start_time": "09:00",
                          "end_time": "11:30",
                          "duration_hours": 2.5,
                          "session_type": "new_material",
                          "break_after": 15
                        }
                      ]
                    }
                  ],
                  "scheduling_principles": ["principle1", "principle2"],
                  "adaptation_suggestions": ["suggestion1", "suggestion2"]
                }"""
            },
            {
                "role": "user",
                "content": f"""Create an optimal study schedule for these chapters:

{chapters_text}

{config_text}

Apply these scheduling principles:
1. Spaced repetition for better retention
2. Harder topics when mental energy is highest
3. Regular breaks and varied subjects
4. Buffer time for review and catch-up
5. Progressive difficulty increase"""
            }
        ]
        
        try:
            response = self._make_api_request(messages, max_tokens=2000)
            content = response['choices'][0]['message']['content']
            
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                else:
                    raise Exception("Could not parse schedule JSON")
                    
        except Exception as e:
            logger.error(f"Schedule creation failed: {e}")
            return self._fallback_schedule(chapters_data, plan_config)
    
    def adapt_schedule_for_missed_session(self, missed_session: Dict, upcoming_sessions: List[Dict], 
                                        current_progress: Dict) -> Dict[str, Any]:
        """Intelligently reschedule when a study session is missed"""
        
        missed_info = f"""
        Missed Session:
        - Chapter: {missed_session['chapter_title']}
        - Scheduled: {missed_session['scheduled_date']} at {missed_session.get('start_time', 'N/A')}
        - Duration: {missed_session['duration_hours']} hours
        - Reason: {missed_session.get('miss_reason', 'Not specified')}
        """
        
        upcoming_info = "\n".join([
            f"- {sess['chapter_title']}: {sess['scheduled_date']} ({sess['duration_hours']}h)"
            for sess in upcoming_sessions[:10]  # Limit to next 10 sessions
        ])
        
        progress_info = f"""
        Current Progress:
        - Total Sessions: {current_progress.get('total_sessions', 0)}
        - Completed: {current_progress.get('completed_sessions', 0)}
        - Remaining Days: {current_progress.get('days_remaining', 0)}
        - Average Daily Progress: {current_progress.get('avg_daily_progress', 0)}%
        """
        
        messages = [
            {
                "role": "system",
                "content": """You are an intelligent study schedule adaptation expert. When a study session is missed, provide smart rescheduling that maintains learning effectiveness.

                Respond with JSON:
                {
                  "adaptation_plan": {
                    "reschedule_missed": {
                      "new_date": "2025-08-27",
                      "new_time": "14:00",
                      "duration_adjustment": 0,
                      "reasoning": "Why this slot works best"
                    },
                    "schedule_adjustments": [
                      {
                        "original_session": "Chapter X",
                        "change_type": "reschedule",
                        "new_date": "2025-08-28", 
                        "new_time": "16:00",
                        "reasoning": "Adjustment explanation"
                      }
                    ]
                  },
                  "impact_analysis": {
                    "urgency_level": "medium",
                    "catch_up_difficulty": "manageable",
                    "recommendations": ["rec1", "rec2"]
                  },
                  "reasoning": "Overall adaptation strategy explanation"
                }"""
            },
            {
                "role": "user",
                "content": f"""A study session was missed and needs intelligent rescheduling:

{missed_info}

Upcoming Sessions:
{upcoming_info}

{progress_info}

Please provide an adaptation plan that:
1. Finds the best slot to reschedule the missed session
2. Minimizes disruption to the existing schedule
3. Maintains study momentum and effectiveness
4. Considers the criticality of the missed topic
5. Provides clear reasoning for all changes"""
            }
        ]
        
        try:
            response = self._make_api_request(messages, max_tokens=2000)
            content = response['choices'][0]['message']['content']
            
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                else:
                    raise Exception("Could not parse adaptation JSON")
                    
        except Exception as e:
            logger.error(f"Schedule adaptation failed: {e}")
            return self._fallback_adaptation(missed_session, upcoming_sessions)
    
    def generate_study_summary(self, topic: str, wikipedia_content: str = None) -> str:
        """Generate a concise study summary for a topic"""
        content_text = f"\nAdditional context from Wikipedia:\n{wikipedia_content}" if wikipedia_content else ""
        
        messages = [
            {
                "role": "system",
                "content": """You are an expert study material creator. Generate concise, well-structured study summaries that help students learn effectively. Focus on key concepts, important facts, and memorable explanations."""
            },
            {
                "role": "user", 
                "content": f"""Create a comprehensive study summary for: {topic}

{content_text}

Structure the summary with:
1. Key Concepts (bullet points)
2. Important Facts to Remember  
3. Common Exam Questions/Topics
4. Memory Aids or Mnemonics
5. Real-world Applications (if applicable)

Keep it concise but thorough, suitable for exam preparation."""
            }
        ]
        
        try:
            response = self._make_api_request(messages, max_tokens=1000)
            return response['choices'][0]['message']['content']
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return f"Summary for {topic}:\n\n[AI summary generation temporarily unavailable. Please review your study materials and create notes manually.]"
    
    def _fallback_subject_breakdown(self, subjects_data: List[Dict]) -> Dict[str, Any]:
        """Fallback method when AI breakdown fails"""
        breakdown = []
        for subject in subjects_data:
            chapters = []
            for i in range(subject['total_chapters']):
                chapters.append({
                    "title": f"Chapter {i+1}",
                    "estimated_hours": 2.0,
                    "difficulty": subject.get('difficulty', 'medium'),
                    "key_topics": [f"Topic {i+1}"],
                    "prerequisites": []
                })
            
            breakdown.append({
                "subject_name": subject['name'],
                "chapters": chapters
            })
        
        return {
            "breakdown": breakdown,
            "study_tips": ["Review regularly", "Take breaks", "Practice with examples"],
            "reasoning": "Fallback breakdown due to AI service unavailability"
        }
    
    def _fallback_schedule(self, chapters_data: List[Dict], plan_config: Dict) -> Dict[str, Any]:
        """Fallback scheduling when AI fails"""
        # Simple round-robin scheduling
        schedule = []
        start_date = datetime.strptime(plan_config['start_date'], '%Y-%m-%d')
        daily_hours = plan_config['daily_hours']
        
        current_date = start_date
        chapters_queue = chapters_data.copy()
        
        while chapters_queue and current_date.strftime('%Y-%m-%d') <= plan_config['end_date']:
            daily_sessions = []
            remaining_hours = daily_hours
            
            for chapter in chapters_queue[:]:
                if remaining_hours >= chapter['estimated_hours']:
                    daily_sessions.append({
                        "chapter_title": chapter['title'],
                        "subject": chapter['subject_name'],
                        "start_time": "09:00",
                        "end_time": "11:00",
                        "duration_hours": chapter['estimated_hours'],
                        "session_type": "new_material",
                        "break_after": 15
                    })
                    remaining_hours -= chapter['estimated_hours']
                    chapters_queue.remove(chapter)
            
            if daily_sessions:
                schedule.append({
                    "date": current_date.strftime('%Y-%m-%d'),
                    "sessions": daily_sessions
                })
            
            current_date += timedelta(days=1)
        
        return {
            "schedule": schedule,
            "scheduling_principles": ["Basic time allocation", "Sequential chapter progression"],
            "adaptation_suggestions": ["Monitor progress", "Adjust as needed"]
        }
    
    def _fallback_adaptation(self, missed_session: Dict, upcoming_sessions: List[Dict]) -> Dict[str, Any]:
        """Fallback adaptation when AI fails"""
        # Simple rescheduling to next available day
        tomorrow = datetime.now() + timedelta(days=1)
        
        return {
            "adaptation_plan": {
                "reschedule_missed": {
                    "new_date": tomorrow.strftime('%Y-%m-%d'),
                    "new_time": "14:00",
                    "duration_adjustment": 0,
                    "reasoning": "Rescheduled to next available day"
                },
                "schedule_adjustments": []
            },
            "impact_analysis": {
                "urgency_level": "medium", 
                "catch_up_difficulty": "manageable",
                "recommendations": ["Review missed material", "Stay consistent"]
            },
            "reasoning": "Basic rescheduling due to AI service unavailability"
        }
