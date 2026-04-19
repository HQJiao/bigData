import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api'

export interface DocumentItem {
  id: string
  filename: string
  status: string
  parser_type?: string
}

export interface DocumentDetail extends DocumentItem {
  content?: string
  error_message?: string
  file_size?: number
  mime_type?: string
}

export interface UploadResult {
  file: File
  success: boolean
  document?: DocumentItem
  duplicate?: boolean
  error?: string
}

export const useDocumentStore = defineStore('documents', () => {
  const documents = ref<DocumentItem[]>([])
  const total = ref(0)
  const currentDocument = ref<DocumentDetail | null>(null)
  const loading = ref(false)

  async function fetchDocuments(page = 1, pageSize = 20) {
    loading.value = true
    try {
      const { data } = await api.get('/files', { params: { page, page_size: pageSize } })
      documents.value = data.items
      total.value = data.total
    } finally {
      loading.value = false
    }
  }

  async function fetchDocument(id: string) {
    loading.value = true
    try {
      const { data } = await api.get(`/files/${id}`)
      currentDocument.value = data
    } finally {
      loading.value = false
    }
  }

  async function uploadFile(file: File) {
    const formData = new FormData()
    formData.append('file', file)
    const { data } = await api.post('/files', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data as DocumentItem
  }

  async function saveContent(id: string, content: string) {
    await api.put(`/files/${id}/content`, { content })
    if (currentDocument.value?.id === id) {
      currentDocument.value.content = content
      currentDocument.value.status = 'completed'
    }
  }

  async function uploadFiles(files: File[]): Promise<UploadResult[]> {
    const results: UploadResult[] = []
    for (const file of files) {
      try {
        const formData = new FormData()
        formData.append('file', file)
        const { data } = await api.post('/files', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        })
        results.push({ file, success: true, document: data as DocumentItem })
      } catch (e: unknown) {
        const axiosErr = e as { response?: { status?: number; data?: { detail?: string } } }
        if (axiosErr.response?.status === 409) {
          results.push({ file, success: false, duplicate: true, error: '文件已存在' })
        } else {
          results.push({ file, success: false, error: '上传失败' })
        }
      }
    }
    return results
  }

  async function deleteDocument(id: string) {
    await api.delete(`/files/${id}`)
    documents.value = documents.value.filter(d => d.id !== id)
  }

  async function deleteDocuments(ids: string[]) {
    await Promise.all(ids.map(id => api.delete(`/files/${id}`)))
    documents.value = documents.value.filter(d => !ids.includes(d.id))
  }

  async function reparseDocument(id: string) {
    const { data } = await api.post(`/files/${id}/reparse`)
    // 更新列表中的状态
    const doc = documents.value.find(d => d.id === id)
    if (doc) doc.status = data.status
    if (currentDocument.value?.id === id) {
      currentDocument.value.status = data.status
      currentDocument.value.error_message = undefined
    }
  }

  async function reparseDocuments(ids: string[]) {
    await Promise.all(ids.map(id => reparseDocument(id)))
  }

  return {
    documents, total, currentDocument, loading,
    fetchDocuments, fetchDocument, uploadFile, uploadFiles,
    saveContent, deleteDocument, deleteDocuments,
    reparseDocument, reparseDocuments,
  }
})
