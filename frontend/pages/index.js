import { useState } from 'react';

export default function Home() {
  const [file, setFile] = useState(null);
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');

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
      body: JSON.stringify({ query: question })
    });
    const json = await res.json();
    setAnswer(json.answer);
  };

  return (
    <div>
      <h1>PDF Assistant</h1>
      <input type="file" onChange={(e) => setFile(e.target.files[0])} />
      <button onClick={upload}>Upload</button>
      <br />
      <input value={question} onChange={(e) => setQuestion(e.target.value)} />
      <button onClick={ask}>Ask</button>
      <p>{answer}</p>
    </div>
  );
}
