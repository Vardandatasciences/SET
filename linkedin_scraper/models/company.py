"""Pydantic models for LinkedIn Company data."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class CompanySummary(BaseModel):
    """Summary information for affiliated/showcase companies."""
    linkedin_url: Optional[str] = None
    name: Optional[str] = None
    followers: Optional[str] = None


class Employee(BaseModel):
    """Employee information."""
    name: str
    designation: Optional[str] = None
    linkedin_url: Optional[str] = None


class SocialMediaLink(BaseModel):
    """Social media link information."""
    platform: str
    url: str


class JobListing(BaseModel):
    """Job listing information."""
    title: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    posted_date: Optional[str] = None


class Product(BaseModel):
    """Product/Service information."""
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    linkedin_url: Optional[str] = None
    logo_url: Optional[str] = None


class LifeUpdate(BaseModel):
    """Company life/culture update."""
    type: str  # photo, video, article
    caption: Optional[str] = None
    url: Optional[str] = None
    posted_date: Optional[str] = None


class Company(BaseModel):
    """
    LinkedIn Company model with validation.
    
    Represents a complete LinkedIn company page with all scraped data.
    """
    linkedin_url: str
    name: Optional[str] = None
    about_us: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    headquarters: Optional[str] = None
    founded: Optional[str] = None
    industry: Optional[str] = None
    company_type: Optional[str] = None
    company_size: Optional[str] = None
    specialties: Optional[str] = None
    headcount: Optional[int] = None
    followers_count: Optional[str] = None
    logo_url: Optional[str] = None
    social_media_links: List[SocialMediaLink] = Field(default_factory=list)
    recent_posts: List[Dict[str, Any]] = Field(default_factory=list)  # Post summaries/URLs
    job_listings: List[JobListing] = Field(default_factory=list)
    products: List[Product] = Field(default_factory=list)
    life_updates: List[LifeUpdate] = Field(default_factory=list)
    tags_keywords: List[str] = Field(default_factory=list)
    mission: Optional[str] = None
    values: Optional[str] = None
    showcase_pages: List[CompanySummary] = Field(default_factory=list)
    affiliated_companies: List[CompanySummary] = Field(default_factory=list)
    employees: List[Employee] = Field(default_factory=list)
    
    @field_validator('linkedin_url')
    @classmethod
    def validate_linkedin_url(cls, v: str) -> str:
        """Validate that URL is a LinkedIn company URL."""
        if 'linkedin.com/company/' not in v:
            raise ValueError('Must be a valid LinkedIn company URL (contains /company/)')
        return v
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary.
        
        Returns:
            Dictionary representation of the company
        """
        return self.model_dump()
    
    def to_json(self, **kwargs) -> str:
        """
        Convert to JSON string.
        
        Args:
            **kwargs: Additional arguments for model_dump_json (e.g., indent=2)
        
        Returns:
            JSON string representation
        """
        return self.model_dump_json(**kwargs)
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<Company {self.name}\n"
            f"  Industry: {self.industry}\n"
            f"  Size: {self.company_size}\n"
            f"  Headquarters: {self.headquarters}\n"
            f"  Employees: {len(self.employees) if self.employees else 0}>"
        )
