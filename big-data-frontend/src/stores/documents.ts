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

  return { documents, total, currentDocument, loading, fetchDocuments, fetchDocument, uploadFile, saveContent }
})
