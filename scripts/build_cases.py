"""
Regenerate tools/tests/cases.json from scripts/case_inputs.json.

The expected outputs come from the Python implementation. Review the diff by eye
before committing; the JavaScript tests then check the browser code matches.

    make cases
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools import transforms  # noqa: E402


def main() -> None:
    inputs = json.loads((ROOT / "scripts" / "case_inputs.json").read_text(encoding="utf-8"))
    cases = []
    for case in inputs:
        opts = case["options"]
        options = transforms.Options.build(
            opts.get("line_breaks", "keep"), opts.get("case", "keep"), opts.get("flags", [])
        )
        output = transforms.apply(case["input"], options)
        s = transforms.stats(output)
        cases.append(
            {
                **case,
                "expected": output,
                "stats": {"characters": s.characters, "words": s.words, "lines": s.lines},
            }
        )
    out = ROOT / "tools" / "tests" / "cases.json"
    out.write_text(json.dumps(cases, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(cases)} cases to {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
