"""Public domain errors carry stable non-sensitive codes."""
class LedgerError(Exception):
    def __init__(self, status: int, code: str):
        self.status = status
        self.code = code
        super().__init__(code)
