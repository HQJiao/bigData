<template>
  <div class="document-detail">
    <div v-if="store.loading" class="loading-state">
      <el-icon class="is-loading" :size="24"><Loading /></el-icon>
      <p>加载中...</p>
    </div>

    <template v-else-if="store.currentDocument">
      <!-- Document Header -->
      <div class="doc-header">
        <div>
          <h1 class="doc-title">{{ store.currentDocument.filename }}</h1>
          <div class="doc-meta">
            <StatusBadge :status="store.currentDocument.status" />
            <span v-if="store.currentDocument.parser_type" class="parser-type">
              {{ store.currentDocument.parser_type }}
            </span>
            <span v-if="store.currentDocument.file_size" class="file-size">
              {{ formatSize(store.currentDocument.file_size) }}
            </span>
          </div>
        </div>
        <router-link to="/documents" class="back-link">
          <el-icon :size="16"><ArrowLeft /></el-icon>
          返回列表
        </router-link>
      </div>

      <!-- Pending / Processing -->
      <div v-if="store.currentDocument.status === 'pending' || store.currentDocument.status === 'processing'" class="status-card">
        <el-icon :size="32" color="var(--color-terracotta)"><Loading /></el-icon>
        <h3>文档解析中</h3>
        <p>请稍后刷新查看结果</p>
        <PrimaryButton @click="refresh" :icon="'Refresh'">刷新</PrimaryButton>
      </div>

      <!-- Failed -->
      <div v-else-if="store.currentDocument.status === 'failed'" class="status-card error-card">
        <el-icon :size="32" color="var(--color-error)"><CircleCloseFilled /></el-icon>
        <h3>解析失败</h3>
        <p>{{ store.currentDocument.error_message || '未知错误' }}</p>
      </div>

      <!-- Completed — Editor -->
      <div v-else class="editor-section">
        <div class="toolbar">
          <PrimaryButton @click="save" :disabled="saving">
            {{ saving ? '保存中...' : '保存' }}
          </PrimaryButton>
          <SecondaryButton @click="download" icon="Download">下载 .txt</SecondaryButton>
          <span v-if="saved" class="saved-hint">已保存</span>
          <span v-if="charCount !== null" class="char-count">{{ charCount.toLocaleString() }} 字符</span>
        </div>
        <textarea
          v-model="content"
          class="content-editor"
          placeholder="文档内容将显示在这里..."
          @input="updateCharCount"
        ></textarea>
      </div>
    </template>

    <!-- Not Found -->
    <div v-else class="not-found">
      <el-empty description="文档不存在" :image-size="120">
        <router-link to="/documents">
          <PrimaryButton>返回列表</PrimaryButton>
        </router-link>
      </el-empty>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useDocumentStore } from '../stores/documents'
import api from '../api'
import { Loading, ArrowLeft, CircleCloseFilled } from '@element-plus/icons-vue'
import StatusBadge from '../components/common/StatusBadge.vue'
import PrimaryButton from '../components/common/PrimaryButton.vue'
import SecondaryButton from '../components/common/SecondaryButton.vue'

const route = useRoute()
const store = useDocumentStore()
const content = ref('')
const saving = ref(false)
const saved = ref(false)
const charCount = ref<number | null>(null)

watch(
  () => route.params.id,
  (id) => {
    if (id) loadDocument(String(id))
  },
  { immediate: true }
)

async function loadDocument(id: string) {
  await store.fetchDocument(id)
  content.value = store.currentDocument?.content || ''
  updateCharCount()
}

function refresh() {
  loadDocument(String(route.params.id))
}

async function save() {
  if (!store.currentDocument) return
  saving.value = true
  saved.value = false
  try {
    await store.saveContent(store.currentDocument.id, content.value)
    saved.value = true
    setTimeout(() => { saved.value = false }, 2000)
  } catch {
    alert('保存失败')
  } finally {
    saving.value = false
  }
}

function updateCharCount() {
  charCount.value = content.value.length
}

async function download() {
  const id = store.currentDocument?.id
  if (!id) return
  const { data } = await api.get(`/files/${id}/content`, { responseType: 'blob' })
  const url = window.URL.createObjectURL(new Blob([data]))
  const a = document.createElement('a')
  a.href = url
  a.download = store.currentDocument!.filename.replace(/\.[^.]+$/, '') + '.txt'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  window.URL.revokeObjectURL(url)
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}
</script>

<style scoped>
.document-detail {
  max-width: 860px;
  margin: 0 auto;
}

.loading-state {
  text-align: center;
  padding: var(--space-30);
  color: var(--color-olive-gray);
}

.loading-state p {
  margin-top: var(--space-8);
  font-size: var(--text-small);
}

/* Document Header */
.doc-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--space-24);
  gap: var(--space-16);
}

.doc-title {
  font-family: var(--font-serif);
  font-size: var(--text-h1);
  font-weight: 500;
  color: var(--color-near-black);
  word-break: break-word;
  line-height: var(--lh-heading);
}

.doc-meta {
  display: flex;
  align-items: center;
  gap: var(--space-12);
  margin-top: var(--space-8);
}

.parser-type,
.file-size {
  font-size: var(--text-caption);
  color: var(--color-stone-gray);
}

.back-link {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  font-size: var(--text-small);
  color: var(--color-olive-gray);
  flex-shrink: 0;
  padding: var(--space-6) var(--space-12);
  border-radius: var(--radius-comfort);
  transition: color 0.15s, background 0.15s;
}

.back-link:hover {
  color: var(--color-terracotta);
  background: rgba(201, 100, 66, 0.06);
}

/* Status Cards */
.status-card {
  background: var(--color-ivory);
  border: 1px solid var(--color-border-cream);
  border-radius: var(--radius-featured);
  padding: var(--space-30);
  text-align: center;
  box-shadow: var(--shadow-whisper);
}

.status-card h3 {
  font-family: var(--font-serif);
  font-size: var(--text-h2);
  font-weight: 500;
  color: var(--color-near-black);
  margin: var(--space-12) 0 var(--space-8);
}

.status-card p {
  font-size: var(--text-small);
  color: var(--color-olive-gray);
  margin-bottom: var(--space-20);
}

.error-card {
  border-color: rgba(181, 51, 51, 0.2);
}

.error-card p {
  color: var(--color-error);
}

/* Editor */
.editor-section {
  background: var(--color-ivory);
  border: 1px solid var(--color-border-cream);
  border-radius: var(--radius-featured);
  padding: var(--space-24);
  box-shadow: var(--shadow-whisper);
}

.toolbar {
  display: flex;
  align-items: center;
  gap: var(--space-12);
  margin-bottom: var(--space-16);
  flex-wrap: wrap;
}

.saved-hint {
  font-size: var(--text-caption);
  color: var(--color-success);
}

.char-count {
  margin-left: auto;
  font-size: var(--text-caption);
  color: var(--color-stone-gray);
}

.content-editor {
  width: 100%;
  min-height: 480px;
  padding: var(--space-16);
  font-family: var(--font-mono);
  font-size: var(--text-small);
  line-height: var(--lh-relaxed);
  color: var(--color-near-black);
  background: var(--color-parchment);
  border: 1px solid var(--color-border-warm);
  border-radius: var(--radius-comfort);
  resize: vertical;
  transition: border-color 0.15s;
}

.content-editor:focus {
  outline: none;
  border-color: var(--color-focus-blue);
}

.content-editor::placeholder {
  color: var(--color-stone-gray);
}

/* Not Found */
.not-found {
  text-align: center;
  padding: var(--space-30);
}
</style>
