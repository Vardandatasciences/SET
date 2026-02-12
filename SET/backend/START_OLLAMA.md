# 🚀 How to Start Ollama

## Quick Start

### Windows:
1. **Press Windows key** (or click Start button)
2. **Type "Ollama"** in search
3. **Click "Ollama"** to open
4. **Wait 5-10 seconds** - Ollama will start
5. **Check system tray** (bottom-right) - you should see Ollama icon

### Mac:
1. **Open Finder**
2. **Go to Applications**
3. **Find and open "Ollama"**
4. **Wait 5-10 seconds** - Ollama will start
5. **Check menu bar** (top-right) - you should see Ollama icon

### Linux:
```bash
# Start Ollama service
systemctl start ollama

# Or run directly
ollama serve

# Check if running
systemctl status ollama
```

## Verify Ollama is Running

Open a terminal/command prompt and run:

```bash
ollama list
```

**If you see output** (even if empty), Ollama is running! ✅

**If you get an error**, Ollama is not running. Follow steps above.

## Test Ollama

```bash
# Try a simple query
ollama run llama3.1:8b "Hello, how are you?"
```

If it responds, Ollama is working perfectly!

## After Starting Ollama

1. **Wait 5-10 seconds** for Ollama to fully start
2. **Restart your SET server**:
   ```bash
   # Stop current server (Ctrl+C)
   # Then restart:
   python main.py
   ```
3. **Try your request again** in the web interface

## Common Issues

### "Ollama not found"
**Solution:** Download Ollama first:
- Visit: https://ollama.ai/download
- Download and install for your OS

### "Connection refused"
**Solution:** 
1. Make sure Ollama is actually running
2. Check system tray (Windows) or menu bar (Mac)
3. Restart Ollama if needed

### "Model not found"
**Solution:** Download the model:
```bash
ollama pull deepseek-r1:latest
# OR
ollama pull llama3.1:8b
```

## Auto-Start Ollama (Optional)

### Windows:
1. Press `Win + R`
2. Type: `shell:startup`
3. Create shortcut to Ollama in that folder
4. Ollama will start automatically on boot

### Mac:
1. System Settings → General → Login Items
2. Add Ollama
3. Ollama will start on login

### Linux:
```bash
# Enable auto-start
systemctl enable ollama
```

## Quick Checklist

- [ ] Ollama installed
- [ ] Ollama application opened
- [ ] Ollama icon visible (system tray/menu bar)
- [ ] `ollama list` command works
- [ ] Model downloaded (`ollama pull <model>`)
- [ ] SET server restarted
- [ ] Test request works

## Still Having Issues?

1. **Check Ollama logs:**
   - Windows: Check system tray → Right-click Ollama → View logs
   - Mac/Linux: Check terminal where you ran `ollama serve`

2. **Try manual start:**
   ```bash
   # Windows: Open Ollama from Start menu
   # Mac: Open from Applications
   # Linux:
   ollama serve
   ```

3. **Check port 11434:**
   ```bash
   # Windows:
   netstat -an | findstr 11434
   
   # Mac/Linux:
   lsof -i :11434
   ```

4. **Restart everything:**
   - Close Ollama completely
   - Restart Ollama
   - Restart SET server

## Need Help?

- **Ollama Docs**: https://ollama.ai/
- **Ollama GitHub**: https://github.com/ollama/ollama
- **Community**: Check Ollama Discord or GitHub Issues

---

**Once Ollama is running, your SET tool will work perfectly!** 🎉
