import assert from "node:assert/strict";
import test from "node:test";

import { readRoute, watchRoute, writeRoute } from "../../apps/api/libscope/api/dashboard_static/routes.js";

test("serializes package routes and restores navigation without duplicate events", () => {
  const previousWindow = globalThis.window;
  const listeners = {};
  const location = {
    href: "http://localhost/#/overview",
    hash: "#/overview",
  };
  globalThis.window = {
    location,
    history: {
      pushState(_state, _title, path) {
        location.href = `http://localhost/${path}`;
        location.hash = path;
      },
      replaceState(_state, _title, path) {
        location.href = `http://localhost/${path}`;
        location.hash = path;
      },
    },
    addEventListener(name, listener) {
      listeners[name] = listener;
    },
  };

  try {
    assert.deepEqual(readRoute("#/packages/42/security"), {
      view: "package-detail",
      packageId: 42,
      detailTab: "security",
    });

    let changes = 0;
    watchRoute(() => { changes += 1; });
    writeRoute("package-detail", 42, "security");
    assert.equal(location.hash, "#/packages/42/security");

    location.href = "http://localhost/#/overview";
    location.hash = "#/overview";
    listeners.popstate();
    listeners.hashchange();
    assert.equal(changes, 1);

    location.href = "http://localhost/#/settings";
    location.hash = "#/settings";
    listeners.hashchange();
    assert.equal(changes, 2);
  } finally {
    if (previousWindow === undefined) delete globalThis.window;
    else globalThis.window = previousWindow;
  }
});
