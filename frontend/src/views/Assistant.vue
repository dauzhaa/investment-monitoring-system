<template>
  <v-container fluid class="pa-0 d-flex flex-column bg-grey-lighten-4" style="height: 100vh;">
    <!-- Хедер -->
    <v-app-bar flat color="white" border="bottom">
      <v-btn v-if="messages.length > 0" icon="mdi-arrow-left" color="primary" class="ml-2 mr-2" @click="clearChat"></v-btn>
      <v-icon v-else color="primary" class="mr-3 ml-4">mdi-robot-outline</v-icon>
      
      <v-toolbar-title class="font-weight-bold text-subtitle-1">
        AI-Аналитик ИнвестМонитор72
      </v-toolbar-title>
      <v-spacer></v-spacer>
      <v-btn variant="text" color="grey-darken-1" @click="clearChat" v-if="messages.length > 0">
        <v-icon start>mdi-broom</v-icon> Очистить
      </v-btn>
    </v-app-bar>

    <!-- Область чата -->
    <v-main class="flex-grow-1 overflow-y-auto" ref="messagesArea">
      <v-container class="pa-4" style="max-width: 900px;">
        
        <!-- Приветственный экран -->
        <WelcomeScreen v-if="messages.length === 0" @suggestion="sendMessage" />

        <!-- Сообщения -->
        <div v-else class="d-flex flex-column gap-4">
          <MessageBubble
            v-for="(msg, idx) in messages"
            :key="idx"
            :message="msg"
          />
          
          <!-- Индикатор загрузки -->
          <div v-if="isThinking" class="d-flex align-center text-grey mt-2">
            <v-progress-circular indeterminate size="20" width="2" color="primary" class="mr-3"></v-progress-circular>
            <span class="text-body-2">Анализирую данные...</span>
          </div>

          <!-- Follow-up вопросы -->
          <FollowUpSuggestions 
            v-if="!isThinking && followUps.length" 
            :suggestions="followUps" 
            @select="sendMessage" 
          />
        </div>
      </v-container>
    </v-main>

    <!-- Подвал с вводом -->
    <v-footer app color="transparent" class="pa-0 border-t bg-white">
      <v-container style="max-width: 900px;" class="py-3 px-4">
        <ChatInput 
          v-model="input" 
          :disabled="isThinking" 
          :tokens-used="tokensUsed"
          @send="sendMessage" 
        />
      </v-container>
    </v-footer>
  </v-container>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import WelcomeScreen from '@/components/assistant/WelcomeScreen.vue'
import MessageBubble from '@/components/assistant/MessageBubble.vue'
import ChatInput from '@/components/assistant/ChatInput.vue'
import FollowUpSuggestions from '@/components/assistant/FollowUpSuggestions.vue'
import axios from 'axios'

const messages = ref([])
const input = ref('')
const isThinking = ref(false)
const tokensUsed = ref(0)
const followUps = ref([])
const messagesArea = ref(null)

const scrollToBottom = async () => {
  await nextTick()
  if (messagesArea.value) {
    const el = messagesArea.value.$el || messagesArea.value
    el.scrollTop = el.scrollHeight
  }
}

const sendMessage = async (text) => {
  if (!text.trim() || isThinking.value) return
  
  // Добавляем сообщение пользователя в UI
  messages.value.push({ role: 'user', content: text })
  input.value = ''
  isThinking.value = true
  followUps.value = [] // Скрываем старые подсказки пока идет загрузка
  await scrollToBottom()

  try {
    // 1. Подготавливаем историю диалога для бэкенда.
    // Pydantic схема ждет только role и content, поэтому отсекаем лишнее (например, tool_calls).
    const apiMessages = messages.value.map(m => ({
      role: m.role,
      content: m.content || ''
    }))

    // 2. Отправляем реальный запрос на эндпоинт бота
    const response = await axios.post('/api/v1/bot/chat', {
      messages: apiMessages
    })

    const data = response.data

    // 3. Сохраняем ответ ассистента в UI
    messages.value.push({
      role: 'assistant',
      content: data.answer || '', // Поле answer берется из твоего bot.py
      // Если в будущем бэкенд научится отдавать tool_calls напрямую массивом — фронт их подхватит
      tool_calls: data.tool_calls || [] 
    })

    // (Опционально) Если бэкенд начнет отдавать эти поля, фронт обновит счетчики и кнопки:
    if (data.tokens_used) tokensUsed.value += data.tokens_used
    if (data.followUps) followUps.value = data.followUps

  } catch (error) {
    console.error('Ошибка при обращении к ИИ:', error)
    messages.value.push({ 
      role: 'assistant', 
      content: '❌ Произошла ошибка при обращении к серверу. Пожалуйста, проверьте подключение или логи бэкенда.' 
    })
  } finally {
    isThinking.value = false
    await scrollToBottom()
  }
}

const clearChat = () => {
  messages.value = []
  followUps.value = []
}
</script>

<style scoped>
.gap-4 { gap: 16px; }
</style>