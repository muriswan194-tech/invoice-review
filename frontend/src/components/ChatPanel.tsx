import { useState, useRef, useEffect } from 'react'
import type { ChatMessage } from '../lib/api'

type Props = {
  recordId: number
  isOpen: boolean
  onClose: () => void
}

/** Chat with the AI advisor about the current document. */
function ChatPanel({ recordId, isOpen, onClose }: Props) {
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [isSending, setIsSending] = useState(false)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  async function handleSend() {
    if (!input.trim() || isSending) return
    const userMessage: { role: 'user'; content: string } = { role: 'user', content: input.trim() }
    setMessages((prev) => [...prev, userMessage])
    setInput('')

    setIsSending(true)
    try {
      const response = await fetch(`/invoices/${recordId}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: [{ role: 'user', content: input.trim() }] }),
      })
      if (!response.ok) {
        throw new Error('Failed to get response')
      }
      const data = await response.json()
      setMessages((prev) => [...prev, { role: 'assistant', content: data.content }])
    } catch (error) {
      console.error('Chat error:', error)
      setMessages((prev) => [...prev, { role: 'assistant', content: 'Sorry, I couldn\'t get a response. Please try again.' }])
    } finally {
      setIsSending(false)
    }
  }

  function handleKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      handleSend()
    }
  }

  if (!isOpen) return null

  return (
    <div className="chat-panel">
      <div className="chat-header">
        <p className="eyebrow">Ask the Advisor</p>
        <button type="button" className="button-quiet button-small" onClick={onClose}>Close</button>
      </div>
      <div className="chat-messages" role="log" aria-live="polite">
        {messages.map((msg, idx) => (
          <div key={idx} className={`chat-message ${msg.role}`}>
            <span className="chat-role">{msg.role === 'user' ? 'You' : 'Advisor'}</span>
            <p>{msg.content}</p>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
      {isSending && <p className="chat-sending">Advisor is thinking\u2026</p>}
      <div className="chat-input">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about the invoice, the rules, or anything else\u2026"
          disabled={isSending}
          rows={3}
        />
        <button type="button" onClick={handleSend} disabled={isSending || !input.trim()}>
          {isSending ? 'Sending\u2026' : 'Send'}
        </button>
      </div>
    </div>
  )
}

export default ChatPanel