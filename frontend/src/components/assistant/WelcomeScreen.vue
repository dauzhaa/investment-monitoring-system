<template>
  <div class="welcome-wrap d-flex flex-column align-center">
    <v-avatar size="56" color="blue-lighten-5" class="mb-2">
      <v-icon size="34" color="primary">mdi-robot-outline</v-icon>
    </v-avatar>
    <h2 class="welcome-title text-center">AI-Аналитик: Чем могу помочь?</h2>
    <p class="welcome-subtitle text-center">
      Делаю SQL-запросы к базе ИнвестМонитор72 и строю графики.
      Выберите готовый запрос или напишите свой.
    </p>

    <div class="sug-grid">
      <button
        v-for="sug in suggestions"
        :key="sug.text"
        type="button"
        class="sug-card"
        @click="$emit('suggestion', sug.text)"
      >
        <div class="sug-emoji">{{ sug.emoji }}</div>
        <div class="sug-title">{{ sug.title }}</div>
        <div class="sug-text">{{ sug.text }}</div>
      </button>
    </div>
  </div>
</template>

<script setup>
const suggestions = [
  { emoji: '🚨', title: 'Зона риска', text: 'Покажи список организаций в зоне риска по ИПО за 2024 год.' },
  { emoji: '🏆', title: 'Лидеры', text: 'Кто лидер по объёму освоенных инвестиций в Тюменском районе?' },
  { emoji: '⚖️', title: 'Сравнение', text: 'Сравни дисциплину сдачи отчётов между ВУЗами и медорганизациями.' },
  { emoji: '👥', title: 'Поиск двойников', text: 'Найди «двойников» для ГБУЗ ТО «ОКБ №1» по размеру плана и профилю.' },
  { emoji: '📈', title: 'Динамика', text: 'Выведи график динамики инвестиций для Тобольска по кварталам.' },
  { emoji: '🕳️', title: 'Разрыв плана', text: 'У каких организаций самый большой разрыв между планом и фактом в этом квартале?' },
  { emoji: '📊', title: 'Рейтинг районов', text: 'Сформируй рейтинг топ-5 и анти-топ-5 районов по качеству отчётности.' },
  { emoji: '🗺️', title: 'Локализация проблем', text: 'В каких районах сконцентрированы проблемные объекты (ИПО ниже 40%)?' },
  { emoji: '🧩', title: 'Матрица', text: 'Покажи матрицу «Дисциплина-Исполнение» для подведомственных учреждений.' },
  { emoji: '🔮', title: 'Прогноз', text: 'Сделай прогноз рисков неосвоения бюджета до конца 2025 года.' }
]
</script>

<style scoped>
.welcome-wrap {
  width: 100%;
  max-width: 1500px;
  margin: 0 auto;          /* центрирование внутри контентной области (справа от sidebar) */
  padding: 12px 24px;
}
.welcome-title {
  font-size: 2rem;
  font-weight: 800;
  color: #14304D;
  margin-bottom: 6px;
}
.welcome-subtitle {
  font-size: 1.05rem;
  font-weight: 500;
  color: #2B3A4A;          /* тёмный вместо серого — читается на проекторе */
  max-width: 760px;
  line-height: 1.4;
  margin-bottom: 18px;
}

/* Сетка 5×2 — без «висящих» карточек, минимум пустот */
.sug-grid {
  width: 100%;
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 14px;
}
.sug-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 16px 12px;
  border: 1.5px solid #C7D2DD;
  border-radius: 16px;
  background: #fff;
  cursor: pointer;
  transition: all .15s ease;
}
.sug-card:hover {
  border-color: #1B3A5C;
  box-shadow: 0 6px 18px rgba(27, 58, 92, .18);
  transform: translateY(-2px);
}
.sug-emoji { font-size: 1.9rem; line-height: 1; margin-bottom: 6px; }
.sug-title {
  font-size: 1.05rem;
  font-weight: 700;
  color: #14304D;
  margin-bottom: 4px;
}
.sug-text {
  font-size: .9rem;
  font-weight: 500;
  color: #33414F;          /* контрастный, не серый */
  line-height: 1.25;
}

/* Адаптив, если проектор/окно уже */
@media (max-width: 1280px) { .sug-grid { grid-template-columns: repeat(4, 1fr); } }
@media (max-width: 960px)  { .sug-grid { grid-template-columns: repeat(3, 1fr); } }
@media (max-width: 600px)  { .sug-grid { grid-template-columns: repeat(2, 1fr); } }
</style>