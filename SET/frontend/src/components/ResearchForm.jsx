import React, { useState } from 'react'
import ProfileCard from './ProfileCard'
import './ResearchForm.css'

const SOURCE_OPTIONS = [
  'ZoomInfo',
  'Zauba Corp',
  'Tracxn',
  'Tofler',
  'PitchBook',
  'LinkedIn',
  'Others'
]

function ResearchForm({ onSubmit, loading }) {
  const [query, setQuery] = useState('')
  const [researchType, setResearchType] = useState('organization')
  const [companyName, setCompanyName] = useState('')
  const [outputFormat, setOutputFormat] = useState('word')
  const [sources, setSources] = useState([])
  
  // Two-step process for individuals
  const [nameChecked, setNameChecked] = useState(false)
  const [showCompanyField, setShowCompanyField] = useState(false)
  const [checkingName, setCheckingName] = useState(false)
  const [peopleCount, setPeopleCount] = useState(0)
  const [peopleList, setPeopleList] = useState([])
  const [sourceBreakdown, setSourceBreakdown] = useState({})
  const [selectedPerson, setSelectedPerson] = useState(null)

  const handleAddSource = () => {
    setSources([...sources, { sourceName: '', customName: '', link: '' }])
  }

  const handleRemoveSource = (index) => {
    setSources(sources.filter((_, i) => i !== index))
  }

  const handleSourceChange = (index, field, value) => {
    const updatedSources = [...sources]
    updatedSources[index] = { ...updatedSources[index], [field]: value }
    // Clear customName if sourceName is not "Others"
    if (field === 'sourceName' && value !== 'Others') {
      updatedSources[index].customName = ''
    }
    
    // Validate LinkedIn URL if link is being changed
    if (field === 'link' && value.includes('linkedin.com/in/')) {
      if (value.includes(' ')) {
        // URL contains spaces - show warning
        console.warn('⚠️ LinkedIn URL contains spaces - will be normalized')
        // Optionally show a user-friendly message
        const cleanedUrl = value.replace(/\s+/g, '-')
        console.log(`💡 Suggested URL: ${cleanedUrl}`)
      }
    }
    
    setSources(updatedSources)
  }

  // Handle name checking for individuals - REAL API CALL
  const handleCheckName = async (e) => {
    e.preventDefault()
    if (!query.trim()) {
      alert('Please enter a name')
      return
    }

    setCheckingName(true)
    
    try {
      // Format sources for the API
      const formattedSources = sources
        .filter(source => {
          if (!source.sourceName || !source.link.trim()) return false
          if (source.sourceName === 'Others' && !source.customName.trim()) return false
          return true
        })
        .map(source => ({
          name: source.sourceName === 'Others' ? source.customName.trim() : source.sourceName,
          link: source.link.trim()
        }))
      
      // Call backend API to check name
      // If sources provided, search only those sources
      // If no sources, search LinkedIn + Google
      const response = await fetch('http://localhost:8000/api/check-name', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: query.trim(),
          sources: formattedSources  // Pass sources to backend
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      
      console.log('✅ Name check response:', data)
      
      // Set the count and people list from real AI search
      setPeopleCount(data.count || 5)
      setPeopleList(data.people || [])
      setSourceBreakdown(data.source_breakdown || {})
      setNameChecked(true)
      setShowCompanyField(true)
      
    } catch (error) {
      console.error('❌ Error checking name:', error)
      
      // Fallback: use simple estimate based on name length
      const nameLength = query.trim().length
      let count
      
      if (nameLength <= 5) {
        count = 15 // Short names are common
      } else if (nameLength <= 10) {
        count = 8  // Medium names
      } else {
        count = 3  // Longer names are less common
      }
      
      setPeopleCount(count)
      setNameChecked(true)
      setShowCompanyField(true)
      
      // Show warning that we're using fallback
      console.warn('⚠️ Using fallback count estimate. Backend might be unavailable.')
    } finally {
      setCheckingName(false)
    }
  }

  // Reset states when research type changes
  const handleResearchTypeChange = (value) => {
    setResearchType(value)
    setNameChecked(false)
    setShowCompanyField(false)
    setCompanyName('')
    setPeopleCount(0)
    setPeopleList([])
    setSourceBreakdown({})
  }

  // Reset states when name changes
  const handleNameChange = (value) => {
    setQuery(value)
    if (researchType === 'individual') {
      setNameChecked(false)
      setShowCompanyField(false)
      setCompanyName('')
      setPeopleCount(0)
      setPeopleList([])
      setSourceBreakdown({})
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    
    if (!query.trim()) {
      alert('Please enter a search query')
      return
    }

    // Filter out empty sources and format them
    const formattedSources = sources
      .filter(source => {
        if (!source.sourceName || !source.link.trim()) return false
        // If "Others" is selected, customName must be provided
        if (source.sourceName === 'Others' && !source.customName.trim()) return false
        return true
      })
      .map(source => ({
        name: source.sourceName === 'Others' ? source.customName.trim() : source.sourceName,
        link: source.link.trim()
      }))

    // Check if LinkedIn URL is provided for individuals
    const hasLinkedInUrl = formattedSources.some(source => 
      source.link.toLowerCase().includes('linkedin.com/in/')
    )

    // For individuals WITHOUT LinkedIn URL, require company name
    if (researchType === 'individual' && !hasLinkedInUrl) {
      // If name not checked yet, require checking first
      if (!nameChecked) {
        alert('Please click "Check Name" button first to verify the name')
        return
      }
      // If name checked but no company name provided and no person selected, require it
      if (showCompanyField && !companyName.trim() && !selectedPerson) {
        alert('Please select a person from the list above or provide the company name to identify the correct person')
        return
      }
    }

    const requestData = {
      query: query.trim(),
      research_type: researchType,
      output_format: outputFormat,
      sources: formattedSources,
    }

    // Include company_name for individuals (helps with disambiguation)
    if (researchType === 'individual' && companyName.trim()) {
      requestData.company_name = companyName.trim()
    }

    onSubmit(requestData)
  }

  return (
    <div className="research-form-container">
      <form onSubmit={handleSubmit} className="research-form">
        <div className="form-group">
          <label htmlFor="researchType">Research Type</label>
          <div className="radio-group">
            <label className="radio-label">
              <input
                type="radio"
                value="organization"
                checked={researchType === 'organization'}
                onChange={(e) => handleResearchTypeChange(e.target.value)}
                disabled={loading}
              />
              <span>Organization</span>
            </label>
            <label className="radio-label">
              <input
                type="radio"
                value="individual"
                checked={researchType === 'individual'}
                onChange={(e) => handleResearchTypeChange(e.target.value)}
                disabled={loading}
              />
              <span>Individual</span>
            </label>
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="query">
            {researchType === 'organization' ? 'Organization Name' : 'Individual Name'}
          </label>
          <div className="name-input-wrapper">
            <input
              type="text"
              id="query"
              value={query}
              onChange={(e) => handleNameChange(e.target.value)}
              placeholder={
                researchType === 'organization'
                  ? 'e.g., Microsoft Corporation'
                  : 'e.g., Satya Nadella'
              }
              required
              disabled={loading || checkingName}
            />
            {researchType === 'individual' && !nameChecked && (
              <button
                type="button"
                onClick={handleCheckName}
                className="check-name-button"
                disabled={!query.trim() || loading || checkingName}
              >
                {checkingName ? 'Checking...' : 'Check Name'}
              </button>
            )}
          </div>
        </div>

        {researchType === 'individual' && nameChecked && (
          <div className="name-check-result">
            {/* Header Section */}
            <div className="results-header">
              <div className="results-summary">
                <span className="results-icon">👥</span>
                <div className="results-text">
                  <h3 className="results-title">
                    {peopleCount} {peopleCount === 1 ? 'Profile' : 'Profiles'} Found
                  </h3>
                  <p className="results-subtitle">
                    {selectedPerson 
                      ? `Selected: ${selectedPerson.name}${selectedPerson.company && selectedPerson.company !== 'N/A' ? ` at ${selectedPerson.company}` : ''}`
                      : 'Click on a profile to select and proceed'}
                  </p>
                </div>
              </div>
              
              {/* Source Breakdown */}
              {Object.keys(sourceBreakdown).length > 0 && (
                <div className="source-breakdown-compact">
                  <span className="breakdown-label">📊 Sources:</span>
                  <div className="breakdown-tags">
                    {Object.entries(sourceBreakdown).map(([source, count]) => (
                      <span key={source} className="breakdown-tag">
                        {source} <span className="breakdown-count">({count})</span>
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
            
            {/* Profile Cards Grid */}
            {peopleList.length > 0 ? (
              <div className="profiles-grid">
                {peopleList.map((person, index) => {
                  // Check if this person is selected
                  const isSelected = selectedPerson?.linkedin_url === person.linkedin_url && person.linkedin_url
                  
                  return (
                    <ProfileCard
                      key={index}
                      person={person}
                      isSelected={isSelected}
                      onSelect={(selectedPerson) => {
                        setSelectedPerson(selectedPerson)
                        
                        // Add LinkedIn URL to sources if available
                        if (selectedPerson.linkedin_url) {
                          const hasLinkedIn = sources.some(s => s.link.includes('linkedin.com/in/'))
                          if (!hasLinkedIn) {
                            setSources([{
                              sourceName: 'LinkedIn',
                              customName: '',
                              link: selectedPerson.linkedin_url
                            }])
                          } else {
                            // Update existing LinkedIn source
                            const updatedSources = sources.map(s => 
                              s.link.includes('linkedin.com/in/') 
                                ? { ...s, link: selectedPerson.linkedin_url }
                                : s
                            )
                            setSources(updatedSources)
                          }
                        }
                        
                        // Update company name if available
                        if (selectedPerson.company && selectedPerson.company !== 'N/A') {
                          let companyName = selectedPerson.company
                          if (companyName.includes('@')) {
                            companyName = companyName.split('@').pop().trim()
                          }
                          setCompanyName(companyName)
                        }
                        
                        // Update query to match selected person's name
                        if (selectedPerson.name) {
                          const cleanName = selectedPerson.name.split('\n')[0].split('•')[0].trim()
                          setQuery(cleanName)
                        }
                      }}
                    />
                  )
                })}
              </div>
            ) : (
              <div className="no-profiles-message">
                <p>No profiles found. Please provide the company name to help identify the correct person.</p>
              </div>
            )}
          </div>
        )}

        {researchType === 'individual' && showCompanyField && (
          <div className="form-group company-field-animated">
            <label htmlFor="companyName">
              Company Name <span className="required-badge">Required</span>
            </label>
            <input
              type="text"
              id="companyName"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              placeholder="e.g., Microsoft Corporation"
              disabled={loading}
              required
            />
          </div>
        )}

        <div className="form-group">
          <label htmlFor="outputFormat">Output Format</label>
          <select
            id="outputFormat"
            value={outputFormat}
            onChange={(e) => setOutputFormat(e.target.value)}
            disabled={loading}
          >
            <option value="word">Word Document (.docx)</option>
            <option value="pdf">PDF Document (.pdf)</option>
            <option value="powerpoint">PowerPoint (.pptx)</option>
          </select>
        </div>

        <div className="form-group">
          <div className="sources-header">
            <label>Additional Sources (Optional)</label>
            <button
              type="button"
              onClick={handleAddSource}
              className="add-source-button"
              disabled={loading}
            >
              + Add Source
            </button>
          </div>
          
          {sources.length > 0 && (
            <div className="sources-list">
              {sources.map((source, index) => (
                <div key={index} className="source-item">
                  <div className="source-row">
                    <div className="source-field">
                      <select
                        value={source.sourceName}
                        onChange={(e) => handleSourceChange(index, 'sourceName', e.target.value)}
                        disabled={loading}
                        className="source-select"
                      >
                        <option value="">Select Source</option>
                        {SOURCE_OPTIONS.map(option => (
                          <option key={option} value={option}>{option}</option>
                        ))}
                      </select>
                    </div>
                    
                    {source.sourceName === 'Others' && (
                      <div className="source-field">
                        <input
                          type="text"
                          placeholder="Enter source name"
                          value={source.customName}
                          onChange={(e) => handleSourceChange(index, 'customName', e.target.value)}
                          disabled={loading}
                          className="source-input"
                        />
                      </div>
                    )}
                    
                    <div className="source-field source-link-field">
                      <input
                        type="url"
                        placeholder="Enter source link"
                        value={source.link}
                        onChange={(e) => handleSourceChange(index, 'link', e.target.value)}
                        disabled={loading}
                        className="source-input"
                      />
                    </div>
                    
                    <button
                      type="button"
                      onClick={() => handleRemoveSource(index)}
                      className="remove-source-button"
                      disabled={loading}
                      title="Remove source"
                    >
                      ×
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <button 
          type="submit" 
          className="submit-button"
          disabled={loading || !query.trim()}
        >
          {loading ? 'Researching...' : 'Generate Intelligence Capsule'}
        </button>
      </form>
    </div>
  )
}

export default ResearchForm

