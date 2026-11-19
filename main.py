from langgraph.graph import END, START, StateGraph
from graph import graph, SeniorityLevel
from nodes import node_5_compile_and_verify, node_4_critic_and_fact_checker, node_3b_copywriting_agent, node_3a_strategy_architect, node_2_context_loader, node_1_analyze_jd

def route_after_jd_analysis(state) -> str:
    analysis = state["jd_analysis"]
    
    if not analysis.is_related:
        return "stop"
        
    if analysis.seniority_level != SeniorityLevel.INTERNSHIP:
        return "stop"
        
    return "continue"

MAX_COMPILER_RETRIES = 2
MAX_COMPRESSION_RETRIES = 1


def router_after_compile(state: dict) -> Literal["revise", "pass"]:
    compiler_error = state.get("compiler_error")
    compiler_retries = state.get("compiler_retry_count", 0)
    page_count = state.get("page_count", 1)
    compression_retries = state.get("compression_retries", 0)

    if compiler_error:
        if compiler_retries <= MAX_COMPILER_RETRIES:
            return "revise"
        return "pass"

    if page_count > 1 and compression_retries <= MAX_COMPRESSION_RETRIES:
        return "revise"

    return "pass"


initial_state = {
    "knowledge_base_path": "/home/izourne/obsidient_notes/ALL/CV",
    "exemplars_path": "/home/izourne/obsidient_notes/ALL/CV/Example_CVs",
    "retry_count": 0
}


builder = StateGraph(graph)

builder.add_node("analyze_node", node_1_analyze_jd)
builder.add_node("context_loader", node_2_context_loader)
builder.add_node("strategy_architect", node_3a_strategy_architect)
builder.add_node("copywriting_agent", node_3b_copywriting_agent)
builder.add_node("fact_checker", node_4_critic_and_fact_checker)
builder.add_node("compile_and_verify", node_5_compile_and_verify)


builder.add_edge(START, "analyze_node")
builder.add_edge("analyze_node", "context_loader")
builder.add_edge("context_loader", "strategy_architect")
builder.add_conditional_edges("strategy_architect", "copywriting_agent")

builder.add_conditional_edges(
    "strategy_architect",               
    route_after_jd_analysis,   
    {                            
        "continue": "copywriting_agent",
        "stop": END,
    },
)


def route_after_critic(state: dict) -> Literal["pass", "revise", "stop"]:
    audit = state.get("audit_result") or {}
    if audit.get("passed", False) or state.get("retry_count", 0) > MAX_RETRIES:
        return "pass"

    return "revise"


# builder.add_edge("copywriting_agent", "fact_checker")
builder.add_conditional_edges("fact_checker", route_after_critic, {
    "revise": "copywriting_agent",
    "pass": "compile_and_verify"
})

builder.add_edge("fact_checker", "compile_and_verify")

builder.add_conditional_edges("compile_and_verify", router_after_compile, {
    "revise": "copywriting_agent",
    "pass": END
})


