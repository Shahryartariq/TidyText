"""
Regenerate tools/tests/cases.json from scripts/case_inputs.json.

The expected outputs come from the Python implementation. Review the diff by eye
before committing; the JavaScript tests then check the browser code matches.

    make cases
"""

import json
import sys
import unicodedata
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools import transforms  # noqa: E402


def dump(data) -> str:
    """JSON that keeps readable characters but escapes invisible ones (spaces, joiners)."""
    text = json.dumps(data, indent=2, ensure_ascii=False)
    return "".join(
        f"\\u{ord(ch):04x}" if ch != " " and unicodedata.category(ch) in {"Zs", "Zl", "Zp", "Cf"} else ch
        for ch in text
    )


def main() -> None:
    inputs = json.loads((ROOT / "scripts" / "case_inputs.json").read_text(encoding="utf-8"))
    cases = []
    for case in inputs:
        opts = case["options"]
        options = transforms.Options.build(
            opts.get("line_breaks", "keep"),
            opts.get("case", "keep"),
            opts.get("flags", []),
            opts.get("sort", "keep"),
            opts.get("find", ""),
            opts.get("replace", ""),
        )
        output = transforms.apply(case["input"], options)
        cases.append(
            {
                **case,
                "expected": output,
                "stats": asdict(transforms.stats(output)),
                "details": asdict(transforms.details(output)),
            }
        )
    out = ROOT / "tools" / "tests" / "cases.json"
    out.write_text(dump(cases) + "\n", encoding="utf-8")
    (ROOT / "scripts" / "case_inputs.json").write_text(
        "[\n" + ",\n".join("  " + dump(c).replace("\n", "").replace("  ", " ") for c in inputs) + "\n]\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(cases)} cases to {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
