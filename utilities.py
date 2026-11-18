from pathlib import Path
from typing import List, Dict, Any, Literal


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