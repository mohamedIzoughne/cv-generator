def route_after_jd_analysis(state) -> str:
    analysis = state["jd_analysis"]
    
    # 1. If the job is unrelated, discard it
    if not analysis.is_related:
        return "stop"
        
    # 2. If seniority is strictly greater than internship, stop here
    # (i.e., if it's junior or mid, halt the graph)
    if analysis.seniority_level != SeniorityLevel.INTERNSHIP:
        return "stop"
        
    # 3. Otherwise, continue to the next node (e.g., knowledge base / CV tailoring)
    return "continue"



initial_state = {
    "knowledge_base_path": "/home/izourne/obsidient_notes/ALL/CV",
    "exemplars_path": "/home/izourne/obsidient_notes/ALL/CV/Example_CVs",
    "retry_count": 0
}