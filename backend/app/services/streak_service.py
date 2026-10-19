import calendar
import logging
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
from beanie import PydanticObjectId

from app.models.consolidated import Session, QuizAttempt, MistakeEntry, User

logger = logging.getLogger(__name__)


class StreakService:
    @classmethod
    async def get_user_activity_heat_map(
        cls,
        user_id: PydanticObjectId,
    ) -> Dict[str, Any]:
        """
        Computes the calendar-synchronized Weekly Consistency Activity Graph.
        In EduMeet, each week is represented by 1 box (e.g., 4 weeks in November),
        with exact Monday/Sunday or calendar date ranges described.
        When a user participates in a live classroom session, the box turns vibrant green.
        """
        user = await User.get(user_id)
        today = datetime.now(timezone.utc).date()
        current_year = today.year

        # 1. Fetch real Live Sessions for this user
        sessions = await Session.find(
            {"participants.user_id": user_id}
        ).to_list()

        user_sessions: List[Dict[str, Any]] = []
        for s in sessions:
            if s.status not in ("cancelled", "no_show_cancelled"):
                act_date = s.scheduled_start_utc.date() if s.scheduled_start_utc else s.created_at.date()
                my_p = next((p for p in s.participants if p.user_id == user_id), None)
                partner_p = next((p for p in s.participants if p.user_id != user_id), None)
                partner_name = "Peer Mentor"
                if partner_p:
                    try:
                        p_user = await User.get(partner_p.user_id)
                        if p_user and p_user.full_name:
                            partner_name = p_user.full_name
                    except Exception:
                        pass

                user_sessions.append({
                    "session_id": str(s.id),
                    "date": act_date,
                    "teach_subject": my_p.teach_subject_slug if my_p else "general",
                    "teach_topic": my_p.teach_topic_slug if my_p else "collaborative-learning",
                    "partner_name": partner_name,
                    "status": s.status,
                    "session_mode": s.session_mode,
                })

        # 2. Fetch real Diagnostic Quizzes for this user
        quizzes = await QuizAttempt.find(QuizAttempt.user_id == user_id).to_list()
        user_quizzes: List[Dict[str, Any]] = []
        for q in quizzes:
            act_date = q.completed_at.date() if q.completed_at else q.started_at.date()
            user_quizzes.append({
                "quiz_id": str(q.id),
                "date": act_date,
                "subject": q.subject_slug,
                "score": q.score_percentage,
            })

        # 3. Fetch Mistake / Spaced repetition entries
        mistakes = await MistakeEntry.find(MistakeEntry.user_id == user_id).to_list()
        user_mistakes: List[Dict[str, Any]] = []
        for m in mistakes:
            user_mistakes.append({
                "mistake_id": str(m.id),
                "date": m.created_at.date(),
            })

        # Deterministic activity seed for brand-new demo users if 0 activity exists
        # so they can see an interactive preview, but real sessions ALWAYS take precedence
        has_real_activity = len(user_sessions) > 0 or len(user_quizzes) > 0
        synthetic_sessions: List[Dict[str, Any]] = []
        if not has_real_activity:
            import hashlib
            seed_hash = int(hashlib.md5(str(user_id).encode()).hexdigest(), 16)
            # Create a couple of demonstration past sessions
            for weeks_back in (1, 3, 5, 8):
                demo_date = today - timedelta(days=weeks_back * 7 + (seed_hash % 3))
                synthetic_sessions.append({
                    "session_id": f"demo-prev-{weeks_back}",
                    "date": demo_date,
                    "teach_subject": "python" if weeks_back % 2 == 0 else "dsa",
                    "teach_topic": "algorithms" if weeks_back % 2 == 0 else "binary-trees",
                    "partner_name": "Jordan (Peer Mentor)",
                    "status": "closed",
                    "session_mode": "regular_30_30",
                })

        all_sessions = user_sessions + synthetic_sessions

        # 4. Construct Calendar Months & 4-Week Activity Boxes
        months_data: List[Dict[str, Any]] = []
        total_live_sessions = len(user_sessions)
        total_contributions = len(user_sessions) + len(user_quizzes) + len(user_mistakes)

        # Build 12 months for current year
        for m in range(1, 13):
            month_name = calendar.month_name[m]
            month_short = calendar.month_abbr[m]
            _, num_days = calendar.monthrange(current_year, m)

            # Partition the month into 4 weeks as requested:
            # Week 1: 1 - 7
            # Week 2: 8 - 14
            # Week 3: 15 - 21
            # Week 4: 22 - num_days (e.g., 28, 30, or 31)
            week_ranges = [
                (1, 7),
                (8, 14),
                (15, 21),
                (22, num_days),
            ]

            weeks_list: List[Dict[str, Any]] = []
            month_active_weeks = 0

            for w_idx, (start_d, end_d) in enumerate(week_ranges, start=1):
                start_date = date(current_year, m, start_d)
                end_date = date(current_year, m, end_d)

                start_day_name = calendar.day_name[start_date.weekday()]
                end_day_name = calendar.day_name[end_date.weekday()]

                range_label = f"{start_d} {month_short} – {end_d} {month_short}"
                full_range_label = f"{start_day_name}, {start_d} {month_short} – {end_day_name}, {end_d} {month_short} {current_year}"

                # Filter activities in this exact date range
                matching_sessions = [s for s in all_sessions if start_date <= s["date"] <= end_date]
                matching_quizzes = [q for q in user_quizzes if start_date <= q["date"] <= end_date]

                live_cnt = len(matching_sessions)
                quiz_cnt = len(matching_quizzes)
                has_live = live_cnt > 0

                is_current = (start_date <= today <= end_date)
                is_past = (end_date < today)
                is_future = (start_date > today)

                # Intensity level: 0=none, 1=quiz only, 2=1 live session (green), 3=2 sessions, 4=3+ sessions
                if has_live:
                    level = min(4, 1 + live_cnt)
                    month_active_weeks += 1
                elif quiz_cnt > 0:
                    level = 1
                    month_active_weeks += 1
                else:
                    level = 0

                # Activity cards for tooltip
                activity_items: List[Dict[str, Any]] = []
                for s in matching_sessions:
                    activity_items.append({
                        "type": "live_session",
                        "title": f"Live Session ({s['teach_subject'].upper()})",
                        "topic": s["teach_topic"].replace("-", " ").title(),
                        "partner": s["partner_name"],
                        "date": s["date"].isoformat(),
                        "status": "Completed" if s["status"] in ("closed", "followup") else "Active Classroom",
                    })

                for q in matching_quizzes:
                    activity_items.append({
                        "type": "quiz",
                        "title": f"Diagnostic Check ({q['subject'].upper()})",
                        "score": f"{q['score']:.0f}%" if q.get("score") is not None else "Completed",
                        "date": q["date"].isoformat(),
                    })

                weeks_list.append({
                    "week_id": f"{current_year}-{m:02d}-w{w_idx}",
                    "week_number": w_idx,
                    "month_number": m,
                    "start_day": start_d,
                    "end_day": end_d,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "start_day_name": start_day_name,
                    "end_day_name": end_day_name,
                    "range_label": range_label,
                    "full_range_label": full_range_label,
                    "has_live_session": has_live,
                    "live_sessions_count": live_cnt,
                    "quiz_count": quiz_cnt,
                    "total_contributions": live_cnt + quiz_cnt,
                    "level": level,
                    "is_current_week": is_current,
                    "is_past_week": is_past,
                    "is_future_week": is_future,
                    "activities": activity_items,
                })

            months_data.append({
                "month_name": month_name,
                "month_short": month_short,
                "month_number": m,
                "year": current_year,
                "weeks_count": len(weeks_list),
                "active_weeks_count": month_active_weeks,
                "weeks": weeks_list,
            })

        # Calculate weekly streak (evaluated on calendar weeks)
        current_streak = 0
        longest_streak = 0
        temp_streak = 0
        current_week_met = False

        # Flatten all past and current weeks
        all_weeks: List[Dict[str, Any]] = []
        for mo in months_data:
            for wk in mo["weeks"]:
                if not wk["is_future_week"]:
                    all_weeks.append(wk)
                if wk["is_current_week"] and wk["has_live_session"]:
                    current_week_met = True

        for wk in all_weeks:
            if wk["has_live_session"] or wk["level"] > 0:
                temp_streak += 1
                if temp_streak > longest_streak:
                    longest_streak = temp_streak
            else:
                temp_streak = 0

        # Current streak from end backwards
        for wk in reversed(all_weeks):
            if wk["is_current_week"] and not wk["has_live_session"]:
                # Current week still underway, don't penalize streak yet
                continue
            if wk["has_live_session"] or wk["level"] > 0:
                current_streak += 1
            else:
                break

        current_streak = max(current_streak, 1 if current_week_met else 0)
        longest_streak = max(longest_streak, current_streak)

        # Build legacy days_list for backward compatibility
        days_list: List[Dict[str, Any]] = []
        cur_d = today - timedelta(days=364)
        while cur_d <= today:
            d_str = cur_d.isoformat()
            has_sess = any(s["date"] == cur_d for s in all_sessions)
            cnt = 1 if has_sess else 0
            days_list.append({
                "date": d_str,
                "count": cnt,
                "level": 2 if has_sess else 0,
                "day_of_week": (cur_d.weekday() + 1) % 7,
            })
            cur_d += timedelta(days=1)

        return {
            "total_contributions": total_contributions if has_real_activity else len(synthetic_sessions),
            "total_live_sessions": total_live_sessions,
            "current_weekly_streak": current_streak if has_real_activity else 3,
            "longest_weekly_streak": max(longest_streak, 5 if not has_real_activity else current_streak),
            "streak_freezes_available": 1,
            "weekly_goal_met": current_week_met,
            "current_week_contributions": 1 if current_week_met else 0,
            "weekly_goal_target": 1,
            "year": current_year,
            "months": months_data,
            "days": days_list,
        }
