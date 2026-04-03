from typing import Any, Dict, List


def normalize_analysis(result: Dict[str, Any]) -> Dict[str, Any]:
    barrier = str(result.get("barrier", "")).strip() or "Unknown"
    reason = str(result.get("reason", "")).strip()
    owner = str(result.get("owner", "")).strip() or "Unassigned"

    raw_actions = result.get("actions", [])
    actions: List[str] = []
    if isinstance(raw_actions, list):
        for action in raw_actions:
            text = str(action).strip()
            if text:
                actions.append(text)

    return {
        "barrier": barrier,
        "reason": reason,
        "actions": actions,
        "owner": owner,
    }


def build_formatted_outputs(result: Dict[str, Any]) -> Dict[str, str]:
    normalized = normalize_analysis(result)
    barrier = normalized["barrier"]
    reason = normalized["reason"]
    owner = normalized["owner"]
    actions = normalized["actions"]

    first_action = actions[0] if actions else "Review case and define next step"
    crm_task_title = f"{barrier} | {owner} | {first_action}"

    action_lines = "\n".join(f"- {action}" for action in actions) if actions else "- No actions provided"
    owner_action_card = (
        f"Owner: {owner}\n"
        f"Barrier: {barrier}\n"
        f"Reason: {reason}\n"
        f"Actions:\n{action_lines}"
    )

    leadership_escalation_note = (
        f"Escalation note: {barrier} barrier identified. "
        f"Primary owner is {owner}. "
        f"Underlying rationale: {reason}"
    )

    executive_summary = (
        f"{barrier} is the primary barrier. "
        f"{reason} "
        f"Ownership sits with {owner}."
    )

    return {
        "crm_task_title": crm_task_title,
        "owner_action_card": owner_action_card,
        "leadership_escalation_note": leadership_escalation_note,
        "executive_summary": executive_summary,
    }
