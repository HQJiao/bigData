<template>
  <el-tag :type="tagType" size="small" class="status-badge">
    {{ label }}
  </el-tag>
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

const typeMap: Record<string, 'success' | 'warning' | 'danger' | 'info'> = {
  pending: 'warning',
  processing: 'warning',
  completed: 'success',
  failed: 'danger',
}

const label = labelMap[props.status] || props.status
const tagType = typeMap[props.status] || 'info'
</script>

<style scoped>
.status-badge {
  font-family: var(--font-sans);
  border-radius: var(--radius-subtle);
}
</style>
