# backend/app/responder.py
def build_answer(message, plan, top_results):
    qs = plan.get("intermediate_queries", [])
    w = plan.get("weights", {})
    return (
        f"I searched using: {', '.join(qs[:2])}. "
        f"Weighting: text={w.get('text',0):.1f}, image={w.get('image',0):.1f}. "
        f"Here are the closest matches."
    )
