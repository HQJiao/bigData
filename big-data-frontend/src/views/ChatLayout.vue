<template>
  <div class="chat-layout">
    <!-- 左侧会话列表 -->
    <aside :class="['sidebar', { collapsed: sidebarCollapsed }]">
      <div class="sidebar-header">
        <el-button type="primary" size="small" @click="createNew">
          <el-icon><Plus /></el-icon>
          新对话
        </el-button>
      </div>
      <div class="sidebar-list">
        <div
          v-for="conv in conversations"
          :key="conv.id"
          :class="['sidebar-item', { active: conv.id === localActiveId }]"
          @click="selectConversation(conv.id)"
        >
          <span class="item-title">{{ conv.title }}</span>
          <el-dropdown trigger="click" @command="(cmd: string) => handleItemAction(cmd, conv.id)">
            <el-icon class="item-more"><MoreFilled /></el-icon>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="rename">重命名</el-dropdown-item>
                <el-dropdown-item command="delete">删除</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </aside>

    <!-- 右侧对话区 -->
    <main class="chat-main">
      <div class="chat-header">
        <el-button text @click="sidebarCollapsed = !sidebarCollapsed">
          <el-icon><Fold v-if="!sidebarCollapsed" /><Expand v-else /></el-icon>
        </el-button>
        <h2>{{ active?.title || '智能对话' }}</h2>
        <div class="doc-selector">
          <span class="doc-label">参考文档：</span>
          <el-select
            v-model="selectedDocIds"
            multiple
            placeholder="选择文档"
            size="small"
            filterable
            class="doc-dropdown"
          >
            <el-option
              v-for="doc in allDocuments"
              :key="doc.id"
              :label="doc.filename"
              :value="doc.id"
            />
          </el-select>
        </div>
      </div>

      <div class="chat-messages" ref="messagesRef">
        <template v-if="messages.length === 0">
          <div class="chat-welcome">
            <el-icon size="48"><ChatDotRound /></el-icon>
            <p>你好！我是文档助手，可以基于已上传的文档回答问题。</p>
            <p class="hint">选择左侧「参考文档」可限定回答范围。</p>
          </div>
        </template>

        <div
          v-for="(msg, i) in messages"
          :key="i"
          :class="['message', msg.role]"
        >
          <div class="message-bubble">
            <MarkdownRenderer v-if="msg.role === 'assistant'" :content="msg.content" />
            <span v-else>{{ msg.content }}</span>
          </div>
        </div>

        <div v-if="isLoading" class="message assistant">
          <div class="message-bubble loading">
            <el-icon class="is-loading"><Loading /></el-icon>
          </div>
        </div>
      </div>

      <div class="chat-input">
        <el-input
          v-model="input"
          type="textarea"
          :autosize="{ minRows: 1, maxRows: 4 }"
          placeholder="输入消息... (Enter 发送, Shift+Enter 换行)"
          @keydown.enter.exact.prevent="sendMessage"
          :disabled="isLoading"
        />
        <div class="input-actions">
          <el-button
            v-if="isLoading"
            type="danger"
            size="small"
            @click="stopGeneration"
          >
            停止
          </el-button>
          <el-button
            type="primary"
            :disabled="!input.trim() || isLoading"
            @click="sendMessage"
            circle
          >
            <el-icon><Promotion /></el-icon>
          </el-button>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import {
  ChatDotRound, Loading, Promotion, Plus, MoreFilled, Fold, Expand,
} from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'
import MarkdownRenderer from '../components/chat/MarkdownRenderer.vue'
import { useConversationStore } from '../stores/conversations'
import { chatStream } from '../api/llm'
import type { ChatMessage } from '../api/llm'

const store = useConversationStore()
const { conversations, active, fetchList, fetchConversation, createConversation, deleteConversation, renameConversation, setActive } = store

const localActiveId = computed({
  get: () => store.activeId,
  set: (val: string | undefined) => { store.activeId = val },
})

const messages = ref<ChatMessage[]>([])
const input = ref('')
const isLoading = ref(false)
const sidebarCollapsed = ref(false)
const messagesRef = ref<HTMLElement | null>(null)
const selectedDocIds = ref<string[]>([])
const allDocuments = ref<any[]>([])

async function loadDocuments() {
  try {
    const res = await fetch('/api/files?page=1&page_size=100')
    const data = await res.json()
    allDocuments.value = data.items || []
  } catch {
    allDocuments.value = []
  }
}

async function createNew() {
  await createConversation()
  messages.value = []
}

async function selectConversation(id: string) {
  setActive(id)
  const conv = await fetchConversation(id)
  if (conv) {
    messages.value = conv.messages
  } else {
    messages.value = []
  }
}

async function sendMessage() {
  const text = input.value.trim()
  if (!text || isLoading.value) return

  if (!localActiveId.value) {
    await createConversation(text.slice(0, 30))
  }

  messages.value.push({ role: 'user', content: text })
  input.value = ''
  isLoading.value = true

  let assistantContent = ''
  messages.value.push({ role: 'assistant', content: '' })

  chatStream(
    text,
    localActiveId.value,
    selectedDocIds.value,
    (token: string) => {
      assistantContent += token
      messages.value[messages.value.length - 1].content = assistantContent
      scrollToBottom()
    },
    (convId: string) => {
      isLoading.value = false
      setActive(convId)
      fetchList()
    },
    (errMsg: string) => {
      messages.value[messages.value.length - 1].content = `对话出错：${errMsg}`
      isLoading.value = false
    },
  )
}

function stopGeneration() {
  isLoading.value = false
}

async function handleItemAction(action: string, id: string) {
  if (action === 'delete') {
    await ElMessageBox.confirm('确定删除此对话？', '确认', { type: 'warning' })
    await deleteConversation(id)
    if (localActiveId.value === id) messages.value = []
  } else if (action === 'rename') {
    const { value } = await ElMessageBox.prompt('输入新标题', '重命名', {
      inputValue: conversations.find(c => c.id === id)?.title || '',
    })
    if (value) await renameConversation(id, value)
  }
}

function scrollToBottom() {
  if (messagesRef.value) {
    messagesRef.value.scrollTop = messagesRef.value.scrollHeight
  }
}

onMounted(() => {
  fetchList().catch(() => console.error('Failed to fetch conversations'))
  loadDocuments()
})
</script>

<style scoped>
.chat-layout {
  display: flex;
  height: calc(100vh - 120px);
}

.sidebar {
  width: 260px;
  border-right: 1px solid var(--border-color, #e8e0d8);
  display: flex;
  flex-direction: column;
  transition: width 0.2s;
  flex-shrink: 0;
}

.sidebar.collapsed {
  width: 0;
  overflow: hidden;
}

.sidebar-header {
  padding: 12px;
  border-bottom: 1px solid var(--border-color, #e8e0d8);
}

.sidebar-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.sidebar-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 10px;
  border-radius: 6px;
  cursor: pointer;
  margin-bottom: 4px;
  transition: background 0.15s;
}

.sidebar-item:hover {
  background: var(--bg-secondary, #f9f5f0);
}

.sidebar-item.active {
  background: var(--primary-light, #f5e6d8);
}

.item-title {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
}

.item-more {
  opacity: 0;
  transition: opacity 0.15s;
  flex-shrink: 0;
}

.sidebar-item:hover .item-more {
  opacity: 1;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.chat-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color, #e8e0d8);
}

.chat-header h2 {
  margin: 0;
  font-size: 16px;
  color: var(--text-primary, #2c1810);
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.doc-selector {
  display: flex;
  align-items: center;
  gap: 6px;
}

.doc-label {
  font-size: 13px;
  color: var(--text-secondary, #6b5744);
  white-space: nowrap;
}

.doc-dropdown {
  width: 160px;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px 16px;
}

.chat-welcome {
  text-align: center;
  color: var(--text-secondary, #6b5744);
  padding: 60px 20px;
}

.chat-welcome .el-icon {
  color: var(--primary-color, #c4704f);
  margin-bottom: 12px;
}

.hint {
  font-size: 13px;
  margin-top: 8px;
}

.message {
  margin-bottom: 16px;
  display: flex;
}

.message.user {
  justify-content: flex-end;
}

.message.assistant {
  justify-content: flex-start;
}

.message-bubble {
  max-width: 75%;
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.6;
}

.message.user .message-bubble {
  background: var(--primary-color, #c4704f);
  color: #fff;
  border-bottom-right-radius: 4px;
}

.message.assistant .message-bubble {
  background: var(--bg-secondary, #f9f5f0);
  color: var(--text-primary, #2c1810);
  border-bottom-left-radius: 4px;
}

.message-bubble.loading {
  display: inline-flex;
  align-items: center;
  color: var(--text-secondary, #6b5744);
}

.chat-input {
  display: flex;
  gap: 12px;
  padding: 12px 16px;
  border-top: 1px solid var(--border-color, #e8e0d8);
  align-items: flex-end;
}

.chat-input :deep(.el-textarea__inner) {
  border-radius: 8px;
  background: var(--bg-secondary, #f9f5f0);
}

.input-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
  align-items: center;
}
</style>
