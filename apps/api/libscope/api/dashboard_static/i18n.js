const LOCALE_STORAGE_KEY = "libscope.locale";
const LOCALE_PATH = "/dashboard-assets/locales";
const SUPPORTED_LOCALES = ["en", "fa", "ar", "es", "fr", "de", "zh"];
const SUPPORTED_LOCALE_SET = new Set(SUPPORTED_LOCALES);
const RTL_LOCALES = new Set(["fa", "ar"]);
const HTML_LOCALES = { zh: "zh-Hans" };
const INTL_LOCALES = {
  en: "en-US",
  fa: "fa-IR",
  ar: "ar",
  es: "es-ES",
  fr: "fr-FR",
  de: "de-DE",
  zh: "zh-CN",
};

let activeLocale = "en";
let dictionaries = {};
const reportedMissing = new Set();

function isDictionary(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value) &&
    Object.values(value).every((item) => typeof item === "string");
}

async function loadDictionary(locale) {
  const response = await fetch(`${LOCALE_PATH}/${locale}.json`, {
    headers: { Accept: "application/json" },
    credentials: "same-origin",
  });
  if (!response.ok) throw new Error(`Unable to load the ${locale} translation file (HTTP ${response.status}).`);
  const dictionary = await response.json();
  if (!isDictionary(dictionary)) throw new Error(`The ${locale} translation file is not a flat string dictionary.`);
  if (locale !== "en" && dictionaries.en) {
    const expectedKeys = Object.keys(dictionaries.en).sort();
    const actualKeys = Object.keys(dictionary).sort();
    if (expectedKeys.length !== actualKeys.length || expectedKeys.some((key, index) => key !== actualKeys[index])) {
      throw new Error(`The ${locale} translation file does not have complete key coverage.`);
    }
    for (const key of expectedKeys) {
      const placeholders = (message) => [...message.matchAll(/\{\{(\w+)\}\}/g)].map((match) => match[1]).sort();
      if (JSON.stringify(placeholders(dictionary[key])) !== JSON.stringify(placeholders(dictionaries.en[key]))) {
        throw new Error(`The ${locale} translation for "${key}" has mismatched placeholders.`);
      }
    }
  }
  return dictionary;
}

function setDocumentLocale(locale) {
  document.documentElement.lang = HTML_LOCALES[locale] || locale;
  document.documentElement.dir = RTL_LOCALES.has(locale) ? "rtl" : "ltr";
  document.title = dictionaries[locale]?.["document.title"] ?? dictionaries.en?.["document.title"] ?? "LibScope";
  const description = document.querySelector('meta[name="description"]');
  if (description) {
    description.content = dictionaries[locale]?.["document.description"] ??
      dictionaries.en?.["document.description"] ?? "";
  }
}

function readSavedLocale() {
  try {
    const saved = localStorage.getItem(LOCALE_STORAGE_KEY);
    return SUPPORTED_LOCALE_SET.has(saved) ? saved : "en";
  } catch (error) {
    console.warn("Unable to read the saved language preference.", error);
    return "en";
  }
}

export async function initializeI18n() {
  dictionaries.en = await loadDictionary("en");
  const requestedLocale = readSavedLocale();
  if (requestedLocale !== "en") {
    try {
      dictionaries[requestedLocale] = await loadDictionary(requestedLocale);
      activeLocale = requestedLocale;
    } catch (error) {
      console.error("The saved language could not be loaded; English fallback is active.", error);
      activeLocale = "en";
    }
  }
  setDocumentLocale(activeLocale);
  const bootstrapStatus = document.querySelector("[data-i18n-key]");
  if (bootstrapStatus) bootstrapStatus.textContent = t(bootstrapStatus.dataset.i18nKey);
  return activeLocale;
}

export async function setLocale(locale) {
  if (!SUPPORTED_LOCALE_SET.has(locale)) throw new Error(`Unsupported locale: ${locale}`);
  if (!dictionaries[locale]) dictionaries[locale] = await loadDictionary(locale);
  activeLocale = locale;
  setDocumentLocale(locale);
  try {
    localStorage.setItem(LOCALE_STORAGE_KEY, locale);
  } catch (error) {
    console.warn("Unable to save the language preference.", error);
  }
}

export function getLocale() {
  return activeLocale;
}

export function getIntlLocale() {
  return INTL_LOCALES[activeLocale] || "en-US";
}

export function t(key, variables = {}) {
  const localized = dictionaries[activeLocale]?.[key];
  if (localized === undefined && !reportedMissing.has(`${activeLocale}:${key}`)) {
    reportedMissing.add(`${activeLocale}:${key}`);
    console.error(`Missing "${key}" translation for locale "${activeLocale}".`);
  }
  const message = localized;
  if (message === undefined) {
    if (!reportedMissing.has(`en:${key}`)) {
      reportedMissing.add(`en:${key}`);
      console.error(`Missing required English translation "${key}".`);
    }
    return `⟦${key}⟧`;
  }
  return message.replace(/\{\{(\w+)\}\}/g, (_, name) => String(variables[name] ?? ""));
}

export function hasTranslation(key) {
  return dictionaries[activeLocale]?.[key] !== undefined && dictionaries.en?.[key] !== undefined;
}

export function supportedLocales() {
  return [...SUPPORTED_LOCALES];
}

