
from graph import graph, JDAnalysis, SelectionBlueprint
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from prompts import JOB_ANALYSIS_PROMPT, STRATEGY_AGENT_PROMPT
from pathlib import Path
from utilities import get_knowledge_base_data, get_example_cvs

base_llm = ChatGoogleGenerativeAI(model="gemini-3.5-flash", temperature=0)


job_analysis_prompt = ChatPromptTemplate.from_messages([
    ("system", JOB_ANALYSIS_PROMPT),
    ("human", "{job_description}")
])

job_analysis_agent = job_analysis_prompt | base_llm.with_structured_output(JDAnalysis)


def node_1_analyze_jd(state: graph):
    # jd_analysis_llm = llm.with_structured_output(JDAnalysis)
    result = job_analysis_agent.invoke({"job_description": state["raw_jd"]})

    return {
        "jd_analysis": result
    }


def node_2_context_loader(state):
    # analysis = state["jd_analysis"]
    # base_dir = Path(state["knowledge_base_path"]).resolve()
    
    full_knowledge = get_knowledge_base_data(state["knowledge_base_path"])
    full_examples_tex = get_example_cvs(state["exemplars_path"], [state["jd_analysis"]["target_role"]], "tex")
    full_examples_md = get_example_cvs(state["exemplars_path"], [state["jd_analysis"]["target_role"]], "md")

    return {
        "full_knowledge": full_knowledge,
        "matched_examples": full_examples_md,
        "matched_examples_latex": full_examples_tex
    }


strategy_prompt = ChatPromptTemplate.from_messages([
    ("system", STRATEGY_AGENT_PROMPT),
    ("human", """
    Job Analysis:
    {jd_analysis}

    Factual Knowledge Base:
    {full_knowledge}

    Targeted Style Exemplars:
    {matched_examples}
    """)
])

strategy_agent = strategy_prompt | base_llm.with_structured_output(SelectionBlueprint)

def node_3a_strategy_architect(state: dict):
    """Curates 'Best 5' entries and maps out the XYZ narrative blueprint."""
    result = strategy_agent.invoke({
        "jd_analysis": state["jd_analysis"].model_dump_json(),
        "full_knowledge": state["full_knowledge"],
        "matched_examples": state["matched_examples"]
    })

    return {
        "selection_blueprint": result
    }