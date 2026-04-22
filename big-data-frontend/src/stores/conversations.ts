import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface Conversation {
  id: string
  title: string
  message_count: number
}

export const useConversationStore = defineStore('conversations', () => {
  const conversations = ref<Conversation[]>([])
  const activeId = ref<string | undefined>()
  const loading = ref(false)

  const active = computed(() =>
    conversations.value.find(c => c.id === activeId.value)
  )

  async function fetchList() {
    const res = await fetch('/api/llm/conversations')
    const data = await res.json()
    conversations.value = data
  }

  async function fetchConversation(id: string) {
    const res = await fetch(`/api/llm/conversations/${id}`)
    if (!res.ok) return null
    const data = await res.json()
    return data
  }

  async function createConversation(title = '新对话') {
    const res = await fetch('/api/llm/conversations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title }),
    })
    const conv: Conversation = await res.json()
    conversations.value.unshift(conv)
    activeId.value = conv.id
    return conv
  }

  async function deleteConversation(id: string) {
    await fetch(`/api/llm/conversations/${id}`, { method: 'DELETE' })
    conversations.value = conversations.value.filter(c => c.id !== id)
    if (activeId.value === id) activeId.value = undefined
  }

  async function renameConversation(id: string, title: string) {
    await fetch(`/api/llm/conversations/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title }),
    })
    const conv = conversations.value.find(c => c.id === id)
    if (conv) conv.title = title
  }

  function setActive(id: string) {
    activeId.value = id
  }

  return {
    conversations,
    activeId,
    active,
    loading,
    fetchList,
    fetchConversation,
    createConversation,
    deleteConversation,
    renameConversation,
    setActive,
  }
})
