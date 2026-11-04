"""PHON command-line interface."""
import argparse
import sys
from pathlib import Path


def cmd_run(args):
    from phon.parser import parse
    from phon.emitter import to_config
    from phon.simulator import Simulator
    path = Path(args.file)
    if not path.exists():
        print("error: file not found: " + str(path), file=sys.stderr)
        return 1
    try:
        source = path.read_text(encoding="utf-8")
        ast = parse(source)
        config = to_config(ast)
        sim = Simulator(config)
        results = sim.run()
        print("# " + path.name)
        if isinstance(results, dict):
            for k, v in results.items():
                print(str(k) + ": " + str(v))
        else:
            print(results)
        return 0
    except Exception as e:
        print("error: " + type(e).__name__ + ": " + str(e), file=sys.stderr)
        return 1


def cmd_compile(args):
    from phon.parser import parse
    path = Path(args.file)
    if not path.exists():
        print("error: file not found: " + str(path), file=sys.stderr)
        return 1
    try:
        source = path.read_text(encoding="utf-8")
        ast = parse(source)
        out = args.output or str(path.with_suffix(".json"))
        try:
            from phon.emitter import emit_file
            emit_file(ast, out)
        except (ImportError, AttributeError):
            from phon.emitter import to_json
            with open(out, "w", encoding="utf-8") as f:
                f.write(to_json(ast))
        print("Wrote " + out)
        return 0
    except Exception as e:
        print("error: " + type(e).__name__ + ": " + str(e), file=sys.stderr)
        return 1


def cmd_test(args):
    from phon.parser import parse
    examples_dir = Path(args.dir) if args.dir else Path("examples")
    if not examples_dir.exists():
        print("error: directory not found: " + str(examples_dir), file=sys.stderr)
        return 1
    ok = 0
    fail = 0
    for f in sorted(examples_dir.rglob("*.phon")):
        try:
            source = f.read_text(encoding="utf-8")
            parse(source)
            ok += 1
            print("[OK]   " + str(f.relative_to(examples_dir)))
        except Exception as e:
            fail += 1
            print("[FAIL] " + str(f.relative_to(examples_dir)) + ": " + str(e), file=sys.stderr)
    print("")
    print(str(ok) + " passed, " + str(fail) + " failed")
    return 0 if fail == 0 else 1


def main(argv=None):
    import phon
    parser = argparse.ArgumentParser(
        prog="phon",
        description="PHON - unified DSL for photonic and phononic wave computing",
    )
    parser.add_argument("--version", action="version", version="phon " + phon.__version__)
    sub = parser.add_subparsers(dest="command")
    p_run = sub.add_parser("run", help="Simulate a .phon file")
    p_run.add_argument("file")
    p_run.set_defaults(func=cmd_run)
    p_compile = sub.add_parser("compile", help="Compile .phon to JSON config")
    p_compile.add_argument("file")
    p_compile.add_argument("-o", "--output")
    p_compile.set_defaults(func=cmd_compile)
    p_test = sub.add_parser("test", help="Run all .phon files in examples/")
    p_test.add_argument("dir", nargs="?")
    p_test.set_defaults(func=cmd_test)
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
