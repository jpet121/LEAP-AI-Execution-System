"""Provider-neutral controlled execution; no Compiler runtime dependency."""
from .contract import preflight, ExecutionContractView, PreflightResult
from .engine import Session, start, resume
from .artifacts import verify

__version__ = "1.0.0"
