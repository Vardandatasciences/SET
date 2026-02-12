import React, { useState } from 'react'
import ResearchForm from './components/ResearchForm'
import ResultsDisplay from './components/ResultsDisplay'
import './App.css'

function App() {
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleResearch = async (formData) => {
    setLoading(true)
    setError(null)
    setResults(null)

    try {
      const response = await fetch('http://localhost:8000/api/research', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Research failed')
      }

      const data = await response.json()
      setResults(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = async (filename) => {
    try {
      const response = await fetch(`http://localhost:8000/api/download/${filename}`)
      if (!response.ok) {
        throw new Error('Download failed')
      }

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="app">
      <div className="container">
        <header className="header">
          <h1>Sales Enablement Intelligence Capsule Tool</h1>
          <p className="subtitle">
            Unified intelligence engine for sales teams conducting prospect research
          </p>
        </header>

        <ResearchForm 
          onSubmit={handleResearch} 
          loading={loading}
        />

        {error && (
          <div className="error-message">
            <strong>Error:</strong> {error}
          </div>
        )}

        {results && (
          <ResultsDisplay 
            results={results} 
            onDownload={handleDownload}
          />
        )}
      </div>
    </div>
  )
}

export default App

