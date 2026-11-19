from pathlib import Path
from typing import List, Dict, Any, Literal
import os
from datetime import datetime
import re

def join_files(documents):
    context_blocks = []
    for doc in documents:
        block = (
            f"--- START DOCUMENT ---\n"
            f"Title: {doc['title']}\n"
            f"Path: {doc['path']}\n"
            f"Content:\n{doc['content']}\n"
            f"--- END DOCUMENT ---"
        )
        context_blocks.append(block)
    
    full_kb_context = "\n\n".join(context_blocks)

    return full_kb_context


def get_knowledge_base_data(base_dir):
    base_dir = Path(base_dir).resolve()
    loaded_docs = []

    for file_path in base_dir.rglob("*.md"):
        if file_path.is_file():
            rel_parts = file_path.relative_to(base_dir).parts
            
            parent_dirs = rel_parts[:-1]
            
            # Check if any parent folder starts with '_' or equals 'Example_CVs'
            should_skip = any(
                part.startswith("_") or part == "Example_CVs" 
                for part in parent_dirs
            )
            
            if should_skip:
                continue
                
            loaded_docs.append({
                "title": file_path.stem,          # e.g., "experience" for experience.md
                "path": str(file_path),           # Absolute path
                "content": file_path.read_text(encoding="utf-8")
            })

    full_knowledge_joined = join_files(loaded_docs)

    return full_knowledge_joined


def get_example_cvs(base_dir: str | Path, roles: List[str], format: Literal["tex", "md"]) -> List[Dict[str, Any]]:
    base_dir = Path(base_dir).resolve()
    loaded_docs: List[Dict[str, Any]] = []
    
    if not base_dir.exists():
        return loaded_docs
    
    # Change to *.md or *.tex depending on your file extension
    for file_path in base_dir.rglob(f"*.{format}"):
        if file_path.is_file():
            rel_parts = file_path.relative_to(base_dir).parts
            parent_dirs = rel_parts[:-1]
            
            # 1. Skip if any parent folder starts with '_'
            if any(part.startswith("_") for part in parent_dirs):
                continue
                
            # 2. Must be located inside an 'Example_CVs' directory
            if "Example_CVs" not in parent_dirs:
                continue
                
            # 3. Check if a subfolder inside 'Example_CVs' matches one of your roles
            try:
                ex_index = parent_dirs.index("Example_CVs")
                # Get all parent folders that come *after* 'Example_CVs'
                subfolders_after_example = parent_dirs[ex_index + 1:]
                
                # Check if any of those subfolders match a role in your list
                matches_role = any(sub in roles for sub in subfolders_after_example)
                if not matches_role:
                    continue
            except ValueError:
                continue
                
            # 4. Load the file content
            loaded_docs.append({
                "title": file_path.stem,          # e.g., filename without extension
                "path": str(file_path),           # Absolute path
                "content": file_path.read_text(encoding="utf-8")
            })

    full_examples_joined = join_files(loaded_docs)

    return full_examples_joined


def run_python_prechecks(latex_code: str, must_have_skills: list[str]) -> list[str]:
    """Runs fast, deterministic Python checks and returns concise violation tokens."""
    violations = []
    latex_lower = latex_code.lower()
    
    for skill in must_have_skills:
        if skill.lower() not in latex_lower:
            violations.append(f"Missing skill: {skill}")
            
    banned_environments = [r"\begin{tabular}", r"\begin{multicols}", r"\begin{table}", r"\begin{minipage}"]
    for env in banned_environments:
        if env in latex_code:
            violations.append(f"Banned env: {env}")
            
            
    return violations


def get_unique_filename(state):
    """
    Generates a filename in the format: YYYY-MM-DD-role.tex
    If it exists, we increment the counter.
    """
    role, company = state["role"], state["jd_analysis"]["company"]
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    base_name = f"{today_str}-{company}-{role}"
    filename = f"{base_name}.tex"
    
    counter = 1
    while os.path.exists(filename):
        filename = f"{base_name}0-{counter}.tex"
        counter += 1
        
    return filename

# def get_pdf_page_count_from_log(tex_filename):
#     log_filename = tex_filename.rsplit(".", 1)[0] + ".log"
    
#     try:
#         with open(log_filename, "r", encoding="utf-8", errors="ignore") as f:
#             log_content = f.read()
            
#         match = re.search(r"Output written on .*? \((\d+)\s+page", log_content)
#         if match:
#             return int(match.group(1))
#     except FileNotFoundError:
#         print(f"Log file {log_filename} not found.")
        
#     return None