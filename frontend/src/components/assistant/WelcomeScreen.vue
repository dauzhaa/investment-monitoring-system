<template>
  <div class="d-flex flex-column align-center justify-center mt-10">
    <v-avatar size="64" color="blue-lighten-5" class="mb-4">
      <v-icon size="36" color="primary">mdi-finance</v-icon>
    </v-avatar>
    <h2 class="text-h5 font-weight-bold mb-2">Чем могу помочь сегодня?</h2>
    <p class="text-body-1 text-grey mb-8 text-center" style="max-width: 500px;">
      Я имею прямой доступ к базе данных ИнвестМонитор72. Спрашивайте о рейтингах, проблемных зонах и динамике ИПО.
    </p>

    <v-row class="w-100" justify="center">
      <v-col cols="12" sm="6" v-for="sug in suggestions" :key="sug.text">
        <v-card variant="outlined" hover class="h-100 rounded-lg" @click="$emit('suggestion', sug.text)">
          <v-card-text class="d-flex align-start pa-3">
            <div class="text-h6 mr-3">{{ sug.emoji }}</div>
            <div>
              <div class="font-weight-bold text-body-2 text-grey-darken-3">{{ sug.title }}</div>
              <div class="text-caption text-grey">{{ sug.text }}</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script setup>
const suggestions = [
  { emoji: '📊', title: 'Рейтинги', text: 'Покажи топ-5 районов по ИПО за 2024 год' },
  { emoji: '⚠️', title: 'Аномалии', text: 'Кто хронически не осваивает план?' },
  { emoji: '⚖️', title: 'Сравнение', text: 'Сравни показатели Тюмени и Тобольска' },
  { emoji: '📉', title: 'Глубокий анализ', text: 'Что не так с Голышмановским районом?' }
]
</script>