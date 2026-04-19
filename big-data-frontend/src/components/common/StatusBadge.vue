<template>
  <span class="status-badge" :style="{ backgroundColor: bg, color: fg }">
    {{ label }}
  </span>
</template>

<script setup lang="ts">
const props = defineProps<{
  status: string
}>()

const labelMap: Record<string, string> = {
  pending: '待解析',
  processing: '解析中',
  completed: '已完成',
  failed: '失败',
}

const colorMap: Record<string, { bg: string; fg: string }> = {
  pending: { bg: 'rgba(201,100,66,0.10)', fg: 'var(--color-terracotta)' },
  processing: { bg: 'rgba(201,100,66,0.10)', fg: 'var(--color-terracotta)' },
  completed: { bg: 'rgba(107,143,60,0.10)', fg: 'var(--color-success)' },
  failed: { bg: 'rgba(181,51,51,0.10)', fg: 'var(--color-error)' },
}

const label = labelMap[props.status] || props.status
const colors = colorMap[props.status] || { bg: 'rgba(94,93,89,0.08)', fg: 'var(--color-stone-gray)' }
const bg = colors.bg
const fg = colors.fg
</script>

<style scoped>
.status-badge {
  display: inline-block;
  padding: 1px 8px;
  border-radius: 10px;
  font-family: var(--font-sans);
  font-size: 11px;
  font-weight: 500;
  line-height: 1.5;
  letter-spacing: 0.01em;
}
</style>
