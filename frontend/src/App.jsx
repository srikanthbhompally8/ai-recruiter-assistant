import { useState } from 'react'
import './App.css'

function App() {
  const [count, setCount] = useState(0)

  return (
    <div className="app">
      <header className="app-header">
        <h1>AI Recruiter Assistant</h1>
        <p>Intelligent recruitment platform powered by AWS Bedrock</p>
      </header>

      <main className="app-main">
        <section className="hero">
          <h2>Welcome to the AI Recruiter Assistant</h2>
          <p>Upload resumes, create job descriptions, and find the perfect matches powered by AI.</p>
          <div className="button-group">
            <button className="btn btn-primary">Get Started</button>
            <button className="btn btn-secondary">Learn More</button>
          </div>
        </section>

        <section className="features">
          <h2>Key Features</h2>
          <div className="feature-grid">
            <div className="feature-card">
              <h3>📄 Resume Parsing</h3>
              <p>Automatically extract information from resumes using AI.</p>
            </div>
            <div className="feature-card">
              <h3>🎯 Smart Matching</h3>
              <p>Find the best candidate-job matches using semantic search.</p>
            </div>
            <div className="feature-card">
              <h3>⚡ Fast Processing</h3>
              <p>Get results in seconds with AWS Bedrock powered analysis.</p>
            </div>
          </div>
        </section>
      </main>

      <footer className="app-footer">
        <p>&copy; 2026 TeamitserveUSA. All rights reserved.</p>
      </footer>
    </div>
  )
}

export default App
