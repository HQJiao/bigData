<template>
  <button class="btn-secondary" :disabled="disabled" @click="$emit('click')">
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
.btn-secondary {
  display: inline-flex;
  align-items: center;
  gap: var(--space-6);
  padding: var(--space-8) var(--space-16) var(--space-8) var(--space-12);
  background: var(--color-warm-sand);
  color: var(--color-charcoal);
  border: none;
  border-radius: var(--radius-comfort);
  box-shadow: 0px 0px 0px 1px var(--color-ring-warm);
  font-family: var(--font-sans);
  font-size: var(--text-small);
  cursor: pointer;
  transition: background 0.15s, box-shadow 0.15s;
}

.btn-secondary:hover:not(:disabled) {
  background: var(--color-border-warm);
  box-shadow: 0px 0px 0px 1px var(--color-ring-deep);
}

.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
