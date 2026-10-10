""" Filesystem tools: read, write, list, delete - all bounded to the workspace.
"""

from pathlib import Path
from harness.tools.registry import designated_tool


# Set the workspace directory. All filesystem tools operate inside this. 
# We resolve it once at import to a canonical absolute path
WORKSPACE = Path("./workspace").resolve()

# Create the workspace directory if it doesn't exist. 
WORKSPACE.mkdir(exist_ok=True)

def _resolve_path(path: str) -> Path:
    """
    Resolve 'path' against the workspace and confirm it stays inside.
    """

    # Step 1: join the user-supplied path against the workspace, and canonicalize.
    # Canonicalization expands '..' segments - without it '../../../etc/passwd
    # would slip past the check below
    target = (WORKSPACE / path).resolve()

    # STep 2: confrim the canonical path is still inside WORKSPACE
    # If '..' walked the path out of the worspace, this will catch it.
    if not target.is_relative_to(WORKSPACE):
        raise ValueError(f"path escapes workspace: {path}")
    return target

@designated_tool
def read(path: str) -> str:
    """ Read the contents of a file from the workspace, by path"""
    # Resolve safely, then read the file's text content in 1 call
    return _resolve_path(path).read_text()

@designated_tool
def write(path: str, content: str) -> str:
    """Write content to a file in the workspace, creating it if needed. Overwrites the file if it already exists. Returns confirmation with byte count."""
    # Step 1: resolve the target path safely.
    target = _resolve_path(path)

    # Step 2: Ensure parent directories exist so nested paths like 
    # notes/research/findings.md work with a prior mkdir call
    target.parent.mkdir(parents=True, exist_ok=True)

    # Step 3: write the content (overwrites if the file exists).
    target.write_text(content)

    # Step 4: return a structured confirmation the model can verify against. 
    return f"wrote {len(content)} bytes to {path}"

@designated_tool
def list(path: str = ".") -> str:
    """List the files and directories at the given path inside the workspace. Defaults to the workspace root. Returns one entry per line."""
    # Step 1: resolve the path safely. Defaults to workspace root.
    target = _resolve_path(path)

    # Step 2: refuse if the target isn't a directory - return an error string
    if not target.is_dir():
        return f"error: not a directory: {path}"

    # Step 3: sort entries for deterministic output: append '/' to directories 
    # so the model can distinguish them from other files at a glance
    entries = sorted(target.iterdir())
    return "\n".join(e.name + ("/" if e.is_dir() else "") for e in entries)

@designated_tool
def mkdir(path: str) -> str:
    """Create a directory in the workspace, including any parent directories. No error if the directory already exists."""
    # Step 1: resolve the path safely.
    target = _resolve_path(path)

    # Step 2: create the directory tree. parents = True builds the full chain so the agent can create nested paths in one call. 'exist_ok=True' makes recreating an existing directory a no-op rather than an error 
    target.mkdir(parents=True, exist_ok=True)

    return f"created directory {path}"

@designated_tool
def delete(path: str) -> str:
    """Delete a file from the workspace. Will not delete directories"""
    # Step 1: resolve the path safely
    target = _resolve_path(path)

    # Step 2: refuse directories - recursive delete is too dangerous right now. 
    if target.is_dir():
        return f"error: refusing to delete directory {path}"

    # Step 3: delete the file and confirm
    target.unlink()
    return f"deleted {path}"