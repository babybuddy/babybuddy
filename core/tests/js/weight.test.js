import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { runInNewContext } from "node:vm";

const source = readFileSync(
  new URL("../../static_src/js/weight.js", import.meta.url),
  "utf8",
);

function setup(value = "", missing = null) {
  const handlers = {};
  const weight = {
    length: 1,
    val: () => value,
    on: (events, handler) => {
      for (const event of events.split(" ")) handlers[event] = handler;
    },
  };
  const warning = {
    length: 1,
    hidden: true,
    toggleClass: (name, hidden) => {
      assert.equal(name, "d-none");
      warning.hidden = hidden;
    },
  };
  const elements = { "#id_weight": weight, "#weight-unit-warning": warning };
  if (missing) delete elements[missing];

  runInNewContext(source, {
    jQuery: (selector) => elements[selector] || { length: 0 },
  });

  return {
    warning,
    handlers,
    input: (newValue, event = "input") => {
      value = newValue;
      handlers[event]();
    },
  };
}

test("warning appears while typing and disappears when corrected or cleared", () => {
  const form = setup();
  assert.equal(form.warning.hidden, true);
  form.input("3562");
  assert.equal(form.warning.hidden, false);
  form.input("3.562");
  assert.equal(form.warning.hidden, true);
  form.input("1000.01");
  assert.equal(form.warning.hidden, false);
  form.input("");
  assert.equal(form.warning.hidden, true);
});

test("values at or below 1000 and invalid values do not warn", () => {
  for (const value of ["", "3.562", "999.99", "1000", "invalid"]) {
    assert.equal(setup(value).warning.hidden, true, value);
  }
});

test("existing large weights warn immediately when the edit form opens", () => {
  assert.equal(setup("1000.01").warning.hidden, false);
});

test("change events update the warning without a submit event", () => {
  const form = setup();
  form.input("3562", "change");
  assert.equal(form.warning.hidden, false);
  assert.deepEqual(Object.keys(form.handlers), ["input", "change"]);
});

test("other pages without the weight field or warning are left alone", () => {
  for (const missing of ["#id_weight", "#weight-unit-warning"]) {
    assert.deepEqual(setup("", missing).handlers, {});
  }
});
