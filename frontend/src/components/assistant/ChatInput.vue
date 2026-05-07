<template>
  <div class="d-flex flex-column w-100">
    <v-textarea
      v-model="localValue"
      placeholder="Спросите об инвестициях, рейтингах или аналитике..."
      variant="outlined"
      density="comfortable"
      auto-grow
      rows="1"
      max-rows="5"
      hide-details
      :disabled="disabled"
      @keydown.enter.exact.prevent="handleSend"
    >
      <template #append-inner>
        <v-btn 
          icon="mdi-arrow-up" 
          variant="flat" 
          color="primary" 
          size="small" 
          :disabled="!localValue.trim() || disabled"
          @click="handleSend"
        ></v-btn>
      </template>
    </v-textarea>
    
    <div class="d-flex justify-space-between mt-1 px-1">
      <span class="text-caption text-grey">Используется GigaChat AI. Возможны неточности.</span>
      <span class="text-caption" :class="tokenColor">
        Лимит токенов: {{ tokensUsed }} / 10 000
      </span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: String,
  disabled: Boolean,
  tokensUsed: Number
})
const emit = defineEmits(['update:modelValue', 'send'])

const localValue = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const tokenColor = computed(() => {
  if (props.tokensUsed > 9000) return 'text-error'
  if (props.tokensUsed > 8000) return 'text-warning'
  return 'text-grey'
})

const handleSend = () => {
  emit('send', localValue.value)
}
</script>