<template>
  <div class="markdown-body" v-html="rendered" />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { marked } from 'marked'

const props = defineProps<{ content: string }>()

const rendered = computed(() => marked.parse(props.content, { breaks: true }) as string)
</script>

<style scoped>
.markdown-body :deep(pre) {
  background: #2d2016;
  color: #f0e6d8;
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
}
.markdown-body :deep(code) {
  background: rgba(0, 0, 0, 0.15);
  padding: 2px 4px;
  border-radius: 3px;
  font-size: 0.9em;
}
.markdown-body :deep(pre code) {
  background: transparent;
  padding: 0;
}
.markdown-body :deep(p) {
  margin: 8px 0;
}
.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  padding-left: 20px;
  margin: 8px 0;
}
.markdown-body :deep(blockquote) {
  border-left: 3px solid var(--primary-color, #c4704f);
  padding-left: 12px;
  color: var(--text-secondary, #6b5744);
  margin: 8px 0;
}
</style>
