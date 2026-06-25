<template>
  <div class="d-flex w-100 mb-6" :class="message.role === 'user' ? 'justify-end' : 'justify-start'">
    <v-avatar v-if="message.role === 'assistant'" size="54" color="blue-lighten-5" class="mr-4 mt-1 shadow-sm border">
      <v-icon size="32" color="primary">mdi-robot-outline</v-icon>
    </v-avatar>
    
    <div 
      class="message-bubble pa-6" 
      :class="message.role === 'user' ? 'bg-primary text-white rounded-xl rounded-tr-0' : 'bg-white border-md rounded-xl rounded-tl-0 content-bot-align'"
      style="max-width: 95%; box-shadow: 0 4px 16px rgba(0,0,0,0.08);"
    >
      <div v-if="message.tool_calls && message.tool_calls.length" class="mb-4 w-100">
        <v-expansion-panels variant="accordion" class="border rounded-lg bg-grey-lighten-5">
          <v-expansion-panel v-for="(tool, idx) in message.tool_calls" :key="idx" elevation="0">
            <v-expansion-panel-title class="py-3 px-4 min-h-0 text-subtitle-1 font-weight-bold text-grey-darken-4">
              <v-icon start size="22" color="primary">mdi-code-json</v-icon> 
              Системный вызов: {{ tool.name }}(...)
            </v-expansion-panel-title>
            <v-expansion-panel-text class="text-body-1 px-4 pb-4 bg-grey-lighten-4">
              <pre class="overflow-x-auto text-grey-darken-4"><code>{{ JSON.stringify(tool.result, null, 2) }}</code></pre>
            </v-expansion-panel-text>
          </v-expansion-panel>
        </v-expansion-panels>
        <div class="mt-6">
          <ToolResultRenderer 
            v-for="(tool, idx) in message.tool_calls" 
            :key="'render-'+idx" 
            :tool-name="tool.name" 
            :result="tool.result" 
          />
        </div>
      </div>

      <div v-if="message.content" class="markdown-body text-projector-ready" v-html="renderedContent"></div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import ToolResultRenderer from './ToolResultRenderer.vue'

const props = defineProps({
  message: Object
})

const renderedContent = computed(() => {
  if (!props.message.content) return ''
  const rawHtml = marked.parse(props.message.content)
  return DOMPurify.sanitize(rawHtml)
})
</script>

<style scoped>
/* Ультра-контрастные стили для мыльного проектора */
.text-projector-ready {
  font-size: 24px !important; /* Огромный шрифт */
  line-height: 1.6 !important;
  font-weight: 500 !important;
  color: #000000 !important; /* Строго черный цвет текста */
}

.content-bot-align {
  background-color: #FFFFFF !important;
  border: 2px solid #CBD5E1 !important; /* Утолщенная рамка для контраста баббла */
}

:deep(.markdown-body) {
  text-align: left !important;
  color: #000000 !important;
  width: 100%;
}

:deep(.markdown-body p) { 
  margin-bottom: 20px; 
}

/* Списки делаем отбивкой, чтобы не слипались */
:deep(.markdown-body ul), :deep(.markdown-body ol) { 
  margin-left: 32px; 
  margin-bottom: 20px; 
  text-align: left !important;
}

:deep(.markdown-body li) {
  margin-bottom: 12px;
}

/* Делаем жирный текст ГИПЕР-заметным */
:deep(.markdown-body strong), :deep(.markdown-body b) {
  font-weight: 900 !important;
  color: #000000 !important;
  background-color: #E3F2FD; /* Легкий синий фон для подсветки на проекторе */
  padding: 2px 8px;
  border-radius: 6px;
}

:deep(.markdown-body pre) { 
  background: #0F172A; 
  color: #F8FAFC;
  padding: 16px; 
  border-radius: 8px; 
  overflow-x: auto; 
  font-size: 18px;
}
</style>