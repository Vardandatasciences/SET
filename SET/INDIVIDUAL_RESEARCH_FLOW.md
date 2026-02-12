# Individual Research Flow Guide

## Two Ways to Research Individuals

### Method 1: With LinkedIn URL (Recommended - Most Accurate) ✅

**When to use**: You have the person's LinkedIn profile URL

**Steps**:
1. Select "Individual" research type
2. Enter the person's name (e.g., "Satya Nadella")
3. Click "+ Add Source"
4. Select "LinkedIn" from dropdown
5. Paste the LinkedIn profile URL (e.g., `https://www.linkedin.com/in/satyanadella/`)
6. Click "Generate Intelligence Capsule" at bottom

**What happens**:
- ✅ System directly scrapes the LinkedIn profile
- ✅ Gets 100% accurate, verified data
- ✅ No ambiguity about which person
- ✅ Fastest and most reliable method

**Example**:
```
Individual Name: John Smith
Additional Sources:
  - Source: LinkedIn
  - Link: https://www.linkedin.com/in/johnsmith123/
[Generate Intelligence Capsule] ← Click this button
```

---

### Method 2: Without LinkedIn URL (Requires Disambiguation)

**When to use**: You don't have the LinkedIn URL, only know the name

**Steps**:
1. Select "Individual" research type
2. Enter the person's name (e.g., "John Smith")
3. Click "Check Name" button (beside the name field)
4. System shows how many people have that name
5. Enter the company name to identify the correct person
6. Click "Generate Intelligence Capsule" at bottom

**What happens**:
- System checks how many people have that name
- You provide company name for disambiguation
- System searches for that specific person
- ⚠️ May use AI-generated data if DISABLE_AI_WEB_INTELLIGENCE=false

**Example**:
```
Individual Name: John Smith
[Check Name] ← Click this button first
👥 15 people found with this name
Company Name: Microsoft Corporation ← Enter to disambiguate
[Generate Intelligence Capsule] ← Click this button
```

---

## Button Layout (Fixed)

### ✅ Correct Layout:
```
┌─────────────────────────────────────────────────────┐
│ Individual Name                                     │
│ [John Smith___________________________] [Check Name]│ ← Check button ONLY here
│                                                     │
│ Company Name (if name checked)                      │
│ [Microsoft Corporation____________________________] │
│                                                     │
│ Output Format                                       │
│ [Word Document (.docx)_________________________▼]  │
│                                                     │
│ Additional Sources (Optional)     [+ Add Source]    │
│ [LinkedIn▼] [https://linkedin.com/in/johnsmith___]│
│                                                     │
│          [Generate Intelligence Capsule]            │ ← Main button at bottom
└─────────────────────────────────────────────────────┘
```

### ❌ OLD (Incorrect) Layout:
```
- Had "Check Name" button at bottom (wrong!)
- Main button text changed between "Check Name" and "Generate Intelligence Capsule" (confusing!)
```

---

## LinkedIn URL Tips

### Valid LinkedIn URLs:
✅ `https://www.linkedin.com/in/satyanadella/`
✅ `https://www.linkedin.com/in/john-smith-12345/`
✅ `https://linkedin.com/in/jane-doe/`

### Invalid LinkedIn URLs:
❌ `https://www.linkedin.com/in/john smith/` (has space - will be auto-fixed to `john-smith`)
❌ `https://www.linkedin.com/feed/` (not a profile)
❌ `https://www.linkedin.com/company/microsoft/` (this is a company, not person)

### Finding Someone's LinkedIn URL:
1. Go to LinkedIn
2. Search for the person
3. Click on their profile
4. Copy URL from address bar
5. Paste it in "Additional Sources" section

---

## Flow Comparison

| Step | With LinkedIn URL | Without LinkedIn URL |
|------|-------------------|---------------------|
| 1. Enter name | ✅ | ✅ |
| 2. Click "Check Name" | ⏭️ Skip | ✅ Required |
| 3. Add LinkedIn URL | ✅ Required | ❌ N/A |
| 4. Enter company name | ⏭️ Skip | ✅ Required |
| 5. Click "Generate Intelligence Capsule" | ✅ | ✅ |
| **Accuracy** | 100% - Real LinkedIn data | Variable - Depends on AI/search |
| **Speed** | Fast - Direct scraping | Slower - Search + disambiguation |

---

## Common Issues & Fixes

### Issue 1: "Failed to scrape person profile: Timeout"
**Cause**: Invalid LinkedIn URL or profile is private
**Fix**: 
- Verify the URL is correct
- Check if profile is public
- Try opening URL in browser first

### Issue 2: "Multiple people found with this name"
**Cause**: Common name without disambiguation
**Fix**: Provide the company name OR use LinkedIn URL method

### Issue 3: LinkedIn URL has spaces
**Cause**: Copy-paste error or manual typing
**Fix**: System will auto-fix spaces to hyphens, but verify the URL is correct

---

## Recommendations

**For Sales Enablement (Recommended)**:
- ✅ Always use Method 1 (With LinkedIn URL)
- ✅ Get 100% accurate data
- ✅ Fastest results
- ✅ No ambiguity

**For Quick Lookups**:
- Use Method 2 if you don't have LinkedIn URL
- Be prepared to provide company name
- Verify results are for correct person

**For Best Data Quality**:
Add to `.env` file:
```env
DISABLE_AI_WEB_INTELLIGENCE=true
```
This ensures ONLY verified LinkedIn data is used (no AI-generated content).
