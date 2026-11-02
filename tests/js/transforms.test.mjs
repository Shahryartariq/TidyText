// Checks the browser implementation against the same cases as the Python tests.
// Run with: make test-js  (or: node --test tests/js/)
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

import { apply, details, stats } from "../../static/js/transforms.js";

const cases = JSON.parse(readFileSync(new URL("../../tools/tests/cases.json", import.meta.url), "utf8"));

for (const c of cases) {
  test(c.name, () => {
    const options = {
      lineBreaks: c.options.line_breaks,
      textCase: c.options.case,
      flags: c.options.flags ?? [],
      sort: c.options.sort,
      find: c.options.find,
      replace: c.options.replace,
    };
    const output = apply(c.input, options);
    assert.equal(output, c.expected);
    assert.deepEqual(stats(output), c.stats);
    assert.deepEqual(details(output), c.details);
  });
}
