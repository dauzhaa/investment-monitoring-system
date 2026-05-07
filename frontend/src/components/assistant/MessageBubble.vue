<template>
  <div class="d-flex w-100" :class="message.role === 'user' ? 'justify-end' : 'justify-start'">
    
    <!-- Аватар Бота -->
    <v-avatar v-if="message.role === 'assistant'" size="36" color="blue-lighten-5" class="mr-3 mt-1">
      <v-icon size="20" color="primary">mdi-robot-outline</v-icon>
    </v-avatar>

    <!-- Баббл сообщения -->
    <div 
      class="message-bubble pa-4 rounded-xl" 
      :class="message.role === 'user' ? 'bg-primary text-white rounded-tr-0' : 'bg-white border rounded-tl-0'"
      style="max-width: 85%;"
    >
      <!-- Блок с функциями (Tool Calls) -->
      <div v-if="message.tool_calls && message.tool_calls.length" class="mb-3">
        <v-expansion-panels variant="accordion" class="border rounded-lg bg-grey-lighten-5">
          <v-expansion-panel v-for="(tool, idx) in message.tool_calls" :key="idx" elevation="0">
            <v-expansion-panel-title class="py-1 px-3 min-h-0 text-caption font-weight-medium text-grey-darken-2">
              <v-icon start size="16">mdi-code-json</v-icon> 
              ▸ Вызов: {{ tool.name }}(...)
            </v-expansion-panel-title>
            <v-expansion-panel-text class="text-caption px-3 pb-3 bg-grey-lighten-4">
              <pre class="overflow-x-auto text-grey-darken-3"><code>{{ JSON.stringify(tool.result, null, 2) }}</code></pre>
            </v-expansion-panel-text>
          </v-expansion-panel>
        </v-expansion-panels>

        <!-- Inline Рендереры для графиков -->
        <div class="mt-4">
          <ToolResultRenderer 
            v-for="(tool, idx) in message.tool_calls" 
            :key="'render-'+idx" 
            :tool-name="tool.name" 
            :result="tool.result" 
          />
        </div>
      </div>

      <!-- Текст сообщения (Markdown) -->
      <div v-if="message.content" class="markdown-body text-body-1" v-html="renderedContent"></div>
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

<style>
/* Немного стилей для Markdown внутри баббла */
.markdown-body p { margin-bottom: 8px; }
.markdown-body ul, .markdown-body ol { margin-left: 20px; margin-bottom: 8px; }
.markdown-body pre { background: #f5f5f5; padding: 8px; border-radius: 4px; overflow-x: auto; }
</style>