import React, { useState } from 'react'
import './ResultsDisplay.css'

function ResultsDisplay({ results, onDownload }) {
  const [expandedSection, setExpandedSection] = useState(null)
  const intelligence = results?.intelligence || {}

  const toggleSection = (section) => {
    setExpandedSection(expandedSection === section ? null : section)
  }

  const getFileName = () => {
    const filePath = results?.file_path || ''
    return filePath.split('/').pop() || 'document'
  }

  const renderOrganizationContent = () => {
    return (
      <>
        <Section
          title="Company Background"
          content={intelligence.company_background}
          expanded={expandedSection === 'background'}
          onToggle={() => toggleSection('background')}
        />
        
        <Section
          title="Leadership Intelligence"
          content={intelligence.leadership_intelligence}
          expanded={expandedSection === 'leadership'}
          onToggle={() => toggleSection('leadership')}
        />
        
        <Section
          title="Financial Information"
          content={intelligence.financial_information}
          expanded={expandedSection === 'financial'}
          onToggle={() => toggleSection('financial')}
        />
        
        <Section
          title="News Intelligence"
          content={intelligence.news_intelligence}
          expanded={expandedSection === 'news'}
          onToggle={() => toggleSection('news')}
        />
        
        <Section
          title="Challenges & Risks"
          content={intelligence.challenges_risks}
          expanded={expandedSection === 'challenges'}
          onToggle={() => toggleSection('challenges')}
        />
        
        <Section
          title="Strategic Priorities"
          content={intelligence.strategic_priorities}
          expanded={expandedSection === 'priorities'}
          onToggle={() => toggleSection('priorities')}
        />
      </>
    )
  }

  const renderIndividualContent = () => {
    return (
      <>
        <Section
          title="Professional Background"
          content={intelligence.professional_background}
          expanded={expandedSection === 'background'}
          onToggle={() => toggleSection('background')}
        />
        
        <Section
          title="Education"
          content={intelligence.education}
          expanded={expandedSection === 'education'}
          onToggle={() => toggleSection('education')}
        />
        
        <Section
          title="Company Information"
          content={intelligence.company_information}
          expanded={expandedSection === 'company'}
          onToggle={() => toggleSection('company')}
        />
        
        <Section
          title="Public Presence"
          content={intelligence.public_presence}
          expanded={expandedSection === 'presence'}
          onToggle={() => toggleSection('presence')}
        />
      </>
    )
  }

  return (
    <div className="results-container">
      <div className="results-header">
        <h2>Research Results</h2>
        <button
          className="download-button"
          onClick={() => onDownload(getFileName())}
        >
          Download {results?.intelligence?.research_type === 'organization' ? 'Capsule' : 'Report'}
        </button>
      </div>

      <div className="intelligence-sections">
        {intelligence.research_type === 'organization'
          ? renderOrganizationContent()
          : renderIndividualContent()}
      </div>

      {intelligence.sources && intelligence.sources.length > 0 && (
        <div className="sources-section">
          <h3>Sources</h3>
          <ul>
            {intelligence.sources.map((source, index) => (
              <li key={index}>{source}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

function Section({ title, content, expanded, onToggle }) {
  const renderContent = () => {
    if (!content) return <p className="no-data">No information available.</p>
    
    if (typeof content === 'string') {
      return <p>{content}</p>
    }
    
    if (typeof content === 'object') {
      if (content.summary) {
        return (
          <div>
            <p>{content.summary}</p>
            {content.key_executives && (
              <div className="executives-list">
                <strong>Key Executives:</strong>
                <ul>
                  {content.key_executives.map((exec, idx) => (
                    <li key={idx}>
                      {exec.role}: {exec.name}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {content.positive_news && content.positive_news.length > 0 && (
              <div className="news-list">
                <strong>Positive News:</strong>
                <ul>
                  {content.positive_news.map((item, idx) => (
                    <li key={idx}>
                      [{item.date}] {item.summary}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {content.negative_news && content.negative_news.length > 0 && (
              <div className="news-list negative">
                <strong>Negative News:</strong>
                <ul>
                  {content.negative_news.map((item, idx) => (
                    <li key={idx}>
                      [{item.date}] {item.summary}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )
      }
      return <pre>{JSON.stringify(content, null, 2)}</pre>
    }
    
    return <p>{String(content)}</p>
  }

  return (
    <div className="intelligence-section">
      <div className="section-header" onClick={onToggle}>
        <h3>{title}</h3>
        <span className="toggle-icon">{expanded ? '−' : '+'}</span>
      </div>
      {expanded && (
        <div className="section-content">
          {renderContent()}
        </div>
      )}
    </div>
  )
}

export default ResultsDisplay

