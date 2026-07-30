import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const css = readFileSync(
  join(dirname(fileURLToPath(import.meta.url)), "../src/styles.css"),
  "utf8",
);

test("styles.css defines scrollbar CSS variables", () => {
  assert.match(css, /--scrollbar-size:\s*6px/);
  assert.match(css, /--scrollbar-thumb:\s*rgba\(255,\s*255,\s*255,\s*0\.2\)/);
  assert.match(css, /--scrollbar-thumb-hover:\s*rgba\(255,\s*255,\s*255,\s*0\.4\)/);
});

test("styles.css styles main__body and sidebar__list scrollbars", () => {
  assert.match(css, /\.main__body\s*,\s*\.sidebar__list/);
  assert.match(css, /scrollbar-width:\s*thin/);
  assert.match(css, /scrollbar-color:\s*var\(--scrollbar-thumb\)\s+transparent/);
  assert.match(css, /::-webkit-scrollbar/);
  assert.match(css, /::-webkit-scrollbar-track/);
  assert.match(css, /::-webkit-scrollbar-thumb/);
  assert.match(css, /::-webkit-scrollbar-thumb:hover/);
});
