<template>
  <div class="document-page">
    <!-- Upload Section -->
    <section class="upload-card">
      <h2 class="section-title">上传文档</h2>
      <p class="section-desc">将文档拖拽到下方区域，系统会自动解析并提取文本内容。</p>

      <div
        class="drop-zone"
        :class="{ dragging: isDragging, 'has-files': previewFiles.length > 0 }"
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
          <el-icon :size="40" color="var(--color-stone-gray)">
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
            <el-icon :size="20" color="var(--color-terracotta)">
              <Document />
            </el-icon>
            <span class="file-name">{{ f.name }}</span>
            <span class="file-size">{{ formatSize(f.size) }}</span>
          </div>
          <p class="preview-hint">
            共 {{ previewFiles.length }} 个文件，点击上传
          </p>
        </div>
      </div>

      <div v-if="uploading" class="upload-progress">
        <el-progress :percentage="uploadProgress" :stroke-width="6" />
      </div>

      <div v-if="uploadedDoc" class="upload-success">
        <el-icon :size="20" color="var(--color-success)"><CircleCheckFilled /></el-icon>
        <span>已上传：<strong>{{ uploadedDoc.filename }}</strong></span>
        <router-link :to="`/documents/${uploadedDoc.id}`" class="view-link">查看详情</router-link>
      </div>

      <div v-if="uploadError" class="upload-error">
        <el-icon :size="20" color="var(--color-error)"><CircleCloseFilled /></el-icon>
        <span>{{ uploadError }}</span>
      </div>
    </section>

    <!-- Search / Filter Bar (placeholder UI) -->
    <section class="filter-bar">
      <el-input
        placeholder="搜索文件名..."
        v-model="searchQuery"
        :prefix-icon="Search"
        clearable
        class="search-input"
      />
      <div class="filter-group">
        <el-select placeholder="状态筛选" v-model="statusFilter" clearable size="default" class="filter-select">
          <el-option label="待解析" value="pending" />
          <el-option label="解析中" value="processing" />
          <el-option label="已完成" value="completed" />
          <el-option label="失败" value="failed" />
        </el-select>
        <el-select placeholder="格式筛选" v-model="formatFilter" clearable size="default" class="filter-select">
          <el-option label="Word (.docx)" value="docx" />
          <el-option label="Excel (.xlsx)" value="xlsx" />
          <el-option label="PDF (.pdf)" value="pdf" />
          <el-option label="图片" value="image" />
          <el-option label="邮件" value="email" />
          <el-option label="文本" value="text" />
        </el-select>
      </div>
    </section>

    <!-- Document List -->
    <section class="list-section">
      <div v-if="store.loading" class="loading-state">
        <el-icon class="is-loading" :size="24"><Loading /></el-icon>
        <p>加载中...</p>
      </div>

      <div v-else-if="store.documents.length === 0" class="empty-state">
        <el-empty description="暂无文档" :image-size="120" />
      </div>

      <div v-else class="document-list">
        <div
          v-for="doc in store.documents"
          :key="doc.id"
          class="document-card"
          @click="$router.push(`/documents/${doc.id}`)"
        >
          <div class="card-main">
            <h3 class="card-title">{{ doc.filename }}</h3>
            <div class="card-meta">
              <StatusBadge :status="doc.status" />
              <span v-if="doc.parser_type" class="parser-tag">{{ doc.parser_type }}</span>
            </div>
          </div>
          <div class="card-action">
            <el-icon :size="18" color="var(--color-stone-gray)"><ArrowRight /></el-icon>
          </div>
        </div>
      </div>

      <!-- Pagination -->
      <div v-if="store.total > 20" class="pagination">
        <el-pagination
          v-model:current-page="page"
          :page-size="20"
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
import { ref, onMounted } from 'vue'
import { useDocumentStore } from '../stores/documents'
import type { DocumentItem } from '../stores/documents'
import { UploadFilled, Document, Search, Loading, ArrowRight, CircleCheckFilled, CircleCloseFilled } from '@element-plus/icons-vue'
import StatusBadge from '../components/common/StatusBadge.vue'

const store = useDocumentStore()

const fileInputRef = ref<HTMLInputElement | null>(null)
const isDragging = ref(false)
const uploading = ref(false)
const uploadProgress = ref(0)
const uploadedDoc = ref<DocumentItem | null>(null)
const uploadError = ref('')
const previewFiles = ref<File[]>([])
const page = ref(1)

const searchQuery = ref('')
const statusFilter = ref('')
const formatFilter = ref('')

onMounted(() => {
  store.fetchDocuments(page.value)
})

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
  uploadError.value = ''
  // Auto-upload if single file
  if (files.length === 1) doUpload(files[0])
}

async function doUpload(file: File) {
  uploading.value = true
  uploadProgress.value = 0
  uploadError.value = ''
  uploadedDoc.value = null

  // Simulate progress (axios doesn't support progress on FormData in all cases)
  const timer = setInterval(() => {
    if (uploadProgress.value < 90) uploadProgress.value += 10
  }, 200)

  try {
    uploadedDoc.value = await store.uploadFile(file)
    uploadProgress.value = 100
    await store.fetchDocuments(page.value)
  } catch {
    uploadError.value = '上传失败，请重试'
  } finally {
    clearInterval(timer)
    uploading.value = false
    previewFiles.value = []
  }
}

function changePage(p: number) {
  if (p < 1) return
  page.value = p
  store.fetchDocuments(p)
}
</script>

<style scoped>
.document-page {
  max-width: 860px;
  margin: 0 auto;
}

/* Upload Card */
.upload-card {
  background: var(--color-ivory);
  border: 1px solid var(--color-border-cream);
  border-radius: var(--radius-featured);
  padding: var(--space-30);
  margin-bottom: var(--space-24);
  box-shadow: var(--shadow-whisper);
}

.section-title {
  font-family: var(--font-serif);
  font-size: var(--text-h1);
  font-weight: 500;
  color: var(--color-near-black);
  margin-bottom: var(--space-8);
}

.section-desc {
  font-size: var(--text-small);
  color: var(--color-olive-gray);
  margin-bottom: var(--space-20);
  line-height: var(--lh-relaxed);
}

/* Drop Zone */
.drop-zone {
  background: var(--color-parchment);
  border: 2px dashed var(--color-border-warm);
  border-radius: var(--radius-featured);
  padding: var(--space-30);
  text-align: center;
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s;
  min-height: 160px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
}

.drop-zone:hover,
.drop-zone.dragging {
  border-color: var(--color-terracotta);
  background: rgba(201, 100, 66, 0.04);
}

.drop-placeholder .drop-text {
  font-size: var(--text-body);
  color: var(--color-olive-gray);
  margin-top: var(--space-8);
}

.drop-placeholder .link-text {
  color: var(--color-terracotta);
  font-weight: 500;
}

.drop-placeholder .hint {
  font-size: var(--text-caption);
  color: var(--color-stone-gray);
  margin-top: var(--space-8);
}

/* File Preview */
.file-preview-list {
  width: 100%;
  text-align: left;
}

.file-preview-item {
  display: flex;
  align-items: center;
  gap: var(--space-12);
  padding: var(--space-8) 0;
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
}

.preview-hint {
  margin-top: var(--space-12);
  font-size: var(--text-caption);
  color: var(--color-olive-gray);
  text-align: center;
}

/* Upload Progress / Status */
.upload-progress {
  margin-top: var(--space-16);
}

.upload-success {
  margin-top: var(--space-16);
  display: flex;
  align-items: center;
  gap: var(--space-8);
  padding: var(--space-12) var(--space-16);
  background: rgba(107, 143, 60, 0.08);
  border-radius: var(--radius-comfort);
  font-size: var(--text-small);
  color: var(--color-near-black);
}

.upload-success strong {
  color: var(--color-near-black);
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
  padding: var(--space-12) var(--space-16);
  background: rgba(181, 51, 51, 0.08);
  border-radius: var(--radius-comfort);
  font-size: var(--text-small);
  color: var(--color-error);
}

/* Filter Bar */
.filter-bar {
  display: flex;
  align-items: center;
  gap: var(--space-12);
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
  width: 130px;
}

/* Document List */
.document-list {
  display: flex;
  flex-direction: column;
}

.document-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-16) var(--space-20);
  background: var(--color-ivory);
  border-top: 1px solid var(--color-border-cream);
  cursor: pointer;
  transition: background 0.15s;
}

.document-card:first-child {
  border-radius: var(--radius-comfort) var(--radius-comfort) 0 0;
}

.document-card:last-child {
  border-radius: 0 0 var(--radius-comfort) var(--radius-comfort);
  border-bottom: 1px solid var(--color-border-cream);
}

.document-card:hover {
  background: var(--color-parchment);
}

.card-main {
  display: flex;
  align-items: center;
  gap: var(--space-16);
  min-width: 0;
}

.card-title {
  font-family: var(--font-serif);
  font-size: var(--text-body-large);
  font-weight: 500;
  color: var(--color-near-black);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-meta {
  display: flex;
  align-items: center;
  gap: var(--space-8);
}

.parser-tag {
  font-size: var(--text-label);
  color: var(--color-stone-gray);
  letter-spacing: 0.04em;
}

.card-action {
  flex-shrink: 0;
  padding-left: var(--space-12);
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
  border-radius: var(--radius-featured);
  padding: var(--space-30);
}

/* Pagination */
.pagination {
  display: flex;
  justify-content: center;
  margin-top: var(--space-20);
}
</style>
