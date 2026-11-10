const LOCALE_STORAGE_KEY = "libscope.locale";
const LOCALE_PATH = "/dashboard-assets/locales";
const SUPPORTED_LOCALES = new Set(["en", "fa", "ar"]);

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
  return dictionary;
}

function setDocumentLocale(locale) {
  document.documentElement.lang = locale;
  document.documentElement.dir = locale === "en" ? "ltr" : "rtl";
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
    return SUPPORTED_LOCALES.has(saved) ? saved : "en";
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
  if (!SUPPORTED_LOCALES.has(locale)) throw new Error(`Unsupported locale: ${locale}`);
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
  return { en: "en-US", fa: "fa-IR", ar: "ar" }[activeLocale] || "en-US";
}

export function t(key, variables = {}) {
  const localized = dictionaries[activeLocale]?.[key];
  if (localized === undefined && !reportedMissing.has(`${activeLocale}:${key}`)) {
    reportedMissing.add(`${activeLocale}:${key}`);
    console.error(`Missing "${key}" translation for locale "${activeLocale}".`);
  }
  const message = localized ?? dictionaries.en?.[key];
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
