<template>
  <v-container fluid class="pa-0 d-flex flex-column bg-grey-lighten-4" style="height: 100vh;">
    <!-- Хедер -->
    <v-app-bar flat color="white" border="bottom">
      <v-icon color="primary" class="mr-3 ml-4">mdi-robot-outline</v-icon>
      <v-toolbar-title class="font-weight-bold text-subtitle-1">
        AI-Аналитик ИнвестМонитор72
      </v-toolbar-title>
      <v-spacer></v-spacer>
      <v-btn variant="text" color="grey-darken-1" @click="clearChat">
        <v-icon start>mdi-broom</v-icon> Очистить диалог
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
// Заглушка для axios
import axios from 'axios'

const messages = ref([])
const input = ref('')
const isThinking = ref(false)
const tokensUsed = ref(150) // Для демо счетчика
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
  
  // Добавляем сообщение пользователя
  messages.value.push({ role: 'user', content: text })
  input.value = ''
  isThinking.value = true
  followUps.value = []
  await scrollToBottom()

  try {
    // В реальном проекте тут axios.post('/api/v1/bot/chat')
    // Для разработки симулируем ответ с function calling:
    setTimeout(async () => {
      messages.value.push({
        role: 'assistant',
        content: 'Видна тенденция: первые места — крупные городские округа. Заводоуковский — единственный некрупный район в топе.',
        tool_calls: [
          {
            name: 'get_top_organizations',
            arguments: { year: 2024 },
            result: {
              year: 2024,
              items: [
                { name: 'Тюмень г.', ipo: 78.4 },
                { name: 'Тюменский', ipo: 74.1 },
                { name: 'Заводоуковский', ipo: 72.8 },
                { name: 'Тобольск г.', ipo: 71.2 },
                { name: 'Ишим г.', ipo: 69.5 }
              ]
            }
          }
        ]
      })
      tokensUsed.value += 124 // симуляция
      followUps.value = ["А кто на последних местах?", "Покажи разброс ИПО внутри Тюмени"]
      isThinking.value = false
      await scrollToBottom()
    }, 1500)
  } catch (error) {
    isThinking.value = false
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