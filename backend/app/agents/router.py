import re
from typing import List, Tuple


class IntentRouter:
    @staticmethod
    def route_intent(prompt: str) -> List[str]:
        """Classifies prompt intent and returns target agent names (single or workflow sequence)."""
        text = prompt.lower().strip()

        # 1. Specific Action Intents (Checked first)
        if any(k in text for k in ["invite", "invitation", "discovery call", "schedule meeting", "kickoff", "meeting invite"]):
            return ["InvitationAgent"]

        if any(k in text for k in ["remind", "reminder", "don't forget", "alert me", "notify me", "snooze"]):
            return ["ReminderAgent"]

        if any(k in text for k in ["location", "where", "geo", "timezone", "city", "region", "trace location"]):
            return ["LocationTracerAgent"]

        if any(k in text for k in ["follow up", "follow-up", "unreplied", "sequence", "cadence"]):
            return ["FollowUpAgent"]

        if any(k in text for k in ["proposal", "scope of work", "quote", "pricing draft"]):
            return ["ProposalAgent"]

        if any(k in text for k in ["learn", "roadmap", "skill", "study", "spaced repetition"]):
            return ["LearningAgent"]

        if any(k in text for k in ["plan my", "schedule", "next 3 hours", "focus block", "agenda", "calendar"]):
            return ["TimeManagementAgent"]

        if any(k in text for k in ["analytics", "business performance", "revenue", "pipeline value", "metrics"]):
            return ["AnalyticsAgent"]

        if any(k in text for k in ["outreach", "cold email", "draft message", "prospecting"]):
            return ["OutreachAgent"]

        if any(k in text for k in ["research", "competitor", "market analysis", "summarize doc"]):
            return ["ResearchAgent"]

        if any(k in text for k in ["project", "task", "milestone", "blocker", "deliverable"]):
            return ["ProjectAgent"]

        # 2. Lead CRM Opportunities Intent
        if any(k in text for k in ["lead", "opportunity", "crm", "client opportunity", "qualify"]):
            return ["LeadAgent"]

        # 3. Strategic focus / ambiguous multi-agent workflow
        if any(k in text for k in ["focus on next", "overview", "what should i do", "daily plan"]):
            return ["TimeManagementAgent", "LeadAgent", "ProjectAgent"]

        # Default fallback agent
        return ["LeadAgent"]
