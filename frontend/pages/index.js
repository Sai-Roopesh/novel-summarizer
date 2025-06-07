import { useState } from 'react';
import { marked } from 'marked';

export default function Home() {
  const [file, setFile] = useState(null);
  const [question, setQuestion] = useState('');
  const [chatId, setChatId] = useState(null);
  const [messages, setMessages] = useState([]);

  const upload = async () => {
    if (!file) return;
    const form = new FormData();
    form.append('file', file);
    await fetch('http://localhost:8000/upload', { method: 'POST', body: form });
  };

  const ask = async () => {
    const res = await fetch('http://localhost:8000/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: question, chat_id: chatId })
    });
    const json = await res.json();
    setChatId(json.chat_id);
    setMessages([...messages, { question, answer: json.answer, sources: json.sources }]);
    setQuestion('');
  };

  const showSource = async (src) => {
    const res = await fetch(`http://localhost:8000/chunk?doc_id=${src.doc_id}&chunk=${src.chunk}`);
    const data = await res.json();
    alert(data.text);
  };

  return (
    <div>
      <h1>PDF Assistant</h1>
      <input type="file" onChange={(e) => setFile(e.target.files[0])} />
      <button onClick={upload}>Upload</button>
      <br />
      <div>
        {messages.map((m, idx) => (
          <div key={idx} style={{ marginBottom: '1em' }}>
            <p><strong>Q:</strong> {m.question}</p>
            <p dangerouslySetInnerHTML={{ __html: marked(m.answer) }}></p>
            <p>
              {m.sources.map((s, i) => (
                <sup key={i}>
                  <a href="#" onClick={() => showSource(s)}>[{i + 1}]</a>
                </sup>
              ))}
            </p>
          </div>
        ))}
      </div>
      <input value={question} onChange={(e) => setQuestion(e.target.value)} />
      <button onClick={ask}>Ask</button>
    </div>
  );
}
