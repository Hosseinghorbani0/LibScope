import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import test from "node:test";

import {
  getIntlLocale,
  getLocale,
  initializeI18n,
  setLocale,
  supportedLocales,
  t,
} from "../../apps/api/libscope/api/dashboard_static/i18n.js";

const localeDirectory = fileURLToPath(
  new URL("../../apps/api/libscope/api/dashboard_static/locales/", import.meta.url),
);

test("loads all seven complete locales with the correct language direction", async () => {
  const previous = {
    fetch: globalThis.fetch,
    localStorage: globalThis.localStorage,
    document: globalThis.document,
  };
  const root = { lang: "", dir: "" };
  const description = { content: "" };
  globalThis.localStorage = {
    getItem: () => null,
    setItem: () => {},
  };
  globalThis.document = {
    documentElement: root,
    title: "",
    querySelector: (selector) => selector === 'meta[name="description"]' ? description : null,
  };
  globalThis.fetch = async (url) => {
    const locale = new URL(url, "http://localhost").pathname.split("/").pop().replace(".json", "");
    const body = await readFile(`${localeDirectory}${locale}.json`, "utf8");
    return { ok: true, status: 200, json: async () => JSON.parse(body) };
  };

  try {
    await initializeI18n();
    assert.deepEqual(supportedLocales(), ["en", "fa", "ar", "es", "fr", "de", "zh"]);

    const localeExpectations = {
      en: ["en", "ltr", "en-US"],
      fa: ["fa", "rtl", "fa-IR"],
      ar: ["ar", "rtl", "ar"],
      es: ["es", "ltr", "es-ES"],
      fr: ["fr", "ltr", "fr-FR"],
      de: ["de", "ltr", "de-DE"],
      zh: ["zh-Hans", "ltr", "zh-CN"],
    };
    for (const [locale, [languageTag, direction, intlLocale]] of Object.entries(localeExpectations)) {
      await setLocale(locale);
      assert.equal(getLocale(), locale);
      assert.equal(root.lang, languageTag);
      assert.equal(root.dir, direction);
      assert.equal(getIntlLocale(), intlLocale);
      assert.ok(document.title);
      assert.ok(description.content);
    }

    await assert.rejects(() => setLocale("unsupported"), /Unsupported locale/);
  } finally {
    if (previous.fetch === undefined) delete globalThis.fetch;
    else globalThis.fetch = previous.fetch;
    if (previous.localStorage === undefined) delete globalThis.localStorage;
    else globalThis.localStorage = previous.localStorage;
    if (previous.document === undefined) delete globalThis.document;
    else globalThis.document = previous.document;
  }
});
