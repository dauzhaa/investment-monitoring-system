<template>
  <div class="d-flex flex-column align-center justify-center mt-10">
    <v-avatar size="64" color="blue-lighten-5" class="mb-4">
      <v-icon size="36" color="primary">mdi-robot-outline</v-icon>
    </v-avatar>
    <h2 class="text-h5 font-weight-bold mb-2">AI-Аналитик: Чем могу помочь?</h2>
    <p class="text-body-1 text-grey mb-6 text-center" style="max-width: 600px;">
      Я умею делать SQL-запросы к базе данных ИнвестМонитор72 и строить графики. 
      Выберите один из популярных запросов или напишите свой.
    </p>

    <v-row class="w-100" justify="center">
      <v-col cols="12" md="6" v-for="sug in suggestions" :key="sug.text">
        <v-card variant="outlined" hover class="h-100 rounded-lg border-opacity-50" @click="$emit('suggestion', sug.text)">
          <v-card-text class="d-flex align-center pa-3">
            <div class="text-h6 mr-3">{{ sug.emoji }}</div>
            <div>
              <div class="font-weight-bold text-body-2 text-grey-darken-3">{{ sug.title }}</div>
              <div class="text-caption text-grey mt-1" style="line-height: 1.2;">{{ sug.text }}</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script setup>
const suggestions = [
  { emoji: '🚨', title: 'Зона риска', text: 'Покажи список организаций в зоне риска по ИПО за 2024 год.' },
  { emoji: '🏆', title: 'Лидеры', text: 'Кто лидер по объему освоенных инвестиций в Тюменском районе?' },
  { emoji: '⚖️', title: 'Сравнение', text: 'Сравни дисциплину сдачи отчетов между ВУЗами и медорганизациями.' },
  { emoji: '👥', title: 'Поиск двойников', text: 'Найди «двойников» для ГБУЗ ТО «ОКБ №1» по размеру плана и профилю.' },
  { emoji: '📈', title: 'Динамика', text: 'Выведи график динамики инвестиций для Тобольска по кварталам.' },
  { emoji: '🕳️', title: 'Разрыв плана', text: 'У каких организаций самый большой разрыв между планом и фактом в этом квартале?' },
  { emoji: '📊', title: 'Рейтинг районов', text: 'Сформируй рейтинг топ-5 и анти-топ 5 районов по качеству отчетности.' },
  { emoji: '🗺️', title: 'Локализация проблем', text: 'В каких районах сконцентрированы проблемные объекты (ИПО ниже 40%)?' },
  { emoji: '🧩', title: 'Матрица', text: 'Покажи матрицу «Дисциплина-Исполнение» для подведомственных учреждений.' },
  { emoji: '🔮', title: 'Прогноз', text: 'Сделай прогноз рисков неосвоения бюджета до конца 2025 года на основе текущих данных.' }
]
</script>