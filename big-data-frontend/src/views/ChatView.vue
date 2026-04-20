<template>
  <div class="chat-container">
    <div class="chat-header">
      <h2>智能对话</h2>
      <el-button v-if="messages.length" size="small" @click="newConversation">
        新对话
      </el-button>
    </div>

    <div class="chat-messages" ref="messagesRef">
      <template v-if="messages.length === 0">
        <div class="chat-welcome">
          <el-icon size="48"><ChatDotRound /></el-icon>
          <p>你好！我是文档助手，可以问我关于已解析文档的问题。</p>
        </div>
      </template>

      <div
        v-for="(msg, i) in messages"
        :key="i"
        :class="['message', msg.role]"
      >
        <div class="message-bubble">
          {{ msg.content }}
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
        placeholder="输入消息..."
        @keydown.enter.exact.prevent="sendMessage"
        :disabled="isLoading"
      />
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
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import { ChatDotRound, Loading, Promotion } from '@element-plus/icons-vue'
import { chat } from '../api/llm'
import type { ChatMessage } from '../api/llm'

const messages = ref<ChatMessage[]>([])
const input = ref('')
const isLoading = ref(false)
const conversationId = ref<string | undefined>()
const messagesRef = ref<HTMLElement | null>(null)

async function sendMessage() {
  const text = input.value.trim()
  if (!text || isLoading.value) return

  messages.value.push({ role: 'user', content: text })
  input.value = ''
  isLoading.value = true

  try {
    const res = await chat(text, conversationId.value)
    if (!conversationId.value) conversationId.value = res.conversation_id
    messages.value.push({ role: 'assistant', content: res.reply })
  } catch (err: any) {
    messages.value.push({
      role: 'assistant',
      content: `对话出错：${err.response?.data?.detail || err.message}`,
    })
  } finally {
    isLoading.value = false
    await nextTick()
    scrollToBottom()
  }
}

function newConversation() {
  messages.value = []
  conversationId.value = undefined
}

function scrollToBottom() {
  if (messagesRef.value) {
    messagesRef.value.scrollTop = messagesRef.value.scrollHeight
  }
}
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 120px);
  max-width: 800px;
  margin: 0 auto;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0;
  border-bottom: 1px solid var(--border-color, #e8e0d8);
}

.chat-header h2 {
  margin: 0;
  font-size: 18px;
  color: var(--text-primary, #2c1810);
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px 0;
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
  max-width: 70%;
  padding: 10px 16px;
  border-radius: 12px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
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
  gap: 8px;
  color: var(--text-secondary, #6b5744);
}

.chat-input {
  display: flex;
  gap: 12px;
  padding: 16px 0;
  border-top: 1px solid var(--border-color, #e8e0d8);
  align-items: flex-end;
}

.chat-input :deep(.el-textarea__inner) {
  border-radius: 8px;
  background: var(--bg-secondary, #f9f5f0);
}

.chat-input .el-button {
  flex-shrink: 0;
}
</style>
