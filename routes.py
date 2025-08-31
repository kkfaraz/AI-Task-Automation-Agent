from flask import render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime, timedelta
import logging

from application import app, db
from models import Subject, Chapter, StudySession, StudyPlan, ScheduleAdaptation
from ai_agent import AIStudyAgent
from scheduler import ScheduleManager
from wikipedia_service import wikipedia_service

logger = logging.getLogger(__name__)

# Initialize services
ai_agent = AIStudyAgent()
schedule_manager = ScheduleManager()


def _wants_json() -> bool:
    """Detect if request expects JSON (AJAX/fetch)."""
    if request.is_json:
        return True
    accept = (request.headers.get("Accept") or "").lower()
    xrw = (request.headers.get("X-Requested-With") or "").lower()
    return "application/json" in accept or xrw == "xmlhttprequest"


@app.route("/")
def dashboard():
    """Main dashboard showing current progress and upcoming sessions"""
    try:
        progress = schedule_manager.get_study_progress()
        upcoming_sessions = schedule_manager.get_current_schedule(days_ahead=7)
        recent_adaptations = schedule_manager.get_adaptations_history(limit=5)
        subjects = Subject.query.all()

        return render_template(
            "dashboard.html",
            progress=progress,
            upcoming_sessions=upcoming_sessions,
            recent_adaptations=recent_adaptations,
            subjects=subjects,
        )

    except Exception as e:
        logger.exception("Dashboard error: %s", e)
        flash("Error loading dashboard. Please try again.", "error")
        return render_template(
            "dashboard.html",
            progress={},
            upcoming_sessions=[],
            recent_adaptations=[],
            subjects=[],
        )


@app.route("/add-subjects", methods=["GET", "POST"])
def add_subjects():
    """Add subjects for exam preparation"""
    if request.method == "POST":
        try:
            subjects_data = []
            subject_count = int(request.form.get("subject_count", 1))

            for i in range(subject_count):
                name = request.form.get(f"subject_name_{i}")
                chapters = int(request.form.get(f"subject_chapters_{i}", 1))
                difficulty = request.form.get(f"subject_difficulty_{i}", "medium")
                exam_date_str = request.form.get(f"exam_date_{i}")

                if name and exam_date_str:
                    subjects_data.append(
                        {
                            "name": name,
                            "total_chapters": chapters,
                            "difficulty": difficulty,
                            "exam_date": exam_date_str,
                        }
                    )

            if not subjects_data:
                flash("Please add at least one subject.", "error")
                return render_template("add_subjects.html")

            flash("Analyzing subjects and creating study breakdown...", "info")
            breakdown = ai_agent.break_down_subjects(subjects_data)

            # Save subjects + chapters
            for subject_data in subjects_data:
                subject = Subject(
                    name=subject_data["name"],
                    total_chapters=subject_data["total_chapters"],
                    difficulty_level=subject_data["difficulty"],
                    exam_date=datetime.strptime(subject_data["exam_date"], "%Y-%m-%d"),
                )
                db.session.add(subject)
                db.session.flush()  # get subject.id

                # find AI breakdown for this subject
                ai_subject = None
                for b in breakdown.get("breakdown", []):
                    if b["subject_name"].lower() == subject_data["name"].lower():
                        ai_subject = b
                        break

                if ai_subject:
                    for ch in ai_subject.get("chapters", []):
                        db.session.add(
                            Chapter(
                                subject_id=subject.id,
                                title=ch["title"],
                                estimated_hours=ch.get("estimated_hours", 2.0),
                                difficulty=ch.get("difficulty", "medium"),
                            )
                        )
                else:
                    for j in range(subject_data["total_chapters"]):
                        db.session.add(
                            Chapter(
                                subject_id=subject.id,
                                title=f"Chapter {j+1}",
                                estimated_hours=2.0,
                                difficulty=subject_data["difficulty"],
                            )
                        )

            db.session.commit()
            flash("Subjects added successfully! Now create a study plan.", "success")
            return redirect(url_for("create_schedule"))

        except Exception as e:
            logger.exception("Error adding subjects: %s", e)
            db.session.rollback()
            flash("Error processing subjects. Please try again.", "error")

    return render_template("add_subjects.html")


@app.route("/create-schedule", methods=["GET", "POST"])
def create_schedule():
    """Create an AI-powered study schedule"""
    if request.method == "POST":
        try:
            plan_name = request.form.get("plan_name", "Study Plan")
            start_date_str = request.form.get("start_date")
            end_date_str = request.form.get("end_date")
            daily_hours = float(request.form.get("daily_hours", 6.0))

            preferred_times = []
            for i in range(3):
                ts = request.form.get(f"time_slot_{i}")
                if ts:
                    preferred_times.append(ts)

            if not start_date_str or not end_date_str:
                flash("Please provide start and end dates.", "error")
                return render_template("schedule.html")

            study_plan = StudyPlan(
                name=plan_name,
                start_date=datetime.strptime(start_date_str, "%Y-%m-%d"),
                end_date=datetime.strptime(end_date_str, "%Y-%m-%d"),
                total_study_hours_per_day=daily_hours,
            )
            study_plan.set_preferred_times(preferred_times)
            db.session.add(study_plan)
            db.session.commit()

            chapters = Chapter.query.all()
            if not chapters:
                flash("No subjects found. Please add subjects first.", "error")
                return redirect(url_for("add_subjects"))

            chapters_data = [
                {
                    "title": ch.title,
                    "subject_name": ch.subject.name,
                    "estimated_hours": ch.estimated_hours,
                    "difficulty": ch.difficulty,
                }
                for ch in chapters
            ]

            plan_config = {
                "start_date": start_date_str,
                "end_date": end_date_str,
                "daily_hours": daily_hours,
                "preferred_times": preferred_times,
            }

            flash("Creating intelligent study schedule...", "info")
            ai_schedule = ai_agent.create_study_schedule(chapters_data, plan_config)

            sessions = schedule_manager.create_sessions_from_ai_schedule(
                ai_schedule, study_plan.id
            )

            flash(
                f"Study schedule created successfully! {len(sessions)} study sessions planned.",
                "success",
            )
            return redirect(url_for("dashboard"))

        except Exception as e:
            logger.exception("Error creating schedule: %s", e)
            db.session.rollback()
            flash("Error creating schedule. Please try again.", "error")

    subjects = Subject.query.all()
    return render_template("schedule.html", subjects=subjects)


@app.route("/schedule-view")
def schedule_view():
    """View the current study schedule"""
    try:
        upcoming_sessions = schedule_manager.get_current_schedule(days_ahead=14)

        schedule_by_date = {}
        for s in upcoming_sessions:
            date = s["scheduled_date"]
            schedule_by_date.setdefault(date, []).append(s)

        return render_template(
            "schedule.html", schedule_by_date=schedule_by_date, view_mode=True
        )
    except Exception as e:
        logger.exception("Error viewing schedule: %s", e)
        flash("Error loading schedule.", "error")
        return render_template("schedule.html", schedule_by_date={}, view_mode=True)


# -------- Completion / Miss with robust handling (POST, GET, JSON) -------- #

@app.route("/complete-session/<int:session_id>", methods=["POST", "GET"])
def complete_session(session_id):
    """Mark a study session as completed (accepts HTML form, GET click, or AJAX)."""
    try:
        notes = ""
        if request.is_json:
            payload = request.get_json(silent=True) or {}
            notes = payload.get("notes", "") or ""
        else:
            notes = request.form.get("notes", "") or ""

        # Try via schedule_manager first
        success = False
        try:
            success = schedule_manager.mark_session_completed(session_id, notes)
        except Exception as inner:
            logger.warning("schedule_manager.mark_session_completed failed: %s", inner)

        # Fallback: direct DB update
        if not success:
            session = StudySession.query.get(session_id)
            if not session:
                msg = "Session not found."
                if _wants_json():
                    return jsonify({"ok": False, "error": msg}), 404
                flash("Error completing session.", "error")
                return redirect(url_for("dashboard"))

            # Update fields safely
            session.status = "completed"
            session.actual_end_time = datetime.utcnow()
            if hasattr(session, "notes"):
                # If your model has notes/remarks
                session.notes = (session.notes or "") + (("\n" + notes) if notes else "")
            db.session.commit()
            success = True

        if _wants_json():
            return jsonify({"ok": True}), 200

        flash("Session marked as completed!", "success")
        return redirect(url_for("dashboard"))

    except Exception as e:
        logger.exception("Error completing session: %s", e)
        db.session.rollback()
        if _wants_json():
            return jsonify({"ok": False, "error": "Internal error"}), 500
        flash("Error completing session.", "error")
        return redirect(url_for("dashboard"))


@app.route("/miss-session/<int:session_id>", methods=["POST", "GET"])
def miss_session(session_id):
    """Mark session as missed and attempt AI reschedule (form/GET/AJAX)."""
    try:
        reason = ""
        if request.is_json:
            payload = request.get_json(silent=True) or {}
            reason = payload.get("reason", "Not specified")
        else:
            reason = request.form.get("reason", "Not specified")

        # First, mark missed via schedule_manager
        success = False
        try:
            success = schedule_manager.mark_session_missed(session_id, reason)
        except Exception as inner:
            logger.warning("schedule_manager.mark_session_missed failed: %s", inner)

        # Fallback: direct mark missed
        if not success:
            session = StudySession.query.get(session_id)
            if not session:
                msg = "Session not found."
                if _wants_json():
                    return jsonify({"ok": False, "error": msg}), 404
                flash("Error marking session as missed.", "error")
                return redirect(url_for("dashboard"))

            session.status = "missed"
            if hasattr(session, "miss_reason"):
                session.miss_reason = reason
            db.session.commit()
            success = True

        # Try AI adaptation (best effort)
        try:
            session = StudySession.query.get(session_id)
            if session:
                missed_session_data = {
                    "chapter_title": session.chapter.title,
                    "scheduled_date": session.scheduled_date.strftime("%Y-%m-%d"),
                    "start_time": session.scheduled_date.strftime("%H:%M"),
                    "duration_hours": session.duration_hours,
                    "miss_reason": reason,
                }
                upcoming_sessions = schedule_manager.get_current_schedule(days_ahead=14)
                progress = schedule_manager.get_study_progress()

                adaptation = ai_agent.adapt_schedule_for_missed_session(
                    missed_session_data, upcoming_sessions, progress
                )

                adaptation_success = schedule_manager.apply_schedule_adaptation(
                    adaptation, session_id, f"missed_session: {reason}"
                )
            else:
                adaptation_success = False
        except Exception as inner:
            logger.warning("AI reschedule failed: %s", inner)
            adaptation_success = False

        if _wants_json():
            return jsonify({"ok": True, "rescheduled": bool(adaptation_success)}), 200

        if adaptation_success:
            flash("Session rescheduled intelligently by AI!", "success")
        else:
            flash(
                "Session marked as missed. Automatic rescheduling may not have applied.",
                "warning",
            )
        return redirect(url_for("dashboard"))

    except Exception as e:
        logger.exception("Error handling missed session: %s", e)
        db.session.rollback()
        if _wants_json():
            return jsonify({"ok": False, "error": "Internal error"}), 500
        flash("Error processing missed session.", "error")
        return redirect(url_for("dashboard"))


@app.route("/fetch-content/<int:chapter_id>")
def fetch_content(chapter_id):
    """Fetch Wikipedia content for a chapter"""
    try:
        chapter = Chapter.query.get_or_404(chapter_id)

        content = wikipedia_service.fetch_topic_summary(chapter.title)

        if content:
            summary = ai_agent.generate_study_summary(chapter.title, content)
            chapter.wikipedia_content = content
            chapter.summary = summary
            db.session.commit()
            flash(f"Study content fetched for {chapter.title}!", "success")
        else:
            flash(f"No Wikipedia content found for {chapter.title}.", "warning")

    except Exception as e:
        logger.exception("Error fetching content: %s", e)
        flash("Error fetching study content.", "error")

    return redirect(url_for("progress"))


@app.route("/progress")
def progress():
    """View detailed progress and chapter content"""
    try:
        subjects = Subject.query.all()
        progress_data = schedule_manager.get_study_progress()

        chapters_with_content = []
        for subject in subjects:
            for chapter in subject.chapters:
                chapters_with_content.append(
                    {
                        "id": chapter.id,
                        "title": chapter.title,
                        "subject_name": subject.name,
                        "is_completed": chapter.is_completed,
                        "difficulty": chapter.difficulty,
                        "estimated_hours": chapter.estimated_hours,
                        "has_summary": bool(chapter.summary),
                        "has_wikipedia_content": bool(chapter.wikipedia_content),
                        "summary": chapter.summary,
                        "wikipedia_content": (
                            chapter.wikipedia_content[:500] + "..."
                            if chapter.wikipedia_content
                            and len(chapter.wikipedia_content) > 500
                            else chapter.wikipedia_content
                        ),
                    }
                )

        return render_template(
            "progress.html",
            chapters=chapters_with_content,
            progress=progress_data,
            subjects=subjects,
        )

    except Exception as e:
        logger.exception("Error loading progress: %s", e)
        flash("Error loading progress data.", "error")
        return render_template("progress.html", chapters=[], progress={}, subjects=[])


@app.route("/api/progress-chart")
def progress_chart_data():
    """API endpoint for progress chart data"""
    try:
        progress = schedule_manager.get_study_progress()

        subjects = Subject.query.all()
        subject_progress = []
        for subject in subjects:
            total = len(subject.chapters)
            completed = sum(1 for ch in subject.chapters if ch.is_completed)
            rate = (completed / total * 100) if total > 0 else 0
            subject_progress.append(
                {"name": subject.name, "total": total, "completed": completed, "rate": round(rate, 1)}
            )

        daily = []
        for i in range(14, 0, -1):
            date = datetime.now() - timedelta(days=i)
            sessions_count = (
                StudySession.query.filter(
                    db.func.date(StudySession.actual_end_time) == date.date(),
                    StudySession.status == "completed",
                ).count()
            )
            daily.append({"date": date.strftime("%m/%d"), "sessions": sessions_count})

        return jsonify({"overall": progress, "by_subject": subject_progress, "daily": daily})

    except Exception as e:
        logger.exception("Error generating chart data: %s", e)
        return jsonify({"error": "Failed to load chart data"}), 500


@app.route("/reset-schedule", methods=["POST"])
def reset_schedule():
    """Reset the entire study schedule (for testing/demo purposes)"""
    try:
        StudySession.query.delete()
        Chapter.query.delete()
        Subject.query.delete()
        StudyPlan.query.delete()
        ScheduleAdaptation.query.delete()

        db.session.commit()
        flash("Schedule reset successfully. You can now start fresh.", "success")

    except Exception as e:
        logger.exception("Error resetting schedule: %s", e)
        db.session.rollback()
        flash("Error resetting schedule.", "error")

    return redirect(url_for("dashboard"))


@app.errorhandler(404)
def not_found(error):
    return render_template("layout.html"), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template("layout.html"), 500
