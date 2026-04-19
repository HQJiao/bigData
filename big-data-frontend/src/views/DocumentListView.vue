<template>
  <div class="document-page">
    <!-- Upload Section -->
    <section class="upload-card">
      <h2 class="section-title">上传文档</h2>
      <p class="section-desc">将文档拖拽到下方区域，系统会自动解析并提取文本内容。</p>

      <div
        class="drop-zone"
        :class="{ dragging: isDragging }"
        @dragover.prevent="isDragging = true"
        @dragleave.prevent="isDragging = false"
        @drop.prevent="onDrop"
        @click="fileInputRef?.click()"
      >
        <input
          type="file"
          ref="fileInputRef"
          style="display: none"
          @change="onFileSelect"
          :multiple="true"
          accept=".docx,.xlsx,.xls,.csv,.pdf,.png,.jpg,.jpeg,.bmp,.eml,.msg,.txt,.md,.json,.xml,.yml,.yaml"
        />

        <div v-if="previewFiles.length === 0" class="drop-placeholder">
          <el-icon :size="36" color="var(--color-stone-gray)">
            <UploadFilled />
          </el-icon>
          <p class="drop-text">
            拖拽文件到此处，或 <span class="link-text">点击选择</span>
          </p>
          <p class="hint">
            支持 docx · xlsx · pdf · png · jpg · eml · msg · txt · md · json · xml · yml
          </p>
        </div>

        <div v-else class="file-preview-list">
          <div v-for="(f, i) in previewFiles" :key="i" class="file-preview-item">
            <el-icon :size="18" color="var(--color-terracotta)">
              <Document />
            </el-icon>
            <span class="file-name">{{ f.name }}</span>
            <span class="file-size">{{ formatSize(f.size) }}</span>
            <span v-if="uploadResults[i]" class="file-status">
              <span v-if="uploadResults[i].success" class="status-success">已上传</span>
              <span v-else-if="uploadResults[i].duplicate" class="status-duplicate">已存在</span>
              <span v-else class="status-error">失败</span>
            </span>
          </div>

          <!-- Upload All Button -->
          <div v-if="previewFiles.length > 1 && !uploading" class="upload-actions">
            <button class="upload-all-btn" @click.stop="uploadAll">
              全部上传 ({{ previewFiles.length }} 个文件)
            </button>
            <button class="clear-btn" @click.stop="clearPreview">清除</button>
          </div>

          <p v-if="previewFiles.length === 1 && !uploading" class="preview-hint">
            点击上传
          </p>
        </div>
      </div>

      <!-- Upload Progress -->
      <div v-if="uploading" class="upload-progress">
        <el-progress
          :percentage="uploadProgress"
          :stroke-width="4"
          :status="uploadProgress >= 100 ? 'success' : undefined"
        />
        <p class="upload-progress-text">正在上传 {{ uploadedCount }}/{{ previewFiles.length }}</p>
      </div>

      <!-- Upload Error -->
      <div v-if="uploadError" class="upload-error">
        <el-icon :size="18" color="var(--color-error)"><CircleCloseFilled /></el-icon>
        <span>{{ uploadError }}</span>
      </div>
    </section>

    <!-- Search / Filter Bar -->
    <section class="filter-bar">
      <el-input
        placeholder="搜索文件名..."
        v-model="searchQuery"
        :prefix-icon="Search"
        clearable
        class="search-input"
        size="default"
      />
      <div class="filter-group">
        <el-select v-model="statusFilter" placeholder="状态筛选" clearable size="default" class="filter-select">
          <el-option label="待解析" value="pending" />
          <el-option label="解析中" value="processing" />
          <el-option label="已完成" value="completed" />
          <el-option label="失败" value="failed" />
        </el-select>
        <el-select v-model="formatFilter" placeholder="格式筛选" clearable size="default" class="filter-select">
          <el-option label="Word" value="docx" />
          <el-option label="Excel" value="excel" />
          <el-option label="PDF" value="pdf" />
          <el-option label="图片" value="image" />
          <el-option label="邮件" value="email" />
          <el-option label="文本" value="text" />
        </el-select>
      </div>
    </section>

    <!-- Batch Operations Bar -->
    <section v-if="selectedIds.length > 0" class="batch-bar">
      <span class="selected-count">已选择 {{ selectedIds.length }} 个文件</span>
      <button class="batch-btn" @click="batchReparse">重新解析</button>
      <button class="batch-btn batch-btn-danger" @click="batchDelete">删除</button>
      <button class="batch-btn batch-btn-clear" @click="clearSelection">取消</button>
    </section>

    <!-- Document List -->
    <section class="list-section">
      <div v-if="store.loading" class="loading-state">
        <el-icon class="is-loading" :size="20"><Loading /></el-icon>
        <p>加载中...</p>
      </div>

      <div v-else-if="store.documents.length === 0" class="empty-state">
        <el-empty description="暂无文档" :image-size="100" />
      </div>

      <div v-else class="document-list">
        <div
          v-for="doc in paginatedDocuments"
          :key="doc.id"
          class="document-card"
          :class="{ selected: selectedIds.includes(doc.id) }"
          @click="$router.push(`/documents/${doc.id}`)"
        >
          <label class="card-checkbox" @click.stop>
            <input
              type="checkbox"
              :checked="selectedIds.includes(doc.id)"
              @change="toggleSelect(doc.id)"
            />
          </label>
          <span class="card-title">{{ doc.filename }}</span>
          <span class="card-tags">
            <StatusBadge :status="doc.status" />
            <span v-if="getFormatLabel(doc)" class="format-label">{{ getFormatLabel(doc) }}</span>
          </span>
          <span class="card-actions" @click.stop>
            <el-tooltip v-if="doc.status === 'failed'" content="重新解析" placement="top">
              <el-icon class="action-icon" :size="14" @click="store.reparseDocument(doc.id); store.fetchDocuments()">
                <Refresh />
              </el-icon>
            </el-tooltip>
            <el-tooltip content="删除" placement="top">
              <el-icon class="action-icon action-icon-danger" :size="14" @click="confirmDelete(doc)">
                <Delete />
              </el-icon>
            </el-tooltip>
          </span>
          <el-icon class="card-arrow" :size="16" color="var(--color-stone-gray)">
            <ArrowRight />
          </el-icon>
        </div>
      </div>

      <!-- Pagination -->
      <div v-if="store.total > pageSize" class="pagination">
        <el-pagination
          v-model:current-page="page"
          :page-size="pageSize"
          :total="store.total"
          layout="prev, pager, next"
          @current-change="changePage"
          small
        />
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useDocumentStore } from '../stores/documents'
import type { DocumentItem, UploadResult } from '../stores/documents'
import { UploadFilled, Document, Search, Loading, ArrowRight, CircleCloseFilled, Refresh, Delete } from '@element-plus/icons-vue'
import StatusBadge from '../components/common/StatusBadge.vue'

const store = useDocumentStore()

const fileInputRef = ref<HTMLInputElement | null>(null)
const isDragging = ref(false)
const uploading = ref(false)
const uploadProgress = ref(0)
const uploadedCount = ref(0)
const uploadError = ref('')
const previewFiles = ref<File[]>([])
const uploadResults = ref<UploadResult[]>([])
const page = ref(1)
const pageSize = 20
const selectedIds = ref<string[]>([])
const pollingTimer = ref<number | null>(null)

const searchQuery = ref('')
const statusFilter = ref('')
const formatFilter = ref('')

onMounted(() => {
  store.fetchDocuments(page.value)
  startPolling()
})

onUnmounted(() => {
  stopPolling()
})

const paginatedDocuments = computed(() => {
  let docs = [...store.documents]

  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    docs = docs.filter(d => d.filename.toLowerCase().includes(q))
  }

  if (statusFilter.value) {
    docs = docs.filter(d => d.status === statusFilter.value)
  }

  if (formatFilter.value) {
    docs = docs.filter(d => getFormatLabel(d) === formatFilter.value || getFormatKey(d) === formatFilter.value)
  }

  return docs
})

function getFormatKey(doc: DocumentItem): string {
  const ext = doc.filename.split('.').pop()?.toLowerCase() || ''
  const map: Record<string, string> = {
    docx: 'docx',
    xlsx: 'excel', xls: 'excel', csv: 'excel',
    pdf: 'pdf',
    png: 'image', jpg: 'image', jpeg: 'image', bmp: 'image',
    eml: 'email', msg: 'email',
    txt: 'text', md: 'text', json: 'text', xml: 'text', yml: 'text', yaml: 'text',
  }
  return map[ext] || ''
}

function getFormatLabel(doc: DocumentItem): string {
  const key = getFormatKey(doc)
  const labels: Record<string, string> = {
    docx: 'docx', excel: 'excel', pdf: 'pdf',
    image: 'image', email: 'email', text: 'text',
  }
  return labels[key] || (doc.parser_type || '')
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

function onDrop(e: DragEvent) {
  isDragging.value = false
  const files = e.dataTransfer?.files
  if (files?.length) setPreview(Array.from(files))
}

function onFileSelect(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files?.length) setPreview(Array.from(input.files))
}

function setPreview(files: File[]) {
  previewFiles.value = files
  uploadResults.value = []
  uploadError.value = ''
  if (files.length === 1) doUpload(files[0])
}

function clearPreview() {
  previewFiles.value = []
  uploadResults.value = []
}

async function doUpload(file: File) {
  uploading.value = true
  uploadProgress.value = 0
  uploadedCount.value = 0
  uploadError.value = ''
  uploadResults.value = []

  const timer = setInterval(() => {
    if (uploadProgress.value < 90) uploadProgress.value += 10
  }, 200)

  try {
    const doc = await store.uploadFile(file)
    uploadProgress.value = 100
    uploadedCount.value = 1
    uploadResults.value = [{ file, success: true, document: doc }]
    await store.fetchDocuments(page.value)
  } catch {
    uploadError.value = '上传失败，请重试'
    uploadResults.value = [{ file, success: false, error: '上传失败' }]
  } finally {
    clearInterval(timer)
    uploading.value = false
  }
}

async function uploadAll() {
  uploading.value = true
  uploadProgress.value = 0
  uploadedCount.value = 0
  uploadError.value = ''
  uploadResults.value = previewFiles.value.map(f => ({ file: f, success: false }))

  const results = await store.uploadFiles(previewFiles.value)
  uploadResults.value = results

  let successCount = 0
  results.forEach((r, i) => {
    if (r.success) successCount++
    uploadProgress.value = Math.round(((i + 1) / results.length) * 100)
  })
  uploadedCount.value = successCount

  await store.fetchDocuments(page.value)
  uploading.value = false

  const dupCount = results.filter(r => r.duplicate).length
  const failCount = results.filter(r => !r.success && !r.duplicate).length
  if (failCount > 0) {
    uploadError.value = `${failCount} 个文件上传失败`
  }
  if (dupCount > 0) {
    uploadError.value = uploadError.value
      ? uploadError.value + `，${dupCount} 个文件已存在`
      : `${dupCount} 个文件已存在`
  }
}

function toggleSelect(id: string) {
  const idx = selectedIds.value.indexOf(id)
  if (idx >= 0) selectedIds.value.splice(idx, 1)
  else selectedIds.value.push(id)
}

function clearSelection() {
  selectedIds.value = []
}

function confirmDelete(doc: DocumentItem) {
  if (confirm(`确定删除「${doc.filename}」吗？此操作不可撤销。`)) {
    store.deleteDocument(doc.id)
  }
}

async function batchDelete() {
  if (!confirm(`确定删除选中的 ${selectedIds.value.length} 个文件吗？此操作不可撤销。`)) return
  await store.deleteDocuments(selectedIds.value)
  selectedIds.value = []
}

async function batchReparse() {
  await store.reparseDocuments(selectedIds.value)
  selectedIds.value = []
  await store.fetchDocuments(page.value)
}

function changePage(p: number) {
  if (p < 1) return
  page.value = p
  store.fetchDocuments(p)
}

// 实时状态轮询
function startPolling() {
  pollingTimer.value = window.setInterval(async () => {
    const hasPending = store.documents.some(d => d.status === 'pending' || d.status === 'processing')
    if (hasPending) {
      await store.fetchDocuments(page.value)
    }
  }, 3000)
}

function stopPolling() {
  if (pollingTimer.value) {
    clearInterval(pollingTimer.value)
    pollingTimer.value = null
  }
}
</script>

<style scoped>
.document-page {
  max-width: 820px;
  margin: 0 auto;
}

/* Upload Card */
.upload-card {
  background: var(--color-ivory);
  border: 1px solid var(--color-border-cream);
  border-radius: var(--radius-featured);
  padding: var(--space-24) var(--space-30);
  margin-bottom: var(--space-20);
  box-shadow: var(--shadow-whisper);
}

.section-title {
  font-family: var(--font-serif);
  font-size: var(--text-h1);
  font-weight: 500;
  color: var(--color-near-black);
  margin-bottom: var(--space-6);
}

.section-desc {
  font-size: var(--text-small);
  color: var(--color-olive-gray);
  margin-bottom: var(--space-20);
}

/* Drop Zone */
.drop-zone {
  background: var(--color-parchment);
  border: 1.5px dashed var(--color-border-warm);
  border-radius: var(--radius-featured);
  padding: var(--space-24) var(--space-30);
  text-align: center;
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s;
  min-height: 140px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
}

.drop-zone:hover,
.drop-zone.dragging {
  border-color: var(--color-terracotta);
  background: rgba(201, 100, 66, 0.03);
}

.drop-placeholder .drop-text {
  font-size: var(--text-body);
  color: var(--color-olive-gray);
  margin-top: var(--space-8);
}

.drop-placeholder .link-text {
  color: var(--color-terracotta);
  font-weight: 500;
  cursor: pointer;
}

.drop-placeholder .hint {
  font-size: var(--text-caption);
  color: var(--color-stone-gray);
  margin-top: var(--space-6);
}

/* File Preview */
.file-preview-list {
  width: 100%;
  text-align: left;
}

.file-preview-item {
  display: flex;
  align-items: center;
  gap: var(--space-10);
  padding: var(--space-6) 0;
  border-bottom: 1px solid var(--color-border-cream);
}

.file-preview-item:last-of-type {
  border-bottom: none;
}

.file-name {
  flex: 1;
  font-size: var(--text-small);
  color: var(--color-near-black);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-size {
  font-size: var(--text-caption);
  color: var(--color-stone-gray);
  flex-shrink: 0;
}

.file-status {
  flex-shrink: 0;
  font-size: var(--text-caption);
  font-weight: 500;
}

.status-success { color: var(--color-success); }
.status-duplicate { color: var(--color-terracotta); }
.status-error { color: var(--color-error); }

/* Upload Actions */
.upload-actions {
  display: flex;
  gap: var(--space-10);
  margin-top: var(--space-12);
  justify-content: center;
}

.upload-all-btn {
  background: var(--color-terracotta);
  color: #fff;
  border: none;
  border-radius: var(--radius-comfort);
  padding: var(--space-8) var(--space-16);
  font-size: var(--text-small);
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.15s;
}

.upload-all-btn:hover {
  opacity: 0.85;
}

.clear-btn {
  background: transparent;
  color: var(--color-stone-gray);
  border: 1px solid var(--color-border-warm);
  border-radius: var(--radius-comfort);
  padding: var(--space-8) var(--space-16);
  font-size: var(--text-small);
  cursor: pointer;
  transition: color 0.15s, border-color 0.15s;
}

.clear-btn:hover {
  color: var(--color-near-black);
  border-color: var(--color-stone-gray);
}

.preview-hint {
  margin-top: var(--space-10);
  font-size: var(--text-caption);
  color: var(--color-olive-gray);
  text-align: center;
}

/* Upload Progress / Status */
.upload-progress {
  margin-top: var(--space-16);
}

.upload-progress-text {
  margin-top: var(--space-6);
  font-size: var(--text-caption);
  color: var(--color-olive-gray);
  text-align: center;
}

.upload-success {
  margin-top: var(--space-16);
  display: flex;
  align-items: center;
  gap: var(--space-8);
  padding: var(--space-10) var(--space-16);
  background: rgba(107, 143, 60, 0.07);
  border-radius: var(--radius-comfort);
  font-size: var(--text-small);
  color: var(--color-near-black);
}

.upload-success strong {
  font-weight: 500;
}

.view-link {
  margin-left: auto;
  font-size: var(--text-small);
  font-weight: 500;
}

.upload-error {
  margin-top: var(--space-16);
  display: flex;
  align-items: center;
  gap: var(--space-8);
  padding: var(--space-10) var(--space-16);
  background: rgba(181, 51, 51, 0.07);
  border-radius: var(--radius-comfort);
  font-size: var(--text-small);
  color: var(--color-error);
}

/* Filter Bar */
.filter-bar {
  display: flex;
  align-items: center;
  gap: var(--space-10);
  margin-bottom: var(--space-16);
  flex-wrap: wrap;
}

.search-input {
  flex: 1;
  min-width: 200px;
}

.filter-group {
  display: flex;
  gap: var(--space-8);
}

.filter-select {
  width: 120px;
}

/* Batch Bar */
.batch-bar {
  display: flex;
  align-items: center;
  gap: var(--space-10);
  padding: var(--space-10) var(--space-16);
  background: var(--color-ivory);
  border: 1px solid var(--color-border-cream);
  border-radius: var(--radius-comfort);
  margin-bottom: var(--space-16);
  box-shadow: var(--shadow-whisper);
}

.selected-count {
  flex: 1;
  font-size: var(--text-small);
  color: var(--color-terracotta);
  font-weight: 500;
}

.batch-btn {
  background: var(--color-terracotta);
  color: #fff;
  border: none;
  border-radius: var(--radius-comfort);
  padding: var(--space-6) var(--space-12);
  font-size: var(--text-caption);
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.15s;
}

.batch-btn:hover {
  opacity: 0.85;
}

.batch-btn-danger {
  background: var(--color-error);
}

.batch-btn-clear {
  background: transparent;
  color: var(--color-stone-gray);
  border: 1px solid var(--color-border-warm);
}

/* Document List */
.document-list {
  background: var(--color-ivory);
  border: 1px solid var(--color-border-cream);
  border-radius: var(--radius-comfort);
  overflow: hidden;
}

.document-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px var(--space-20);
  border-top: 1px solid var(--color-border-cream);
  cursor: pointer;
  transition: background 0.15s;
  gap: var(--space-8);
}

.document-card:first-child {
  border-top: none;
}

.document-card:hover {
  background: var(--color-parchment);
}

.document-card.selected {
  background: rgba(201, 100, 66, 0.04);
}

.card-checkbox {
  flex-shrink: 0;
  cursor: pointer;
  display: flex;
  align-items: center;
}

.card-checkbox input[type="checkbox"] {
  appearance: none;
  width: 16px;
  height: 16px;
  border: 1.5px solid var(--color-stone-gray);
  border-radius: 3px;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
}

.card-checkbox input[type="checkbox"]:checked {
  border-color: var(--color-terracotta);
  background: var(--color-terracotta);
}

.card-title {
  font-family: var(--font-serif);
  font-size: var(--text-body);
  font-weight: 500;
  color: var(--color-near-black);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  min-width: 0;
}

.card-tags {
  display: flex;
  align-items: center;
  gap: var(--space-6);
  flex-shrink: 0;
}

.format-label {
  font-size: var(--text-label);
  color: var(--color-stone-gray);
  letter-spacing: 0.02em;
}

.card-actions {
  display: flex;
  align-items: center;
  gap: var(--space-6);
  flex-shrink: 0;
  opacity: 0;
  transition: opacity 0.15s;
}

.document-card:hover .card-actions {
  opacity: 1;
}

.action-icon {
  cursor: pointer;
  padding: 2px;
  border-radius: 4px;
  transition: color 0.15s, background 0.15s;
}

.action-icon:hover {
  background: rgba(201, 100, 66, 0.1);
  color: var(--color-terracotta);
}

.action-icon-danger:hover {
  background: rgba(181, 51, 51, 0.1);
  color: var(--color-error);
}

.card-arrow {
  flex-shrink: 0;
  margin-left: var(--space-8);
}

/* States */
.loading-state {
  text-align: center;
  padding: var(--space-30);
  color: var(--color-olive-gray);
}

.loading-state p {
  margin-top: var(--space-8);
  font-size: var(--text-small);
}

.empty-state {
  background: var(--color-ivory);
  border: 1px solid var(--color-border-cream);
  border-radius: var(--radius-comfort);
  padding: var(--space-30);
}

/* Pagination */
.pagination {
  display: flex;
  justify-content: center;
  margin-top: var(--space-20);
}
</style>
