<template>
  <button class="btn-primary" :disabled="disabled" @click="$emit('click')">
    <el-icon v-if="icon" :size="16"><component :is="icon" /></el-icon>
    <slot />
  </button>
</template>

<script setup lang="ts">
defineProps<{
  disabled?: boolean
  icon?: string
}>()

defineEmits(['click'])
</script>

<style scoped>
.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: var(--space-6);
  padding: var(--space-8) var(--space-16) var(--space-8) var(--space-12);
  background: var(--color-terracotta);
  color: var(--color-ivory);
  border: 1px solid var(--color-terracotta);
  border-radius: var(--radius-comfort);
  font-family: var(--font-sans);
  font-size: var(--text-small);
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
}

.btn-primary:hover:not(:disabled) {
  background: var(--color-coral);
  border-color: var(--color-coral);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
