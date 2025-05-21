import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import LanguageDetector from "i18next-browser-languagedetector";
import en from "./locale/en.json";
import fi from "./locale/fi.json";
import sv from "./locale/sv.json";

i18n
  .use(initReactI18next)
  .use(LanguageDetector)
  .init({
    resources: {
      en,
      fi,
      sv,
    },
    detection: {
      order: ["path"],
      lookupFromPathIndex: 0,
    },
    fallbackLng: "en",
    interpolation: {
      escapeValue: false,
    },
  });

export default i18n;
