# How to Update Your Google API Key

## Quick Steps:

1. **Open your .env file:**
   - Location: `C:\Users\louky\Downloads\SET\SET\backend\.env`
   - Or run: `notepad .env` in the backend folder

2. **Find this line:**
   ```
   GOOGLE_CUSTOM_SEARCH_API_KEY=AIzaSyBRFG6TGQdbqvhrU0w2-lP1MWSdtLeXSiE
   ```

3. **Replace the old key with your NEW key:**
   ```
   GOOGLE_CUSTOM_SEARCH_API_KEY=YOUR_NEW_KEY_HERE
   ```
   (Paste the new key you just copied)

4. **Save the file** (Ctrl+S)

5. **Close Notepad**

6. **Test again:**
   ```powershell
   python test_google_api.py
   ```

---

## If You Haven't Created the New Key Yet:

1. In the "Create API key" dialog:
   - Name: "API key 2" (or any name)
   - Application restrictions: "None"
   - API restrictions: "Don't restrict key"
   - Click "Create"

2. Copy the new key that appears

3. Follow steps above to update .env
