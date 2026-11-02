"""Adapters live at the edge. Host mode needs no API credential or Runner."""
from pathlib import Path
import json
import time
import urllib.request
from .canonical import canonical, digest, read_json
from .protocols import schema, CHALLENGE, CLASSIFICATION


class HostResponseRequired(RuntimeError):
    pass


class StructuredAdapter:
    def __init__(self):
        self.audit = []
        self.latency_seconds = 0.0

    def call(self, role, payload, output_schema):
        prompt = (Path(__file__).parent / "prompts" / (role + ".txt")).read_text(encoding="utf-8")
        request = {"role": role, "instructions": prompt, "input": payload, "output_schema": output_schema}
        start = time.monotonic()
        response = self.exchange(request)
        if self.latency_seconds is not None:
            self.latency_seconds += time.monotonic() - start
        self.audit.append({"request": request, "response": response})
        return response

    def interpret(self, request_state):
        return self.call("interpreter", {"request_state": request_state.to_dict()}, schema("semantic_ir.schema.json"))

    def challenge(self, request_state, candidate_ir):
        # No interpreter messages, rationale, or repair history cross this boundary.
        return self.call("challenger", {"request_state": request_state.to_dict(), "candidate_ir": candidate_ir}, CHALLENGE)

    def classify_issue(self, request_state, candidate_ir, findings):
        return self.call("classifier", {"request_state": request_state.to_dict(), "candidate_ir": candidate_ir,
                                        "findings": findings}, CLASSIFICATION)

    def reconcile(self, request_state, candidate_ir, findings):
        return self.call("reconciler", {"request_state": request_state.to_dict(), "candidate_ir": candidate_ir,
                                        "findings": findings}, schema("semantic_ir.schema.json"))


class HostAdapter(StructuredAdapter):
    """Content-addressed exchange with a Python-capable host reasoning model.

    Only a trusted host writes response files. Hashes bind context, not model honesty.
    """
    def __init__(self, directory):
        super().__init__()
        self.latency_seconds = None  # Host reasoning happens outside this Python call.
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def exchange(self, request):
        key = digest(canonical(request))
        request_file = self.directory / f"{key}.request.json"
        request_file.write_bytes(canonical(request))
        response_file = self.directory / f"{key}.response.json"
        if not response_file.exists():
            raise HostResponseRequired(f"Host model response needed: {request_file}")
        envelope = read_json(response_file)
        if set(envelope) != {"request_sha256", "output"} or envelope["request_sha256"] != key:
            raise ValueError("Host response bound to wrong request")
        return envelope["output"]


class HTTPAdapter(StructuredAdapter):
    """Optional OpenAI-compatible chat endpoint, explicitly configured by operator.

    Network access occurs here only. There is no external task execution or tools.
    """
    def __init__(self, endpoint, model, api_key, timeout=120):
        super().__init__()
        if not endpoint.startswith("https://"):
            raise ValueError("Model endpoint must use HTTPS")
        self.endpoint, self.model, self.api_key, self.timeout = endpoint, model, api_key, timeout

    def exchange(self, request):
        body = {"model": self.model, "messages": [
            {"role": "system", "content": request["instructions"]},
            {"role": "user", "content": canonical(request["input"]).decode()}],
            "response_format": {"type": "json_schema", "json_schema": {
                "name": request["role"], "schema": request["output_schema"], "strict": True}}}
        req = urllib.request.Request(self.endpoint, data=canonical(body), headers={
            "Content-Type": "application/json", "Authorization": "Bearer " + self.api_key})
        with urllib.request.urlopen(req, timeout=self.timeout) as response:
            if int(response.headers.get("Content-Length", "0")) > 8_000_000:
                raise ValueError("Oversized model response")
            data = response.read(8_000_001)
        if len(data) > 8_000_000:
            raise ValueError("Oversized model response")
        return json.loads(json.loads(data)["choices"][0]["message"]["content"])
