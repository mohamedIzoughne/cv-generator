
from graph import graph, JDAnalysis, SelectionBlueprint, CVGenerationResult
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from prompts import JOB_ANALYSIS_PROMPT, STRATEGY_AGENT_PROMPT, WRITER_AGENT_PROMPT, CRITIC_PROMPT
from pathlib import Path
from utilities import get_knowledge_base_data, get_example_cvs, run_python_prechecks, get_unique_filename, get_pdf_page_count_from_log
import subprocess
import os
from pypdf import PdfReader


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

writer_prompt = ChatPromptTemplate.from_messages([
    ("system", WRITER_AGENT_PROMPT),
    ("human", """
    Job Analysis:
    {jd_analysis}

    Selection Blueprint (from Node 3A):
    {selection_blueprint}

    Factual Knowledge Base (Ground Truth):
    {full_knowledge}

    Style Exemplars (Structure & Tone Reference ONLY):
    {matched_examples}

    Revision Instructions (If retrying from Critic/Compiler):
    {revision_instructions}
    """)
])

writer_agent = writer_prompt | base_llm.with_structured_output(CVGenerationResult)

def node_3b_copywriting_agent(state: dict):
    """Translates the selection blueprint into compilable, ATS-compliant LaTeX."""

    revision_instructions = state.get("revision_instructions", "Initial generation pass. Follow all constraints strictly.")

    result = writer_agent.invoke({
        "jd_analysis": state["jd_analysis"].model_dump_json(),
        "selection_blueprint": state["selection_blueprint"].model_dump_json(),
        "full_knowledge": state["full_knowledge"],
        "matched_examples": state["matched_examples_latex"],
        "revision_instructions": revision_instructions
    })

    return {
        "latex_code": result.latex_source_code,
    }


critic_prompt = ChatPromptTemplate.from_messages([
    ("system", CRITIC_PROMPT),
    ("human", """
        Generated LaTeX Code to Audit:
        {latex_code}

        Factual Knowledge Base (Ground Truth):
        {full_knowledge}

        Deterministic Python Pre-Check Violations Already Found:
        {python_precheck_violations}
        """)
    ])


critic_agent = critic_prompt | base_llm.with_structured_output()

def node_4_critic_and_fact_checker(state: dict):
    latex_code = state["latex_code"]
    must_have_skills = state["jd_analysis"].must_have_skills

    python_violations = run_python_prechecks(latex_code, must_have_skills)
    
    audit_result = critic_agent.invoke({
        "latex_code": latex_code,
        "full_knowledge": state["full_knowledge"],
        "python_precheck_violations": python_violations
    })
    

    all_violations = list(set(python_violations + audit_result.rule_violations))
    passed = len(all_violations) == 0 and len(audit_result.hallucinated_claims) == 0

    if not passed:
        revision_instructions = (
            f"Please fix the following audit failures:\n"
            f"- Structural & Rule Violations: {all_violations}\n"
            f"- Factual Hallucinations: {audit_result.hallucinated_claims}\n"
            f"Revise the LaTeX source code strictly correcting these points while keeping the 1-page word budget."
        )
    else:
        revision_instructions = "Passed all checks."

    return {
        "audit_result": {
            "passed": passed,
            "hallucinated_claims": audit_result.hallucinated_claims,
            "rule_violations": all_violations,
            "revision_instructions": revision_instructions
        },
        "retry_count": state["retry_count"] + (0 if passed else 1)
    }





def node_5_compile_and_verify(state: dict):
    os.makedirs("output", exist_ok=True)
    
    filename = get_unique_filename(state)
    tex_path = os.path.join("output", filename)
    pdf_path = tex_path.rsplit(".", 1)[0] + ".pdf"

    latex_code = state["latex_code"]
    
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(latex_code)

    try:
        for _ in range(2):
            subprocess.run(
                [
                    "pdflatex", 
                    "-interaction=nonstopmode", 
                    "-output-directory=output", 
                    tex_path
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True
            )

        reader = PdfReader(pdf_path)
        page_count = len(reader.pages)

        if page_count > 1:
            current_retries = state.get("compression_retries", 0)
            
            if current_retries == 0:
                revision_instruction = (
                    "The compiled PDF overflowed to 2 pages. Apply the Anti-Smoothing Constraint: "
                    "drop the lowest-relevance secondary bullet or tighten phrasing by ~15% "
                    "without losing verified metrics."
                )
                return {
                    "page_count": page_count,
                    "compression_retries": current_retries + 1,
                    "revision_instruction": revision_instruction,
                    "compiler_retry_count": 0 # Reset compiler retry on successful compile phase
                }
            else:
                geometry_override = (
                    r"\usepackage[top=1.1cm, bottom=1.1cm, left=1.4cm, right=1.4cm]{geometry}"
                    r"\setlength{\parskip}{0.15em}"
                    r"\setlength{\itemsep}{0em}"
                )
                if r"\begin{document}" in latex_code:
                    latex_code = latex_code.replace(
                        r"\begin{document}", 
                        f"{geometry_override}\n\\begin{{document}}"
                    )
                
                with open(tex_path, "w", encoding="utf-8") as f:
                    f.write(latex_code)
                    
                subprocess.run(
                    ["pdflatex", "-interaction=nonstopmode", "-output-directory=output", tex_path],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                reader = PdfReader(pdf_path)
                page_count = len(reader.pages)

        print(f"Success! Final PDF generated at: {pdf_path} (Pages: {page_count})")
        return {
            "page_count": page_count,
            "pdf_path": pdf_path,
            "latex_code": latex_code,
            "compiler_retry_count": 0
        }

    except subprocess.CalledProcessError as e:
        compiler_retries = state.get("compiler_retry_count", 0) + 1
        print(f"LaTeX compilation failed (Attempt {compiler_retries}).")

        if compiler_retries > 2:
            print("Max compilation retries reached. Stopping execution.")
            return {
                "compiler_retry_count": compiler_retries,
                "compiler_error": e.stderr,
                "revision_instruction": "Compilation failed repeatedly. Terminating execution."
            }

        return {
            "compiler_retry_count": compiler_retries,
            "compiler_error": e.stderr,
            "revision_instruction": (
                f"LaTeX compilation crashed with the following error:\n{e.stderr}\n"
                "Fix the syntax errors in the LaTeX code while keeping the formatting intact."
            )
        }