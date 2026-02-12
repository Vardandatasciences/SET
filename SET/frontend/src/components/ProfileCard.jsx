import React from 'react'
import './ProfileCard.css'

function ProfileCard({ person, isSelected, onSelect }) {
  const hasPhoto = person.photo_url && person.photo_url.trim() !== ''
  const isClickable = person.linkedin_url && person.linkedin_url.trim() !== ''
  
  // Generate initials from name
  const getInitials = (name) => {
    if (!name) return '?'
    const parts = name.split(' ')
    if (parts.length === 1) return parts[0].charAt(0).toUpperCase()
    return (parts[0].charAt(0) + parts[parts.length - 1].charAt(0)).toUpperCase()
  }
  
  // Get source icon based on source name
  const getSourceIcon = (source) => {
    if (!source) return '🔍'
    const lowerSource = source.toLowerCase()
    if (lowerSource.includes('linkedin')) return '🔗'
    if (lowerSource.includes('google')) return '🌐'
    if (lowerSource.includes('company') || lowerSource.includes('website')) return '🏢'
    if (lowerSource.includes('news')) return '📰'
    return '🔍'
  }
  
  const handleClick = () => {
    if (isClickable && onSelect) {
      onSelect(person)
    }
  }
  
  return (
    <div 
      className={`profile-card ${isSelected ? 'selected' : ''} ${isClickable ? 'clickable' : ''}`}
      onClick={handleClick}
      role={isClickable ? 'button' : 'article'}
      tabIndex={isClickable ? 0 : -1}
      onKeyPress={(e) => {
        if (isClickable && (e.key === 'Enter' || e.key === ' ')) {
          handleClick()
        }
      }}
    >
      {/* Selection Indicator */}
      {isSelected && (
        <div className="selection-badge">
          <span className="checkmark">✓</span>
          Selected
        </div>
      )}
      
      {/* Card Content */}
      <div className="profile-card-content">
        {/* Profile Photo or Avatar */}
        <div className="profile-photo-container">
          {hasPhoto ? (
            <img 
              src={person.photo_url} 
              alt={person.name || 'Profile'} 
              className="profile-photo"
              onError={(e) => {
                // If image fails to load, show initials instead
                e.target.style.display = 'none'
                e.target.nextSibling.style.display = 'flex'
              }}
            />
          ) : null}
          <div 
            className="profile-avatar" 
            style={{ display: hasPhoto ? 'none' : 'flex' }}
          >
            {getInitials(person.name)}
          </div>
        </div>
        
        {/* Profile Info */}
        <div className="profile-info">
          <h3 className="profile-name">{person.name}</h3>
          
          {person.title && person.title !== 'N/A' && (
            <p className="profile-title">{person.title}</p>
          )}
          
          {person.company && person.company !== 'N/A' && (
            <p className="profile-company">
              <span className="company-icon">🏢</span>
              {person.company}
            </p>
          )}
          
          {person.location && person.location.trim() !== '' && (
            <p className="profile-location">
              <span className="location-icon">📍</span>
              {person.location}
            </p>
          )}
          
          {/* Source Badge */}
          <div className="profile-source">
            <span className="source-icon">{getSourceIcon(person.source)}</span>
            <span className="source-text">{person.source || 'Unknown Source'}</span>
          </div>
        </div>
        
        {/* Action Button */}
        {isClickable && !isSelected && (
          <div className="select-button-container">
            <button 
              className="select-button"
              onClick={handleClick}
              type="button"
            >
              Select
            </button>
          </div>
        )}
        
        {isSelected && (
          <div className="selected-indicator">
            <div className="selected-checkmark">✓</div>
          </div>
        )}
      </div>
      
      {/* Click hint */}
      {isClickable && !isSelected && (
        <div className="click-hint">
          Click to select this profile
        </div>
      )}
    </div>
  )
}

export default ProfileCard
