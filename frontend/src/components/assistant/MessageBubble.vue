<template>
  <div class="d-flex w-100 mb-4" :class="message.role === 'user' ? 'justify-end' : 'justify-start'">
    <v-avatar v-if="message.role === 'assistant'" size="42" color="blue-lighten-5" class="mr-3 mt-1 shadow-sm">
      <v-icon size="24" color="primary">mdi-robot-outline</v-icon>
    </v-avatar>
    
    <div 
      class="message-bubble pa-4" 
      :class="message.role === 'user' ? 'bg-primary text-white rounded-xl rounded-tr-0' : 'bg-white border rounded-xl rounded-tl-0 content-bot-align'"
      style="max-width: 82%; box-shadow: 0 2px 8px rgba(0,0,0,0.05);"
    >
      <div v-if="message.tool_calls && message.tool_calls.length" class="mb-3 w-100">
        <v-expansion-panels variant="accordion" class="border rounded-lg bg-grey-lighten-5">
          <v-expansion-panel v-for="(tool, idx) in message.tool_calls" :key="idx" elevation="0">
            <v-expansion-panel-title class="py-2 px-3 min-h-0 text-subtitle-2 font-weight-bold text-grey-darken-3">
              <v-icon start size="18" color="primary">mdi-code-json</v-icon> 
              Системный вызов: {{ tool.name }}(...)
            </v-expansion-panel-title>
            <v-expansion-panel-text class="text-caption px-3 pb-3 bg-grey-lighten-4">
              <pre class="overflow-x-auto text-grey-darken-3"><code>{{ JSON.stringify(tool.result, null, 2) }}</code></pre>
            </v-expansion-panel-text>
          </v-expansion-panel>
        </v-expansion-panels>
        <div class="mt-4">
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
/* Кастомизация рендеринга текста ИИ под требования проектора */
.text-projector-ready {
  font-size: 1.25rem !important; /* Значительно увеличенный шрифт */
  line-height: 1.6 !important;
  font-weight: 500;
}

.content-bot-align {
  background-color: #F8FAFC !important;
  border-color: #E2E8F0 !important;
}

/* Стили разметки Markdown внутри баббла. Убран глобальный text-align: center */
:deep(.markdown-body) {
  text-align: left !important; /* Ровный левый край текста ответа */
  color: #1E293B;
}

:deep(.markdown-body p) { 
  margin-bottom: 12px; 
}

:deep(.markdown-body ul), :deep(.markdown-body ol) { 
  margin-left: 24px; 
  margin-bottom: 12px; 
  text-align: left !important;
}

:deep(.markdown-body li) {
  margin-bottom: 4px;
}

:deep(.markdown-body pre) { 
  background: #0F172A; 
  color: #F8FAFC;
  padding: 12px; 
  border-radius: 8px; 
  overflow-x: auto; 
  font-size: 14px;
}
</style>