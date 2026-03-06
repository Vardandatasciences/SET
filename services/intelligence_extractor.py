import re
import json
from typing import Dict, Any, Literal, List
from datetime import datetime


class IntelligenceExtractor:
    """
    Extracts structured intelligence from raw research data
    """
    
    async def extract_intelligence(
        self, 
        raw_data: Dict[str, Any],
        research_type: Literal["individual", "organization"]
    ) -> Dict[str, Any]:
        """
        Extract structured intelligence from raw Perplexity response
        """
        print("\n" + "="*80)
        print("🔍 INTELLIGENCE EXTRACTION STARTED")
        print("="*80)
        print(f"📊 Research Type: {research_type}")
        print(f"📝 Raw Response Length: {len(raw_data.get('raw_response', ''))} characters")
        print(f"📌 Raw Response Preview (first 500 chars):")
        print("-"*80)
        print(raw_data.get('raw_response', '')[:500])
        print("-"*80)
        
        if research_type == "individual":
            result = self._extract_individual_intelligence(raw_data)
        else:
            result = self._extract_organization_intelligence(raw_data)
        
        print("\n✅ INTELLIGENCE EXTRACTION COMPLETED")
        print("="*80 + "\n")
        return result
    
    def _extract_individual_intelligence(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured intelligence for individuals
        """
        content = raw_data.get("raw_response", "")
        
        print("\n🔨 EXTRACTING INDIVIDUAL SECTIONS:")
        print("-"*80)
        
        # Check if there's LinkedIn data at the start
        has_linkedin_data = "LINKEDIN PROFILE DATA" in content
        linkedin_data = {}
        
        if has_linkedin_data:
            print("\n📋 DETECTED LINKEDIN DATA - Extracting structured sections...")
            linkedin_data = self._extract_linkedin_individual_data(content)
            print(f"   ✓ LinkedIn Name: {linkedin_data.get('name', 'N/A')}")
            print(f"   ✓ LinkedIn About: {len(linkedin_data.get('about', ''))} chars")
            print(f"   ✓ LinkedIn Experience: {len(linkedin_data.get('experience', ''))} chars")
            print(f"   ✓ LinkedIn Education: {len(linkedin_data.get('education', ''))} chars")
            print(f"   ✓ LinkedIn Certifications: {len(linkedin_data.get('certifications', ''))} chars")
        
        # First, let's see what section headers actually exist in the content
        print("\n📋 ANALYZING CONTENT STRUCTURE:")
        section_headers = re.findall(r'^#{1,3}\s*\d*\.?\s*(.+)$', content, re.MULTILINE)
        print(f"   Found {len(section_headers)} section headers:")
        for idx, header in enumerate(section_headers[:10], 1):
            print(f"   [{idx}] {header.strip()}")
        if len(section_headers) > 10:
            print(f"   ... and {len(section_headers) - 10} more")
        
        print("\n📄 EXTRACTING OLLAMA AI SECTIONS:")
        print("-"*80)
        
        professional_bg = self._extract_section(content, "Professional Background", "Education")
        
        # If LinkedIn data exists, use it and optionally add Ollama insights
        if linkedin_data.get('experience') or linkedin_data.get('about'):
            linkedin_prof = []
            
            if linkedin_data.get('about'):
                linkedin_prof.append(f"**Professional Summary:**\n{linkedin_data['about']}\n")
            
            if linkedin_data.get('experience'):
                linkedin_prof.append(f"**Work Experience:**\n{linkedin_data['experience']}")
            
            # Only add Ollama data if it's not just "Not found"
            if professional_bg and not self._is_empty_section(professional_bg):
                linkedin_prof.append(f"\n**Additional Research:**\n{professional_bg}")
            
            professional_bg = '\n\n'.join(linkedin_prof)
        
        print(f"✓ Professional Background: {len(professional_bg)} chars extracted")
        if professional_bg:
            print(f"  Preview: {professional_bg[:200]}...")
            print(f"\n  📄 FULL CONTENT:")
            print("  " + "="*76)
            print("  " + professional_bg.replace("\n", "\n  "))
            print("  " + "="*76)
        else:
            print("  ⚠️  EMPTY!")
        
        education = self._extract_section(content, "Education", "Company Information")
        
        # If LinkedIn data exists, format it properly
        if linkedin_data.get('education') or linkedin_data.get('certifications'):
            linkedin_edu = []
            
            if linkedin_data.get('education'):
                linkedin_edu.append(f"**Education:**\n{linkedin_data['education']}")
            
            if linkedin_data.get('certifications'):
                linkedin_edu.append(f"**Certifications & Training:**\n{linkedin_data['certifications']}")
            
            # Only add Ollama data if it's not just "Not found"
            if education and not self._is_empty_section(education):
                linkedin_edu.append(f"\n**Additional Research:**\n{education}")
            
            education = '\n\n'.join(linkedin_edu)
        
        print(f"\n✓ Education: {len(education)} chars extracted")
        if education:
            print(f"  Preview: {education[:200]}...")
        else:
            print("  ⚠️  EMPTY!")
        
        company_info = self._extract_section(content, "Company Information", "Public Presence")
        
        # If LinkedIn data has company info, format it nicely
        if linkedin_data.get('company'):
            company_parts = [linkedin_data['company']]
            
            # Only add Ollama data if it's not just "Not found"
            if company_info and not self._is_empty_section(company_info):
                company_parts.append(f"\n**Additional Research:**\n{company_info}")
            
            company_info = '\n\n'.join(company_parts)
        
        print(f"\n✓ Company Information: {len(company_info)} chars extracted")
        if company_info:
            print(f"  Preview: {company_info[:200]}...")
        else:
            print("  ⚠️  EMPTY!")
        
        public_presence = self._extract_section(content, "Public Presence", "Professional Network")
        print(f"\n✓ Public Presence: {len(public_presence)} chars extracted")
        if public_presence:
            print(f"  Preview: {public_presence[:200]}...")
            print(f"\n  📄 FULL CONTENT:")
            print("  " + "="*76)
            print("  " + public_presence.replace("\n", "\n  "))
            print("  " + "="*76)
        else:
            print("  ⚠️  EMPTY!")
        
        professional_network = self._extract_section(content, "Professional Network", "Recent Activity")
        print(f"\n✓ Professional Network: {len(professional_network)} chars extracted")
        if professional_network:
            print(f"  Preview: {professional_network[:200]}...")
            print(f"\n  📄 FULL CONTENT:")
            print("  " + "="*76)
            print("  " + professional_network.replace("\n", "\n  "))
            print("  " + "="*76)
        else:
            print("  ⚠️  EMPTY!")
        
        recent_activity = self._extract_section(content, "Recent Activity", None)
        print(f"\n✓ Recent Activity: {len(recent_activity)} chars extracted")
        if recent_activity:
            print(f"  Preview: {recent_activity[:200]}...")
            print(f"\n  📄 FULL CONTENT:")
            print("  " + "="*76)
            print("  " + recent_activity.replace("\n", "\n  "))
            print("  " + "="*76)
        else:
            print("  ⚠️  EMPTY!")
        
        print("-"*80)
        
        intelligence = {
            "query": raw_data.get("query", ""),
            "research_type": "individual",
            "professional_background": professional_bg,
            "education": education,
            "company_information": company_info,
            "public_presence": public_presence,
            "professional_network": professional_network,
            "recent_activity": recent_activity,
            "sources": raw_data.get("sources", []),
            "raw_content": content
        }
        
        return intelligence
    
    def _extract_linkedin_individual_data(self, content: str) -> Dict[str, Any]:
        """
        Extract LinkedIn-specific data from the combined response
        """
        linkedin_data = {}
        
        # Extract LinkedIn profile section
        linkedin_start = content.find("LINKEDIN PROFILE DATA")
        if linkedin_start == -1:
            return linkedin_data
        
        # Find where Ollama data starts
        ollama_start = content.find("ADDITIONAL WEB INTELLIGENCE")
        if ollama_start == -1:
            linkedin_section = content[linkedin_start:]
        else:
            linkedin_section = content[linkedin_start:ollama_start]
        
        # Extract name
        name_match = re.search(r'Name:\s*(.+)', linkedin_section)
        if name_match:
            linkedin_data['name'] = name_match.group(1).strip()
        
        # Extract location
        location_match = re.search(r'Location:\s*(.+)', linkedin_section)
        if location_match:
            linkedin_data['location'] = location_match.group(1).strip()
        
        # Extract about section
        about_match = re.search(r'ABOUT:\s*([\s\S]+?)(?=\n(?:EXPERIENCE:|EDUCATION:|CERTIFICATIONS:|====))', linkedin_section)
        if about_match:
            linkedin_data['about'] = about_match.group(1).strip()
        
        # Extract and format experience
        exp_match = re.search(r'EXPERIENCE:\s*([\s\S]+?)(?=\n(?:EDUCATION:|CERTIFICATIONS:|====))', linkedin_section)
        if exp_match:
            exp_text = exp_match.group(1).strip()
            # Format experience nicely
            formatted_exp = self._format_linkedin_experience(exp_text)
            linkedin_data['experience'] = formatted_exp
        
        # Extract and format education
        edu_match = re.search(r'EDUCATION:\s*([\s\S]+?)(?=\n(?:CERTIFICATIONS:|====))', linkedin_section)
        if edu_match:
            edu_text = edu_match.group(1).strip()
            # Format education nicely
            formatted_edu = self._format_linkedin_education(edu_text)
            linkedin_data['education'] = formatted_edu
        
        # Extract and format certifications
        cert_match = re.search(r'CERTIFICATIONS:\s*([\s\S]+?)(?=\n====)', linkedin_section)
        if cert_match:
            cert_text = cert_match.group(1).strip()
            # Format certifications nicely
            formatted_cert = self._format_linkedin_certifications(cert_text)
            linkedin_data['certifications'] = formatted_cert
        
        # Create formatted company info from experience and about
        company_parts = []
        if linkedin_data.get('experience'):
            # Extract current company from first experience entry
            current_exp = linkedin_data['experience'].split('\n')[0] if linkedin_data.get('experience') else ''
            if 'at' in current_exp:
                company_parts.append(f"**Current Role:** {current_exp}")
        
        if linkedin_data.get('location'):
            company_parts.append(f"**Location:** {linkedin_data['location']}")
        
        if linkedin_data.get('about'):
            company_parts.append(f"\n**Professional Summary:**\n{linkedin_data['about']}")
        
        if company_parts:
            linkedin_data['company'] = '\n'.join(company_parts)
        
        return linkedin_data
    
    def _format_linkedin_experience(self, text: str) -> str:
        """Format LinkedIn experience entries"""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        formatted = []
        
        for line in lines:
            if line.startswith('•'):
                line = line[1:].strip()
            formatted.append(f"• {line}")
        
        return '\n'.join(formatted)
    
    def _format_linkedin_education(self, text: str) -> str:
        """Format LinkedIn education entries"""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        formatted = []
        current_entry = []
        
        for line in lines:
            # Remove bullet points
            if line.startswith('•'):
                line = line[1:].strip()
            
            # Skip "Transformers" entries (these seem to be data artifacts)
            if line == "Transformers":
                continue
            
            # If line contains a date pattern or is long (likely a school name), start new entry
            if re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}', line) or len(line) > 50:
                if current_entry:
                    formatted.append('\n'.join(current_entry))
                    formatted.append('')  # Add blank line between entries
                    current_entry = []
                current_entry.append(f"• {line}")
            else:
                if current_entry:
                    current_entry.append(f"  {line}")
                else:
                    current_entry.append(f"• {line}")
        
        if current_entry:
            formatted.append('\n'.join(current_entry))
        
        return '\n'.join(formatted)
    
    def _format_linkedin_certifications(self, text: str) -> str:
        """Format LinkedIn certification entries"""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        formatted = []
        
        for line in lines:
            if line.startswith('•'):
                line = line[1:].strip()
            
            # Check if it's an issuer line (starts with "Issued:")
            if line.startswith('Issued:'):
                formatted.append(f"  {line}")
            else:
                formatted.append(f"• {line}")
        
        return '\n'.join(formatted)
    
    def _extract_organization_intelligence(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured intelligence for organizations
        """
        content = raw_data.get("raw_response", "")

        # If the response is only LinkedIn company text (no AI‑generated
        # sections like "Company Background"), we still want to return a
        # nicely structured JSON object. Detect the dedicated LinkedIn
        # company block and parse it into fields first.
        linkedin_company_block = ""
        if "LINKEDIN COMPANY DATA" in content:
            start = content.find("LINKEDIN COMPANY DATA")
            end_marker = "ADDITIONAL WEB INTELLIGENCE"
            end = content.find(end_marker, start)
            if end == -1:
                end = len(content)
            linkedin_company_block = content[start:end]

        company_from_linkedin: Dict[str, Any] = {}
        if linkedin_company_block:
            company_from_linkedin = self._parse_linkedin_company_block(
                linkedin_company_block
            )

        # Default extraction via explicitly marked sections (when present)
        company_background = self._extract_section(
            content, "Company Background", "Leadership Intelligence"
        )
        leadership_intel = self._extract_leadership_intelligence(content)
        financial_info = self._extract_financial_information(content)
        news_intel = self._extract_news_intelligence(content)
        challenges_risks = self._extract_challenges_risks(content)
        strategic_priorities = self._extract_section(
            content, "Strategic Priorities", "Recent Activity"
        )
        recent_activity = self._extract_section(
            content, "Recent Activity", "Additional Sources"
        )
        additional_sources_info = self._extract_section(
            content, "Additional Sources Information", None
        )

        # When AI sections are missing, synthesize them from the
        # LinkedIn company metadata we just parsed.
        if company_from_linkedin:
            # Company background: core facts + about + specialties.
            if not company_background:
                lines = []
                name = company_from_linkedin.get("company")
                if name:
                    lines.append(f"Company: {name}")
                website = company_from_linkedin.get("website")
                if website:
                    lines.append(f"Website: {website}")
                industry = company_from_linkedin.get("industry")
                if industry:
                    lines.append(f"Industry: {industry}")
                size = company_from_linkedin.get("company_size")
                if size:
                    lines.append(f"Company size: {size}")
                hq = company_from_linkedin.get("headquarters")
                if hq:
                    lines.append(f"Headquarters: {hq}")
                founded = company_from_linkedin.get("founded")
                if founded:
                    lines.append(f"Founded: {founded}")

                about = company_from_linkedin.get("about")
                if about:
                    if lines:
                        lines.append("")
                    lines.append("About:")
                    lines.append(about)

                specialties = company_from_linkedin.get("specialties")
                if specialties:
                    if lines:
                        lines.append("")
                    lines.append("Specialties:")
                    lines.append(specialties)

                company_background = "\n".join(lines).strip()

            # Leadership intelligence: summarize key employees if AI section
            # is empty.
            if not leadership_intel.get("summary") and company_from_linkedin.get(
                "key_employees"
            ):
                employees_text = company_from_linkedin["key_employees"]
                leadership_intel["summary"] = (
                    "Key employees from LinkedIn company page:\n" + employees_text
                )

        intelligence = {
            "query": raw_data.get("query", ""),
            "research_type": "organization",
            "company_background": company_background,
            "leadership_intelligence": leadership_intel,
            "financial_information": financial_info,
            "news_intelligence": news_intel,
            "challenges_risks": challenges_risks,
            "strategic_priorities": strategic_priorities,
            "recent_activity": recent_activity,
            "additional_sources_info": additional_sources_info,
            "sources": raw_data.get("sources", []),
            "raw_content": content,
        }

        # Expose parsed LinkedIn fields (if any) as top‑level helpers.
        if company_from_linkedin:
            intelligence["company_name"] = company_from_linkedin.get("company")
            intelligence["linkedin_company"] = company_from_linkedin

        return intelligence

    def _parse_linkedin_company_block(self, text: str) -> Dict[str, Any]:
        """
        Parse the 'LINKEDIN COMPANY DATA' text block into a structured dict.

        This is used when AI‑generated sections like 'Company Background'
        are missing so we can still return a meaningful, structured payload.
        """
        lines = [line.strip() for line in text.splitlines()]
        result: Dict[str, Any] = {}

        about_lines: list[str] = []
        specialties_lines: list[str] = []
        key_emp_lines: list[str] = []

        mode: str | None = None

        for line in lines:
            if not line:
                continue

            # Basic key:value pairs
            m = re.match(r"Company:\s*(.+)", line)
            if m:
                result["company"] = m.group(1).strip()
                continue

            m = re.match(r"Website:\s*(.+)", line)
            if m:
                result["website"] = m.group(1).strip()
                continue

            m = re.match(r"Industry:\s*(.+)", line)
            if m:
                result["industry"] = m.group(1).strip()
                continue

            m = re.match(r"Company Size:\s*(.+)", line)
            if m:
                result["company_size"] = m.group(1).strip()
                continue

            m = re.match(r"Headquarters:\s*(.+)", line)
            if m:
                result["headquarters"] = m.group(1).strip()
                continue

            m = re.match(r"Founded:\s*(.+)", line)
            if m:
                result["founded"] = m.group(1).strip()
                continue

            m = re.match(r"LinkedIn:\s*(.+)", line)
            if m:
                result["linkedin_url"] = m.group(1).strip()
                continue

            # Section markers
            if line.startswith("ABOUT:"):
                mode = "about"
                continue
            if line.startswith("SPECIALTIES:"):
                mode = "specialties"
                continue
            if line.startswith("KEY EMPLOYEES"):
                mode = "key_employees"
                continue
            if line.startswith("="):
                mode = None
                continue

            # Section content
            if mode == "about":
                about_lines.append(line)
            elif mode == "specialties":
                specialties_lines.append(line)
            elif mode == "key_employees":
                key_emp_lines.append(line)

        if about_lines:
            result["about"] = "\n".join(about_lines).strip()
        if specialties_lines:
            # Join and lightly clean up any comma‑separated characters.
            result["specialties"] = " ".join(specialties_lines).strip()
        if key_emp_lines:
            result["key_employees"] = "\n".join(key_emp_lines).strip()

        return result
    
    def _extract_section(self, content: str, start_marker: str, end_marker: str = None) -> str:
        """
        Extract a section from content between two markers
        """
        if not start_marker:
            return ""
        
        # Find start position - now also matches "## 1. Professional Background" format
        start_pattern = re.compile(
            rf"({re.escape(start_marker)}|##\s*\d*\.?\s*{re.escape(start_marker)}|###\s*\d*\.?\s*{re.escape(start_marker)}|\*\*{re.escape(start_marker)}\*\*)", 
            re.IGNORECASE
        )
        start_match = start_pattern.search(content)
        
        if not start_match:
            print(f"      ⚠️  Section '{start_marker}' NOT FOUND in content")
            return ""
        
        start_pos = start_match.end()
        print(f"      ✓ Found section '{start_marker}' at position {start_match.start()}")
        
        # Find end position
        if end_marker:
            end_pattern = re.compile(
                rf"({re.escape(end_marker)}|##\s*\d*\.?\s*{re.escape(end_marker)}|###\s*\d*\.?\s*{re.escape(end_marker)}|\*\*{re.escape(end_marker)}\*\*)", 
                re.IGNORECASE
            )
            end_match = end_pattern.search(content, start_pos)
            if end_match:
                extracted = content[start_pos:end_match.start()].strip()
                print(f"      ✓ Extracted {len(extracted)} chars (ended at '{end_marker}')")
                return extracted
        
        # If no end marker, take until next ## or end of content
        next_section = re.search(r'\n##\s+', content[start_pos:])
        if next_section:
            extracted = content[start_pos:start_pos + next_section.start()].strip()
            print(f"      ✓ Extracted {len(extracted)} chars (ended at next section)")
            return extracted
        
        extracted = content[start_pos:].strip()
        print(f"      ✓ Extracted {len(extracted)} chars (to end of content)")
        return extracted
    
    def _extract_leadership_intelligence(self, content: str) -> Dict[str, Any]:
        """
        Extract structured leadership intelligence including executive messages
        """
        section = self._extract_section(content, "Leadership Intelligence", "Financial Information")
        
        # Try to extract individual leaders
        leaders = []
        leader_pattern = re.compile(r'(CEO|CTO|CFO|COO|CMO|CIO|President|Founder)[:\-]?\s*([^\n]+)', re.IGNORECASE)
        for match in leader_pattern.finditer(section):
            leaders.append({
                "role": match.group(1),
                "name": match.group(2).strip()
            })
        
        # Extract executive messages
        executive_messages = {
            "ceo_message": self._extract_executive_message(section, "CEO"),
            "cfo_message": self._extract_executive_message(section, "CFO"),
            "cto_message": self._extract_executive_message(section, "CTO"),
            "cio_message": self._extract_executive_message(section, "CIO"),
            "audit_committee_message": self._extract_executive_message(section, "Audit Committee"),
            "advisory_board_message": self._extract_executive_message(section, "Advisory Board")
        }
        
        # Extract leadership targets and focus points
        targets_keywords = ["target", "goal", "objective", "focus", "priority", "initiative"]
        leadership_targets = self._extract_keywords(section, targets_keywords)
        
        return {
            "summary": section,
            "key_executives": leaders,
            "executive_messages": executive_messages,
            "leadership_targets": leadership_targets,
            "public_challenges": self._extract_keywords(section, ["challenge", "controversy", "turnover", "risk"]),
            "turnover_patterns": self._extract_keywords(section, ["resigned", "replaced", "stepped down", "left"])
        }
    
    def _extract_financial_information(self, content: str) -> Dict[str, Any]:
        """
        Extract structured financial information
        """
        section = self._extract_section(content, "Financial Information", "News Intelligence")
        
        return {
            "summary": section,
            "revenue_trends": self._extract_keywords(section, ["revenue", "sales", "growth", "decline"]),
            "funding": self._extract_keywords(section, ["funding", "raised", "investment", "round"]),
            "stress_events": self._extract_keywords(section, ["loss", "debt", "warning", "audit", "risk"]),
            "risk_factors": self._extract_keywords(section, ["risk", "warning", "concern", "challenge"])
        }
    
    def _extract_news_intelligence(self, content: str) -> Dict[str, Any]:
        """
        Extract structured news intelligence with positive/negative classification
        """
        section = self._extract_section(content, "News Intelligence", "Challenges")
        
        # Extract positive news
        positive_keywords = ["expansion", "partnership", "launch", "award", "growth", "success", "achievement"]
        positive_news = self._extract_news_items(section, positive_keywords, "positive")
        
        # Extract negative news
        negative_keywords = ["fine", "lawsuit", "breach", "crisis", "failure", "loss", "misconduct", "scandal"]
        negative_news = self._extract_news_items(section, negative_keywords, "negative")
        
        return {
            "summary": section,
            "positive_news": positive_news,
            "negative_news": negative_news,
            "neutral_context": self._extract_keywords(section, ["trend", "industry", "market", "development"])
        }
    
    def _extract_news_items(self, content: str, keywords: List[str], sentiment: str) -> List[Dict[str, Any]]:
        """
        Extract news items matching keywords
        """
        items = []
        sentences = re.split(r'[.!?]\s+', content)
        
        for sentence in sentences:
            if any(keyword.lower() in sentence.lower() for keyword in keywords):
                # Try to extract date
                date_match = re.search(r'\b(20\d{2}|\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b', sentence)
                date = date_match.group(1) if date_match else "Unknown"
                
                items.append({
                    "date": date,
                    "summary": sentence.strip(),
                    "sentiment": sentiment,
                    "impact_category": self._classify_impact(sentence)
                })
        
        return items[:10]  # Limit to 10 items
    
    def _extract_challenges_risks(self, content: str) -> Dict[str, Any]:
        """
        Extract challenges and risks intelligence
        """
        section = self._extract_section(content, "Challenges", "Strategic Priorities")
        
        return {
            "summary": section,
            "external_challenges": self._extract_keywords(section, [
                "competition", "regulatory", "economic", "geopolitical", "technology", "market"
            ]),
            "internal_challenges": self._extract_keywords(section, [
                "leadership", "sales", "operational", "culture", "morale", "initiative"
            ]),
            "public_controversies": self._extract_keywords(section, [
                "lawsuit", "scandal", "backlash", "crisis", "controversy"
            ]),
            "impact_assessment": self._extract_keywords(section, [
                "severity", "risk", "short-term", "long-term", "impact"
            ])
        }
    
    def _extract_keywords(self, content: str, keywords: List[str]) -> List[str]:
        """
        Extract sentences or phrases containing keywords
        """
        matches = []
        sentences = re.split(r'[.!?]\s+', content)
        
        for sentence in sentences:
            for keyword in keywords:
                if keyword.lower() in sentence.lower():
                    matches.append(sentence.strip())
                    break
        
        return matches[:5]  # Limit to 5 matches per category
    
    def _classify_impact(self, text: str) -> str:
        """
        Classify impact category from text
        """
        text_lower = text.lower()
        if any(word in text_lower for word in ["financial", "revenue", "profit", "loss", "funding"]):
            return "financial"
        elif any(word in text_lower for word in ["operational", "production", "supply", "manufacturing"]):
            return "operational"
        elif any(word in text_lower for word in ["reputation", "brand", "image", "public"]):
            return "reputational"
        elif any(word in text_lower for word in ["legal", "lawsuit", "court", "regulatory", "fine"]):
            return "legal"
        else:
            return "general"
    
    def _is_empty_section(self, text: str) -> bool:
        """
        Check if a section contains only 'Not found' or empty responses
        """
        if not text:
            return True
        
        # Remove markdown formatting and whitespace
        clean_text = re.sub(r'\*\*', '', text)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        # Check if it's mostly "Not found" responses
        not_found_count = clean_text.lower().count('not found')
        total_lines = len([line for line in text.split('\n') if line.strip()])
        
        # If more than 80% of lines say "Not found", consider it empty
        if total_lines > 0 and not_found_count > (total_lines * 0.8):
            return True
        
        # Check for common empty patterns
        empty_patterns = [
            r'^\s*-\s*\*\*[^:]+\*\*:\s*not found\s*$',
            r'^\s*not found\s*$',
            r'^\s*n/a\s*$',
            r'^\s*none\s*$'
        ]
        
        for pattern in empty_patterns:
            if re.match(pattern, clean_text, re.IGNORECASE):
                return True
        
        return False
    
    def _extract_executive_message(self, content: str, executive_role: str) -> str:
        """
        Extract executive message for a specific role (CEO, CFO, etc.)
        """
        role_pattern = re.compile(
            rf"{re.escape(executive_role)}\s+(message|letter|statement|communication)[:\-]?\s*([^\n]*(?:\n(?!\n)[^\n]*)*)",
            re.IGNORECASE | re.MULTILINE
        )
        
        match = role_pattern.search(content)
        if match:
            # Get the matched content
            message = match.group(0)
            # Clean up and limit length
            message = message.strip()
            # Get up to 500 characters or until double newline
            sentences = re.split(r'[.!?]\s+', message)
            result = '. '.join(sentences[:3])  # Take first 3 sentences
            return result if result else "No message found"
        
        return "No message found"

