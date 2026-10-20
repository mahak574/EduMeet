import logging
import math
import secrets
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any

import networkx as nx
from beanie import PydanticObjectId
from fastapi import HTTPException, status

from app.models.consolidated import (
    Availability,
    Block,
    Match,
    MatchingPoolEntry,
    MatchParty,
    Session,
    SessionParticipant,
    SkillProfile,
    User,
    validate_slug,
)
from app.services.availability_service import (
    compute_contiguous_overlap_minutes,
    expand_and_merge_slots,
)

logger = logging.getLogger(__name__)


def _ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class MatchingService:
    @staticmethod
    def calculate_topic_gain(teacher_score: float, learner_score: float) -> float:
        """
        Formal reciprocal gain formulation:
        Knowledge Gap(Learner) = max(0, 80 - S_Learner)
        Competency Advantage(Teacher) = max(0, S_Teacher - 60)
        Gain = (Knowledge Gap * Competency Advantage) / (80 * 40)
        """
        knowledge_gap = max(0.0, 80.0 - learner_score)
        competency_advantage = max(0.0, teacher_score - 60.0)
        gain = (knowledge_gap * competency_advantage) / (80.0 * 40.0)
        return round(gain, 4)

    @classmethod
    def find_optimal_topic_pair(
        cls,
        profile_a: SkillProfile,
        profile_b: SkillProfile,
        common_subjects: List[str],
    ) -> Optional[Tuple[str, str, str, str, float]]:
        """
        Searches all cross-topic pairings between student A and student B across shared subjects.
        Returns: (subject_a, topic_a, subject_b, topic_b, max_reciprocal_gain)
        """
        best_reciprocal_gain = 0.0
        best_pair: Optional[Tuple[str, str, str, str, float]] = None

        # 1. First, search intra-subject complementary pairs across all common subjects
        for subject in common_subjects:
            topics_a = profile_a.subjects.get(subject, {})
            topics_b = profile_b.subjects.get(subject, {})

            if not topics_a or not topics_b:
                continue

            all_topic_keys = list(set(list(topics_a.keys()) + list(topics_b.keys())))

            for topic_a in all_topic_keys:
                score_a_teaches = topics_a.get(topic_a).score if topic_a in topics_a else 50.0
                score_b_learns = topics_b.get(topic_a).score if topic_a in topics_b else 50.0
                gain_a_to_b = cls.calculate_topic_gain(score_a_teaches, score_b_learns)

                if gain_a_to_b <= 0.0:
                    continue

                for topic_b in all_topic_keys:
                    if topic_a == topic_b:
                        continue  # Must teach different complementary topics

                    score_b_teaches = topics_b.get(topic_b).score if topic_b in topics_b else 50.0
                    score_a_learns = topics_a.get(topic_b).score if topic_b in topics_a else 50.0
                    gain_b_to_a = cls.calculate_topic_gain(score_b_teaches, score_a_learns)

                    if gain_b_to_a <= 0.0:
                        continue

                    # Strict reciprocal bottleneck: min(Gain(A->B), Gain(B->A))
                    reciprocal_gain = min(gain_a_to_b, gain_b_to_a)
                    if reciprocal_gain > best_reciprocal_gain:
                        best_reciprocal_gain = reciprocal_gain
                        best_pair = (subject, topic_a, subject, topic_b, reciprocal_gain)

        # 2. If no intra-subject pair met the threshold, or to find global cross-subject maximum:
        # Evaluate cross-subject pairs across all calibrated subjects in both profiles
        for subj_a, topics_a in profile_a.subjects.items():
            for subj_b, topics_b in profile_b.subjects.items():
                if subj_a == subj_b:
                    continue  # Intra-subject handled above

                # Check if student B studies subj_a, and student A studies subj_b
                b_topics_in_subj_a = profile_b.subjects.get(subj_a, {})
                a_topics_in_subj_b = profile_a.subjects.get(subj_b, {})

                for topic_a, skill_a in topics_a.items():
                    score_a_teaches = skill_a.score
                    score_b_learns = b_topics_in_subj_a.get(topic_a).score if topic_a in b_topics_in_subj_a else 50.0
                    gain_a_to_b = cls.calculate_topic_gain(score_a_teaches, score_b_learns)
                    if gain_a_to_b <= 0.0:
                        continue

                    for topic_b, skill_b in topics_b.items():
                        score_b_teaches = skill_b.score
                        score_a_learns = a_topics_in_subj_b.get(topic_b).score if topic_b in a_topics_in_subj_b else 50.0
                        gain_b_to_a = cls.calculate_topic_gain(score_b_teaches, score_a_learns)
                        if gain_b_to_a <= 0.0:
                            continue

                        reciprocal_gain = min(gain_a_to_b, gain_b_to_a)
                        if reciprocal_gain > best_reciprocal_gain:
                            best_reciprocal_gain = reciprocal_gain
                            best_pair = (subj_a, topic_a, subj_b, topic_b, reciprocal_gain)

        return best_pair

    @classmethod
    async def compute_pair_weight(
        cls,
        user_a: User,
        user_b: User,
        profile_a: SkillProfile,
        profile_b: SkillProfile,
        avail_a: Optional[Availability],
        avail_b: Optional[Availability],
        common_subjects: List[str],
        scheduling_horizon_days: int = 7,
    ) -> Optional[Tuple[float, Dict[str, Any]]]:
        """
        Computes edge weight W(A, B) for graph matching:
        W = min(Gain(A->B), Gain(B->A)) * M_avail * M_lang * M_style * M_history * exp(-0.5 * no_shows)
        Returns (weight, details) or None if discarded.
        """
        # 1. Blocks check
        blocked = await Block.find_one({
            "$or": [
                {"blocker_user_id": user_a.id, "blocked_user_id": user_b.id},
                {"blocker_user_id": user_b.id, "blocked_user_id": user_a.id},
            ]
        })
        if blocked:
            return None

        # 2. History & prior ratings check
        # Discard if prior rating average <= 2.0 / 5.0
        m_history = 1.0
        prior_sessions = await Session.find({
            "status": "closed",
            "participants.user_id": {"$all": [user_a.id, user_b.id]},
        }).to_list()

        for s in prior_sessions:
            for p in s.participants:
                if p.rating_given:
                    clarity = p.rating_given.get("clarity", 5.0)
                    helpfulness = p.rating_given.get("helpfulness", 5.0)
                    rating_agg = (clarity + helpfulness) / 2.0
                    if rating_agg <= 2.0:
                        return None
                    if rating_agg >= 4.5:
                        m_history = 1.2

        # 3. Optimal reciprocal topic pair
        topic_match = cls.find_optimal_topic_pair(profile_a, profile_b, common_subjects)
        if not topic_match:
            return None

        subj_a, topic_a, subj_b, topic_b, raw_gain = topic_match
        if raw_gain <= 0.0:
            return None

        # 4. Common language requirement
        langs_a = set(user_a.languages or ["en"])
        langs_b = set(user_b.languages or ["en"])
        common_langs = list(langs_a & langs_b)
        if not common_langs:
            return None  # Discard if no shared language
        m_lang = 1.15

        # 5. Teaching style alignment
        style_a = getattr(user_a.preferences, "preferred_teaching_style", "example_heavy")
        style_b = getattr(user_b.preferences, "preferred_teaching_style", "example_heavy")
        m_style = 1.10 if style_a == style_b else 1.0

        # 6. Availability expansion & contiguous overlap calculation
        today = datetime.now(timezone.utc).date()
        target_dates = [today + timedelta(days=d) for d in range(1, scheduling_horizon_days + 1)]

        def _expand_user_slots(avail: Optional[Availability], default_tz: str) -> list[Tuple[datetime, datetime]]:
            if not avail or not avail.weekly_slots:
                # Default fallback: Weekday evenings 18:00 - 20:00 (1080 - 1200) in user's timezone
                slots_local: list[tuple[date, int, int]] = []
                for d in target_dates:
                    slots_local.append((d, 1080, 1200))
                return expand_and_merge_slots(slots_local, default_tz)

            slots_local = []
            blocked_dates = set(avail.specific_blocked_dates)
            for d in target_dates:
                if d.isoformat() in blocked_dates:
                    continue
                day_idx = d.weekday()  # 0=Monday, 6=Sunday
                for ws in avail.weekly_slots:
                    if ws.day_of_week == day_idx:
                        slots_local.append((d, ws.start_min, ws.end_min))

            return expand_and_merge_slots(slots_local, avail.timezone)

        intervals_a = _expand_user_slots(avail_a, user_a.timezone)
        intervals_b = _expand_user_slots(avail_b, user_b.timezone)

        # Requires >= 60 contiguous minutes
        overlaps = compute_contiguous_overlap_minutes(intervals_a, intervals_b, min_continuous_minutes=60)
        if not overlaps:
            return None  # Discard edge if no >= 60 min continuous window exists

        total_overlap_hours = sum(dur for _, _, dur in overlaps) / 60.0
        m_avail = min(1.0, max(0.2, total_overlap_hours / 4.0))

        # 7. Reliability metric (no-show penalty)
        total_no_shows = user_a.no_show_count + user_b.no_show_count
        reliability_multiplier = math.exp(-0.5 * total_no_shows)

        # Final edge weight
        final_weight = raw_gain * m_avail * m_lang * m_style * m_history * reliability_multiplier

        # Take up to 3 proposed slots (start times of valid continuous intervals)
        proposed_slots = [start_dt for start_dt, _, _ in overlaps[:3]]

        details = {
            "subj_a": subj_a,
            "topic_a": topic_a,
            "subj_b": subj_b,
            "topic_b": topic_b,
            "common_languages": common_langs,
            "proposed_slots": proposed_slots,
            "raw_gain": raw_gain,
            "weight": final_weight,
        }
        return final_weight, details

    @classmethod
    async def join_pool(
        cls,
        user_id: PydanticObjectId,
        subject_slugs: Optional[List[str]] = None,
    ) -> MatchingPoolEntry:
        """
        Adds user to the active reciprocal teaching matching pool.
        Requires that user has completed at least one diagnostic assessment.
        """
        user = await User.get(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

        # Verify skill calibration exists
        profile = await SkillProfile.find_one(SkillProfile.user_id == user_id)
        if not profile or not profile.subjects:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please complete at least one diagnostic quiz before joining the matching pool.",
            )

        # Subjects to match for
        if subject_slugs:
            chosen_subjects = [validate_slug(s) for s in subject_slugs]
        elif user.subjects_studied:
            chosen_subjects = user.subjects_studied
        elif profile and profile.subjects:
            chosen_subjects = list(profile.subjects.keys())
        else:
            chosen_subjects = []

        # Check existing active match
        active_match = await cls.get_active_match(user_id)
        if active_match:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You already have an active or pending match proposal. Please confirm or decline it first.",
            )

        entry = await MatchingPoolEntry.find_one(MatchingPoolEntry.user_id == user_id)
        if not entry:
            entry = MatchingPoolEntry(
                user_id=user_id,
                subject_slugs=chosen_subjects,
                status="active",
                entered_at=datetime.now(timezone.utc),
            )
            await entry.insert()
        else:
            entry.status = "active"
            entry.subject_slugs = chosen_subjects
            entry.entered_at = datetime.now(timezone.utc)
            entry.current_match_id = None
            await entry.save()

        return entry

    @classmethod
    async def leave_pool(cls, user_id: PydanticObjectId) -> bool:
        """Removes user from the active matching pool."""
        entry = await MatchingPoolEntry.find_one(MatchingPoolEntry.user_id == user_id)
        if entry:
            entry.status = "cancelled"
            await entry.save()
            return True
        return False

    @classmethod
    async def get_pool_status(cls, user_id: PydanticObjectId) -> Optional[MatchingPoolEntry]:
        """Returns the current matching pool entry for user."""
        return await MatchingPoolEntry.find_one(MatchingPoolEntry.user_id == user_id)

    @classmethod
    async def get_active_match(cls, user_id: PydanticObjectId) -> Optional[Match]:
        """Returns active pending or confirmed match for the user."""
        now = datetime.now(timezone.utc)
        return await Match.find_one({
            "participants.user_id": user_id,
            "status": {"$in": ["pending", "confirmed"]},
            "expires_at": {"$gt": now},
        })

    @classmethod
    async def get_live_roster(cls, current_user: Optional[User] = None) -> Dict[str, Any]:
        """
        Retrieves real-time visibility into active students waiting in the matching pool.
        Returns strictly authenticated first name + initial and subjects (no user_id, no country, no fake sim-peers).
        """
        active_entries = await MatchingPoolEntry.find(MatchingPoolEntry.status == "active").to_list()
        peers_list: List[Dict[str, Any]] = []

        my_teach: List[str] = []
        my_learn: List[str] = []
        if current_user:
            my_teach = current_user.subjects_studied or []
            my_entry = next((e for e in active_entries if e.user_id == current_user.id), None)
            if my_entry and my_entry.subject_slugs:
                my_learn = my_entry.subject_slugs
            else:
                my_learn = []

        for entry in active_entries:
            u = await User.get(entry.user_id)
            if not u:
                continue

            is_me = current_user is not None and u.id == current_user.id
            teaches = u.subjects_studied if u.subjects_studied else []
            learns = entry.subject_slugs if entry.subject_slugs else []

            parts = (u.full_name or "Student").strip().split()
            if len(parts) > 1:
                name = f"{parts[0]} {parts[1][0]}."
            elif len(parts) == 1:
                name = parts[0]
            else:
                name = "Student"

            if is_me:
                name = f"{name} (You)"

            can_teach_me = any(s in my_learn for s in teaches)
            wants_from_me = any(s in my_teach for s in learns)
            is_compatible = can_teach_me or wants_from_me

            peers_list.append({
                "display_name": name,
                "teaches_subjects": teaches,
                "learns_subjects": learns,
                "is_compatible": is_compatible,
                "is_me": is_me,
            })

        return {
            "total_active_in_queue": len(peers_list),
            "matching_algorithm": "Reciprocal Bipartite Graph (Edmonds-Karp / Hopcroft-Karp)",
            "peers": peers_list,
        }

    @classmethod
    async def run_matching_cycle(cls) -> List[Match]:
        """
        Executes NetworkX maximum weight matching on all active matching pool entries.
        Outputs strict 1:1 reciprocal pairs and creates Match proposals.
        """
        active_entries = await MatchingPoolEntry.find(MatchingPoolEntry.status == "active").to_list()
        if len(active_entries) < 2:
            logger.info("Matching cycle skipped: fewer than 2 active pool candidates.")
            return []

        user_ids = [e.user_id for e in active_entries]
        users = await User.find({"_id": {"$in": user_ids}}).to_list()
        profiles = await SkillProfile.find({"user_id": {"$in": user_ids}}).to_list()
        availabilities = await Availability.find({"user_id": {"$in": user_ids}}).to_list()

        user_map: Dict[PydanticObjectId, User] = {u.id: u for u in users}
        profile_map: Dict[PydanticObjectId, SkillProfile] = {p.user_id: p for p in profiles}
        avail_map: Dict[PydanticObjectId, Availability] = {a.user_id: a for a in availabilities}
        entry_map: Dict[PydanticObjectId, MatchingPoolEntry] = {e.user_id: e for e in active_entries}

        # Construct General Undirected Graph
        g = nx.Graph()
        for uid in user_ids:
            g.add_node(str(uid))

        edge_details: Dict[Tuple[str, str], Dict[str, Any]] = {}

        # Evaluate all candidate edges (A, B)
        for i in range(len(user_ids)):
            u_a_id = user_ids[i]
            user_a = user_map.get(u_a_id)
            prof_a = profile_map.get(u_a_id)
            if not user_a or not prof_a:
                continue

            for j in range(i + 1, len(user_ids)):
                u_b_id = user_ids[j]
                user_b = user_map.get(u_b_id)
                prof_b = profile_map.get(u_b_id)
                if not user_b or not prof_b:
                    continue

                common_subjs = list(
                    set(entry_map[u_a_id].subject_slugs) & set(entry_map[u_b_id].subject_slugs)
                )
                if not common_subjs:
                    continue

                res = await cls.compute_pair_weight(
                    user_a=user_a,
                    user_b=user_b,
                    profile_a=prof_a,
                    profile_b=prof_b,
                    avail_a=avail_map.get(u_a_id),
                    avail_b=avail_map.get(u_b_id),
                    common_subjects=common_subjs,
                )

                if res is not None:
                    weight, details = res
                    if weight > 0.0:
                        node_a = str(u_a_id)
                        node_b = str(u_b_id)
                        g.add_edge(node_a, node_b, weight=weight)
                        edge_key = (min(node_a, node_b), max(node_a, node_b))
                        edge_details[edge_key] = details

        if g.number_of_edges() == 0:
            logger.info("Matching cycle complete: no compatible pairs with positive weight.")
            return []

        # Execute Maximum Weight Matching with Max Cardinality
        matched_pairs = nx.max_weight_matching(g, maxcardinality=True, weight="weight")
        created_matches: List[Match] = []
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=24)

        for n1_str, n2_str in matched_pairs:
            u1_id = PydanticObjectId(n1_str)
            u2_id = PydanticObjectId(n2_str)
            edge_key = (min(n1_str, n2_str), max(n1_str, n2_str))
            details = edge_details[edge_key]

            # Participant 1 teaches topic_a and learns topic_b
            # Participant 2 teaches topic_b and learns topic_a
            p1 = MatchParty(
                user_id=u1_id,
                teach_subject_slug=details["subj_a"],
                teach_topic_slug=details["topic_a"],
                learn_subject_slug=details["subj_b"],
                learn_topic_slug=details["topic_b"],
            )
            p2 = MatchParty(
                user_id=u2_id,
                teach_subject_slug=details["subj_b"],
                teach_topic_slug=details["topic_b"],
                learn_subject_slug=details["subj_a"],
                learn_topic_slug=details["topic_a"],
            )

            match_doc = Match(
                participants=[p1, p2],
                score=details["weight"],
                common_languages=details["common_languages"],
                proposed_slots=details["proposed_slots"],
                status="pending",
                created_at=now,
                expires_at=expires_at,
            )
            await match_doc.insert()
            created_matches.append(match_doc)

            # Update pool entries to matched
            for uid in [u1_id, u2_id]:
                pool_entry = entry_map.get(uid)
                if pool_entry:
                    pool_entry.status = "matched"
                    pool_entry.current_match_id = match_doc.id
                    await pool_entry.save()

        logger.info("Matching cycle created %d match proposals.", len(created_matches))
        return created_matches

    @classmethod
    async def confirm_match(
        cls,
        user_id: PydanticObjectId,
        match_id: PydanticObjectId,
        chosen_slot: datetime,
    ) -> Tuple[Match, Optional[Session]]:
        """
        Records user confirmation for a proposed match.
        When mutual confirmation occurs, atomically creates a Session.
        """
        match = await Match.get(match_id)
        if not match:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found.")

        if match.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Match is no longer pending (status: {match.status}).",
            )

        now = datetime.now(timezone.utc)
        if _ensure_utc(match.expires_at) < now:
            match.status = "expired"
            await match.save()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Match proposal has expired.")

        # Find user's participant entry
        user_party: Optional[MatchParty] = None
        partner_party: Optional[MatchParty] = None

        for p in match.participants:
            if p.user_id == user_id:
                user_party = p
            else:
                partner_party = p

        if not user_party or not partner_party:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a participant in this match.",
            )

        user = await User.get(user_id)
        if not user or not user.age_confirmed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Age confirmation is required before confirming a match or creating a session.",
            )

        # Update confirmation status
        chosen_slot_utc = _ensure_utc(chosen_slot)
        user_party.confirmed = True
        user_party.confirmed_at = now
        user_party.selected_slot = chosen_slot_utc

        created_session: Optional[Session] = None

        # Check if mutual confirmation is reached
        if partner_party.confirmed:
            match.status = "confirmed"

            # Determine mutually agreed start time
            session_start = partner_party.selected_slot or user_party.selected_slot or match.proposed_slots[0]
            session_start_utc = _ensure_utc(session_start)
            session_end_utc = session_start_utc + timedelta(minutes=60)

            # Create authoritative Session document
            created_session = Session(
                match_id=match.id,
                session_mode="regular_30_30",
                status="scheduled",
                video_room_id=f"edumeet-{secrets.token_urlsafe(16)}",
                yjs_doc_id=f"edumeet-doc-{match.id}",
                scheduled_start_utc=session_start_utc,
                scheduled_end_utc=session_end_utc,
                participants=[
                    SessionParticipant(
                        user_id=user_party.user_id,
                        role="teacher_a",
                        teach_subject_slug=user_party.teach_subject_slug,
                        teach_topic_slug=user_party.teach_topic_slug,
                        learn_subject_slug=user_party.learn_subject_slug,
                        learn_topic_slug=user_party.learn_topic_slug,
                    ),
                    SessionParticipant(
                        user_id=partner_party.user_id,
                        role="teacher_b",
                        teach_subject_slug=partner_party.teach_subject_slug,
                        teach_topic_slug=partner_party.teach_topic_slug,
                        learn_subject_slug=partner_party.learn_subject_slug,
                        learn_topic_slug=partner_party.learn_topic_slug,
                    ),
                ],
            )
            await created_session.insert()
            match.session_id = created_session.id

            logger.info("Mutual match confirmed! Created Session %s", created_session.id)

        await match.save()
        return match, created_session

    @classmethod
    async def decline_match(
        cls,
        user_id: PydanticObjectId,
        match_id: PydanticObjectId,
        reason: Optional[str] = None,
    ) -> bool:
        """
        Declines proposed match. Releases the other partner back into the active pool.
        """
        match = await Match.get(match_id)
        if not match:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found.")

        is_participant = any(p.user_id == user_id for p in match.participants)
        if not is_participant:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a participant in this match.",
            )

        match.status = "rejected"
        await match.save()

        # Release partner back to active matching pool
        for p in match.participants:
            pool_entry = await MatchingPoolEntry.find_one(MatchingPoolEntry.user_id == p.user_id)
            if pool_entry:
                if p.user_id != user_id:
                    pool_entry.status = "active"
                    pool_entry.current_match_id = None
                    await pool_entry.save()
                else:
                    pool_entry.status = "cancelled"
                    pool_entry.current_match_id = None
                    await pool_entry.save()

        logger.info("User %s declined match %s. Partner restored to active pool.", user_id, match_id)
        return True
