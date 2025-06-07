import { useState } from 'react'
import { marked } from 'marked'
import './index.css'
import { Button } from './components/Button'

function App() {
  const [file, setFile] = useState(null)
  const [question, setQuestion] = useState('')
  const [chatId, setChatId] = useState(null)
  const [messages, setMessages] = useState([])

  const upload = async () => {
    if (!file) return
    const form = new FormData()
    form.append('file', file)
    await fetch('http://localhost:8000/upload', { method: 'POST', body: form })
  }

  const ask = async () => {
    if (!question) return
    const res = await fetch('http://localhost:8000/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: question, chat_id: chatId })
    })
    const json = await res.json()
    setChatId(json.chat_id)
    setMessages([...messages, { question, answer: json.answer, sources: json.sources }])
    setQuestion('')
  }

  const showSource = async (src) => {
    const res = await fetch(`http://localhost:8000/chunk?doc_id=${src.doc_id}&chunk=${src.chunk}`)
    const data = await res.json()
    alert(data.text)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-100 p-8 flex flex-col items-center text-gray-900">
      <h1 className="text-4xl font-bold mb-8">PDF Assistant</h1>
      <div className="flex gap-2 mb-8">
        <input
          type="file"
          onChange={e => setFile(e.target.files[0])}
          className="file:mr-4 file:rounded-md file:border-0 file:bg-blue-600 file:px-4 file:py-2 file:text-white file:cursor-pointer text-sm"
        />
        <Button onClick={upload}>Upload</Button>
      </div>
      <div className="w-full max-w-2xl space-y-4 mb-8 overflow-y-auto">
        {messages.map((m, idx) => (
          <div key={idx} className="bg-white rounded-xl shadow-lg p-4 space-y-2">
            <p className="font-medium text-blue-700">Q: {m.question}</p>
            <div
              className="prose max-w-none"
              dangerouslySetInnerHTML={{ __html: marked(m.answer) }}
            />
            <p className="text-sm text-gray-500">
              {m.sources.map((s, i) => (
                <sup key={i} className="ml-1">
                  <a href="#" onClick={() => showSource(s)} className="text-blue-600">[{i + 1}]</a>
                </sup>
              ))}
            </p>
          </div>
        ))}
      </div>
      <div className="w-full max-w-2xl flex gap-2">
        <input
          className="flex-1 border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          value={question}
          onChange={e => setQuestion(e.target.value)}
          placeholder="Ask a question..."
        />
        <Button variant="secondary" onClick={ask}>Ask</Button>
      </div>
    </div>
  )
}

export default App
