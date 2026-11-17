
from graph import graph, JDAnalysis
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from prompts import JOB_ANALYSIS_PROMPT


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

