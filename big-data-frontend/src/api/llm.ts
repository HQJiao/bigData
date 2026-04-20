import axios from 'axios'

const llmApi = axios.create({
  baseURL: '/api/llm',
  timeout: 60000,
})

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface ChatResponse {
  reply: string
  conversation_id: string
}

export async function chat(
  message: string,
  conversationId?: string,
): Promise<ChatResponse> {
  const { data } = await llmApi.post('/chat', {
    message,
    conversation_id: conversationId,
    stream: false,
  })
  return data
}

export function chatStream(
  message: string,
  conversationId: string | undefined,
  onToken: (token: string) => void,
  onEnd: (conversationId: string) => void,
  onError: (message: string) => void,
): void {
  const body = JSON.stringify({ message, conversation_id: conversationId, stream: true })
  fetch('/api/llm/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body,
  })
    .then((res) => {
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const reader = res.body?.getReader()
      if (!reader) throw new Error('No readable stream')

      const decoder = new TextDecoder()
      let buffer = ''

      const read = () => {
        reader.read().then(({ done, value }) => {
          if (done) return
          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() || ''

          for (const line of lines) {
            if (!line.startsWith('data: ')) continue
            try {
              const json = JSON.parse(line.slice(6))
              if (json.event === 'token') onToken(json.content)
              else if (json.event === 'end') onEnd(json.conversation_id)
              else if (json.event === 'error') onError(json.message)
            } catch {
              // skip malformed SSE lines
            }
          }
          read()
        })
      }
      read()
    })
    .catch((err: Error) => onError(err.message))
}
