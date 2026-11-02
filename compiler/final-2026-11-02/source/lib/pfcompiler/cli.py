import argparse
import os
from pathlib import Path
import sys
from .canonical import canonical, read_json
from .source import RequestState
from .compiler import Compiler
from .adapters import HostAdapter, HTTPAdapter
from .artifacts import verify_package, replay, IntegrityError
from .validation import validate_ir, InvalidIR
from .protocols import check_challenge

EXIT = {"COMPILE_RELEASED": 0, "COMPILE_NEEDS_CLARIFICATION": 10,
        "COMPILE_UNSUPPORTED": 20, "COMPILE_FAILED": 50}


def adapter(args):
    if args.adapter == "host":
        return HostAdapter(args.exchange)
    if args.adapter == "http":
        return HTTPAdapter(os.environ["PF_MODEL_ENDPOINT"], os.environ["PF_MODEL_NAME"],
                           os.environ["PF_MODEL_API_KEY"])
    raise ValueError("Unknown adapter; use host or http")


def state_file(path):
    path = Path(path)
    if path.stat().st_size > 1_000_000:
        raise ValueError("Request file exceeds SYSTEM source cap")
    if path.suffix.lower() == ".json":
        return RequestState.from_dict(read_json(path))
    return RequestState.capture(path.read_text(encoding="utf-8-sig"))


def main(argv=None):
    parser = argparse.ArgumentParser(prog="pfcompile")
    subs = parser.add_subparsers(dest="command", required=True)
    for name in ("compile", "continue", "challenge"):
        p = subs.add_parser(name)
        p.add_argument("request")
        p.add_argument("--adapter", choices=["host", "http"], required=True)
        p.add_argument("--exchange", default=".pfexchange")
        if name == "challenge":
            p.add_argument("ir")
        else:
            p.add_argument("--out", required=True)
        if name == "continue":
            p.add_argument("--clarification", required=True)
            p.add_argument("--target", required=True, help="Question ID from clarifications.json")
    p = subs.add_parser("validate-ir")
    p.add_argument("ir")
    p.add_argument("--state", help="Defaults to sibling request_state.json")
    p = subs.add_parser("render")
    p.add_argument("ir")
    p.add_argument("--out", required=True)
    p = subs.add_parser("verify-package")
    p.add_argument("zip")
    p = subs.add_parser("replay")
    p.add_argument("receipt")
    subs.add_parser("self-check")
    args = parser.parse_args(argv)
    try:
        if args.command in {"compile", "continue"}:
            state = state_file(args.request)
            if args.command == "continue":
                prior = Path(args.request).parent
                receipt = read_json(prior / "compiler_receipt.json")
                questions = read_json(prior / "clarifications.json")
                if receipt["status"] != "COMPILE_NEEDS_CLARIFICATION" or receipt["source_state_sha256"] != state.sha256 or args.target not in {q["id"] for q in questions}:
                    raise ValueError("Clarification must answer a pending question for this state")
                state = state.append(args.clarification, target=args.target)
            result = Compiler().compile(state, adapter(args))
            result.write(args.out)
            print(canonical({"status": result.status, "out": str(Path(args.out).resolve())}).decode(), end="")
            return EXIT[result.status]
        if args.command == "challenge":
            state, ir = state_file(args.request), read_json(args.ir)
            validate_ir(ir, state)
            result = adapter(args).challenge(state, ir)
            check_challenge(result)
            print(canonical(result).decode(), end="")
            return 0 if result["verdict"] == "PASS" else 30
        if args.command == "validate-ir":
            path = Path(args.ir)
            state = state_file(args.state or path.with_name("request_state.json"))
            result = validate_ir(read_json(path), state)
        elif args.command == "verify-package":
            result = {"status": "VERIFIED", "files": len(verify_package(args.zip))}
        elif args.command == "replay":
            result = replay(args.receipt)
        elif args.command == "render":
            path = Path(args.ir)
            replay(path.with_name("compiler_receipt.json"))
            out = Path(args.out)
            out.mkdir(parents=True, exist_ok=True)
            if any(out.iterdir()):
                raise ValueError("Render output must be empty")
            for name in ("contract.xml", "portable_brief.txt"):
                (out / name).write_bytes(path.with_name(name).read_bytes())
            result = {"status": "RENDERED", "out": str(out.resolve())}
        else:
            from .selfcheck import self_check
            result = self_check()
        print(canonical(result).decode(), end="")
        return 0
    except IntegrityError as e:
        print(str(e), file=sys.stderr)
        return 40
    except (ValueError, InvalidIR, OSError, KeyError) as e:
        print(str(e), file=sys.stderr)
        return 30
    except Exception as e:
        print(type(e).__name__ + ": " + str(e), file=sys.stderr)
        return 50


if __name__ == "__main__":
    sys.exit(main())
