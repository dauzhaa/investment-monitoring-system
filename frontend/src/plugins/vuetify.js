import 'vuetify/styles';
import { createVuetify } from 'vuetify';
import * as components from 'vuetify/components';
import * as directives from 'vuetify/directives';
import '@mdi/font/css/materialdesignicons.css';
import { ru } from 'vuetify/locale'; // ИСПРАВЛЕНО: Импорт локали

const myCustomTheme = {
  dark: false,
  colors: {
    primary: '#1B3A5C',
    success: '#2E7D32',
    warning: '#F57C00',
    error: '#D32F2F',
    background: '#F5F7FA',
  }
}

export default createVuetify({
  components,
  directives,
  locale: { // ИСПРАВЛЕНО: Установка русского языка
    locale: 'ru',
    messages: { ru },
  },
  theme: {
    defaultTheme: 'myCustomTheme',
    themes: {
      myCustomTheme,
    }
  },
  icons: {
    defaultSet: 'mdi',
  },
});