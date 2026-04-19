<template>
  <div class="coming-soon">
    <div class="placeholder-card">
      <el-icon :size="48" color="var(--color-stone-gray)">
        <component :is="icon" />
      </el-icon>
      <h3>{{ title }}</h3>
      <p>功能开发中，敬请期待</p>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string
}>()

const icon = 'Tools'
</script>

<style scoped>
.coming-soon {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
}

.placeholder-card {
  background: var(--color-ivory);
  border: 1px solid var(--color-border-cream);
  border-radius: var(--radius-featured);
  padding: var(--space-30) var(--space-30);
  text-align: center;
  box-shadow: var(--shadow-whisper);
}

.placeholder-card h3 {
  font-family: var(--font-serif);
  font-size: var(--text-h2);
  font-weight: 500;
  color: var(--color-near-black);
  margin: var(--space-16) 0 var(--space-8);
}

.placeholder-card p {
  font-size: var(--text-caption);
  color: var(--color-stone-gray);
}
</style>
