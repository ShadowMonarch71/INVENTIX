# Inventix AI - Testing Guide

## ✅ Server Status

Both servers are running:
- ✅ **Backend**: http://localhost:8000 (Healthy)
- ✅ **Frontend**: http://localhost:3000 (Ready)

---

## 🎯 Testing Steps

### Test 1: Open the Dashboard

1. **Open your browser** and navigate to:
   ```
   http://localhost:3000
   ```

2. **Expected Result**:
   - Dark theme with glassmorphism effects
   - Animated header with "INVENTIX AI" logo
   - Sidebar with 5 navigation items
   - Dashboard showing welcome message and stats
   - Legal disclaimer at the bottom of sidebar

---

### Test 2: Test the Idea Analyzer

1. **Click** "Idea Analyzer" in the sidebar

2. **Enter test data**:
   - **Idea Description**: 
     ```
     A machine learning system that uses computer vision to automatically detect defects in manufacturing products in real-time on the assembly line. The system uses edge computing to process images locally without cloud latency.
     ```
   - **Technology Domain**: `Computer Vision, ML`
   - **Additional Context**: `Manufacturing quality control`

3. **Click** "Analyze Idea"

4. **Expected Result**:
   - Loading animation appears
   - After 3-5 seconds, you'll see:
     - ✅ Idea summary
     - ✅ Key concepts extracted (e.g., "computer vision", "edge computing")
     - ✅ 4 novelty scores (Overall, Semantic Uniqueness, Domain Coverage, Prior Art Risk)
     - ✅ Potential overlaps list
     - ✅ Recommended searches
     - ✅ Unknowns section
     - ✅ Scope disclaimer at the bottom
   - All scores should be between 0-100%

---

### Test 3: Test the Patent Risk Scanner

1. **Click** "Patent Risk" in the sidebar

2. **Enter test data**:
   - **Claim Text**: 
     ```
     A method for processing digital images comprising: capturing an image using a camera sensor; applying a convolutional neural network to detect objects in the image; transmitting detection results to a remote server via wireless communication; and displaying the results on a user interface.
     ```
   - **Claim Type**: `Independent Claim`
   - **Technology Domain**: `Computer Vision`

3. **Click** "Scan Risk"

4. **Expected Result**:
   - Animated scan lines appear
   - After 3-5 seconds, you'll see:
     - ✅ Overall risk gauge (0-100%)
     - ✅ Risk level badge (LOW/MEDIUM/HIGH)
     - ✅ Radar chart showing 4 risk dimensions
     - ✅ Individual risk breakdowns:
       - Novelty Risk
       - Scope Risk
       - Clarity Risk
       - Prior Art Risk
     - ✅ Limitations & Unknowns section
     - ✅ Legal disclaimer

---

### Test 4: Verify Other Panels

1. **Click** "Research" in the sidebar
   - **Expected**: "Coming Soon" placeholder with planned features

2. **Click** "Knowledge Graph" in the sidebar
   - **Expected**: Demo visualization with graph nodes and planned integration info

3. **Click** "Dashboard" to return home
   - **Expected**: Dashboard reappears with smooth animation

---

## 🧪 API Testing (Optional)

### Test the API Directly

**Option 1: Using Browser**

1. Open http://localhost:8000/docs
2. You'll see the interactive Swagger UI
3. Try the `/api/analysis/idea` endpoint:
   - Click "Try it out"
   - Fill in the request body:
     ```json
     {
       "idea_text": "A blockchain-based system for transparent supply chain tracking",
       "domain": "Blockchain",
       "context": "Supply chain management"
     }
     ```
   - Click "Execute"
   - See the JSON response

**Option 2: Using PowerShell**

```powershell
# Test idea analysis
$body = @{
    idea_text = "An AI-powered chatbot for customer service"
    domain = "Artificial Intelligence"
    context = "Customer support automation"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/analysis/idea" -Method POST -Body $body -ContentType "application/json"
```

---

## 🎨 UI Features to Notice

### Design Elements
- ✅ **Dark Mode**: Premium dark theme with blue/purple accents
- ✅ **Glassmorphism**: Semi-transparent cards with backdrop blur
- ✅ **Animations**: Smooth transitions between panels
- ✅ **Gradients**: Logo with animated glow effect
- ✅ **Progress Bars**: Color-coded risk/novelty indicators
- ✅ **Responsive**: Try resizing your browser window

### Interactive Elements
- ✅ **Hover Effects**: Cards lift slightly on hover
- ✅ **Active Indicators**: Sidebar shows animated indicator on active panel
- ✅ **Loading States**: Animated orbs and pulsing effects
- ✅ **Status Badges**: Color-coded confidence levels (low/medium/high)

---

## ⚠️ Expected Behaviors

### ANTIGRAVITY Features in Action

1. **Evidence References**:
   - Every response includes an `evidence_references` array
   - Evidence IDs are timestamped (e.g., `EVD-20260201-INPUT`)

2. **Confidence Levels**:
   - Most responses will show "medium" confidence
   - This is correct - the system acknowledges uncertainty

3. **Disclaimers**:
   - Every result has a scope disclaimer
   - Clearly states what the system does NOT determine

4. **Unknowns Section**:
   - Lists what couldn't be determined
   - Example: "Actual prior art overlap"

5. **Crash Logs** (if something fails):
   - Red error card appears
   - Shows error type, message, failed stage
   - Recommends action (e.g., "retry_with_more_evidence")

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Frontend not loading | Check if port 3000 is free. Try `npm run dev -- -p 3001` |
| API errors | Verify your `.env` has valid `GEMINI_API_KEY` |
| "CRASH" responses | This is normal ANTIGRAVITY behavior - check the error message for details |
| Slow responses | Gemini API can take 3-5 seconds - this is expected |
| CORS errors | Ensure backend is running on port 8000 |

---

## ✨ Success Criteria

You've successfully tested the project if:

- [x] Dashboard loads with dark theme
- [x] Idea Analyzer returns novelty scores
- [x] Patent Risk Scanner shows radar chart
- [x] All responses include evidence references
- [x] Disclaimers are visible on all results
- [x] Navigation between panels is smooth
- [x] No console errors in browser (F12 Developer Tools)

---

## 📸 What to Screenshot for Demo

1. **Dashboard** - Shows overall UI and welcome message
2. **Idea Analyzer Results** - Shows novelty scores and key concepts
3. **Patent Risk Radar Chart** - Shows visual risk breakdown
4. **API Docs** - Shows Swagger UI at http://localhost:8000/docs

---

## 🎉 Next Steps

After testing:
1. Try different innovation ideas
2. Test edge cases (very short text, technical jargon)
3. Check the browser console (F12) for any warnings
4. Review the API documentation at `/docs`
5. Explore the source code structure

---

**Happy Testing! 🚀**

If you encounter any issues, check the terminal logs for both frontend and backend.
