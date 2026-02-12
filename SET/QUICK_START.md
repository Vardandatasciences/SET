# 🚀 Quick Start: 100% FREE Setup

## 30-Second Setup (NO API KEYS NEEDED!)

### 1. Install Ollama (Free AI)

**Download:** https://ollama.ai/download

- Windows: Run installer
- Mac: Drag to Applications  
- Linux: `curl -fsSL https://ollama.ai/install.sh | sh`

### 2. Download AI Model

```bash
ollama pull deepseek-r1:latest
# OR for faster: ollama pull llama3.1:8b
```

### 3. Install Dependencies

```bash
cd SET/backend
pip install -r requirements.txt
python -m playwright install chromium
```

### 4. Configure (Optional)

Create `backend/.env`:

```env
# Ollama (no API key needed!)
OLLAMA_MODEL=deepseek-r1:latest

# LinkedIn (optional)
LINKEDIN_EMAIL=your_email@example.com
LINKEDIN_PASSWORD=your_password
```

### 5. Run

```bash
python main.py
```

You should see: **"💡 FREE SETUP - NO API COSTS!"**

## Test Your First Query

```bash
curl -X POST http://localhost:8000/api/research \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Satya Nadella",
    "research_type": "individual",
    "sources": [
      {
        "name": "LinkedIn",
        "link": "https://www.linkedin.com/in/satyanadella/"
      }
    ],
    "output_format": "word"
  }'
```

## What You Get (100% FREE!)

✅ **LinkedIn Profile Data** (direct scraping)
- Name, headline, experience, education, skills

✅ **Web Intelligence** (Ollama - Local AI)
- News, articles, publications, social media

✅ **Combined Report** (Word/PDF/PowerPoint)
- Comprehensive intelligence capsule

✅ **Unlimited Queries** - No API costs!
✅ **Complete Privacy** - Runs on your machine

## How It Works

```
Your Request
    ↓
LinkedIn URL? → LinkedIn Scraper → Direct scraping
    ↓
Other sources? → Ollama (FREE Local AI) → Web intelligence
    ↓
Combined → Document (Word/PDF/PPT)
```

## Need Help?

- 📖 **FREE Setup Guide**: [FREE_SETUP_GUIDE.md](FREE_SETUP_GUIDE.md)
- 📖 **Ollama Details**: [OLLAMA_SETUP.md](OLLAMA_SETUP.md)
- 📖 **Full Documentation**: [README.md](README.md)

## Troubleshooting

**"Ollama is not running"**
→ Open Ollama app or run: `ollama serve`

**"Model not found"**
→ Download it: `ollama pull deepseek-r1:latest`

**"LinkedIn credentials not configured"**
→ Add `LINKEDIN_EMAIL` and `LINKEDIN_PASSWORD` to `.env` (optional)

**"Playwright browser not installed"**
→ Run: `python -m playwright install chromium`

**"Out of memory"**
→ Use smaller model: `ollama pull llama3.1:8b`

## Cost

- **Ollama**: $0.00 (runs locally)
- **LinkedIn**: $0.00 (free scraping)
- **Total**: **$0.00** 🎉

## Ready! 🎉

Your SET tool now uses:
- 🤖 **Ollama** for FREE local AI intelligence
- 🔗 **LinkedIn Scraper** for profile data
- 💰 **Total Cost: $0.00**

Start unlimited, free researching! 🚀
