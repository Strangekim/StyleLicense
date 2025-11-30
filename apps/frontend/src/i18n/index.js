import { createI18n } from 'vue-i18n'
import en from '../locales/en.json'
import ko from '../locales/ko.json'

const i18n = createI18n({
  legacy: false, // Use Composition API mode
  locale: 'en', // Default locale
  fallbackLocale: 'en',
  messages: {
    en,
    ko,
  },
  // Disable strict message format checking
  messageCompiler: undefined,
  warnHtmlMessage: false,
  escapeParameter: false,
})

export default i18n
