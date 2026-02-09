# Dataset Tools Frontend - Development Roadmap

> **Day 1 Goal**: Proof of concept - Parse AI image metadata without NumPy/Python dependencies ✅
> **Status**: WE WON! 🎉

---

## ✅ Completed (Day 1)

### Metadata Parsing
- [x] Parse PNG metadata (A1111, ComfyUI, NovelAI)
- [x] Parse JPEG EXIF metadata (Civitai images)
- [x] Handle Civitai's UTF-16-LE encoding with null bytes
- [x] Extract ComfyUI workflow JSON from JPEGs
- [x] Server-side API route (`/api/metadata`) working
- [x] Display metadata in MetadataPanel

### Current Features
- [x] File tree browser (current folder only)
- [x] Image preview
- [x] Metadata panel (toggle on/off)
- [x] Thumbnail vs List view switcher
- [x] Basic Next.js app structure

---

## 🚀 Next Steps (Priority Order)

### 1. Improve Metadata Display
**Problem**: ComfyUI shows workflow JSON but not extracted prompts/settings
**Root Cause**: Node references like `['32', 0]` are displayed as `[object object]`
**Solution**: One-level node reference resolution (NOT full traversal!)

**What we learned** (from ComfyUI_0069.png):
- ComfyUI uses `[nodeId, outputIndex]` arrays to reference other nodes
- Example: Node 27 (prompt) → `['32', 0]` → Node 32 has actual text
- We need to resolve these references to get the real values

**Implementation**:
- [ ] Write `resolveNodeReference()` function in API route
- [ ] Check if value is array → look up referenced node
- [ ] Extract actual value from referenced node's inputs
- [ ] Apply to text, seed, and other referenced fields
- [ ] Keep simple - one level resolution only (covers 95% of cases)

**After resolution**:
- [ ] Extract prompt text from CLIPTextEncode nodes
- [ ] Extract model/checkpoint names
- [ ] Extract seed, steps, CFG, sampler
- [ ] Show both "simple view" (extracted params) and "full workflow" (JSON)

**Note**: This is simpler than Quadmoon's full traversal - just resolve one hop!

### 2. shadcn/ui Integration
**Goal**: Use shadcn components for better UI/UX

**Note**: shadcn/ui works with Next.js 13/14/15/16 - it's just React components!
The only issue is LLMs defaulting to old Next.js patterns (Pages Router, etc.)

- [ ] Install shadcn/ui CLI and init project
- [ ] Add base components (Card, Button, Dialog, etc.)
- [ ] Create custom blocks based on shadcn patterns
- [ ] Replace existing components gradually
- [ ] Remind AI to use App Router + 'use client' when needed

### 3. Enhanced File Browser
**Problem**: File browser stuck in current folder
- [ ] Add navigation to parent/child folders
- [ ] Add breadcrumb navigation
- [ ] Show folder structure (expand/collapse)

### 4. Restore Drag & Drop
**Had it before, need it back**
- [ ] Drag and drop files/folders to load
- [ ] Drop zone UI with shadcn
- [ ] Handle multiple files at once

### 5. Thumbnail Card Layout
**Goal**: Better visual browse mode
- [ ] Design thumbnail card component (shadcn Card)
- [ ] Grid layout for thumbnails
- [ ] Show preview + key metadata on card
- [ ] Click to view full details

---

## 🎯 Future Enhancements

### Civitai Integration
- [ ] Fetch Civitai API data for images with `civitai:` URNs
- [ ] Display model info (name, creator, tags)
- [ ] Link to Civitai page
- [ ] Cache API responses

### ComfyUI Workflow Parsing
- [ ] Integrate Quadmoon's traversal logic for complex workflows
- [ ] Handle nested node references
- [ ] Resolve "Object object" issues in display
- [ ] Visual workflow diagram (future nice-to-have)

### Backend Considerations
**May need a backend for:**
- [ ] Batch processing multiple images
- [ ] Caching Civitai API responses
- [ ] File operations beyond browser limits
- [ ] Database for metadata indexing (way future)

### Polish & Deployment
- [ ] Vercel demo with sample images
- [ ] Documentation for developers
- [ ] Installation/usage guide
- [ ] Package sample images (curated set, not full collection)

---

## 📝 Technical Notes & Decisions

### Tech Stack
- **Framework**: Next.js 15/16 (confirm shadcn compatibility)
- **UI Library**: shadcn/ui
- **Styling**: Tailwind CSS
- **Backend**: API routes (Node.js) - may add separate backend later
- **Deployment**: Vercel

### What We DON'T Need
- ❌ NumPy (we won without it!)
- ❌ Python dependencies for parsing
- ❌ OpenCV
- ❌ Complex build tools
- ❌ kn-dataset-tools Python package

### Architecture Decisions To Make
- [ ] **shadcn blocks**: Document custom blocks as we create them
- [ ] **MCP integration**: Install when needed for AI assistance
- [ ] **State management**: Current approach vs zustand/jotai (decide if needed)
- [ ] **File handling**: Client-side vs server-side (depends on scale)

### Development Workflow
1. User installs components OR explains requirements
2. User may provide documentation
3. MCP may be used for AI assistance
4. Incremental development - one feature at a time
5. Test with real sample images

---

## 🖼️ Reference Materials

### Available Resources
- Screenshots of original app structure
- Sample images in `/Metadata Samples/`
- Python parser for reference (`parse_image_metadata.py`)
- PromptInspectorBot codebase (for ComfyUI node handling)

### Key Sample Images for Testing
- `ComfyUI_00165_.png` - Simple ComfyUI
- `ComfyUI_00013_.png` - Complex ComfyUI workflow
- `ComfyUI_00023_.png` - A1111 format (mislabeled)
- `ComfyUI_05822_.png` - Dynamic prompts with wildcards
- `4APB6HKZ4Q52TG1ANYBAE92050.jpg` - Civitai JPEG ✅ working!

---

## 🎉 Wins & Milestones

### Day 1
- **Big Win**: Parsed Civitai JPEG metadata without Python!
- **Breakthrough**: Discovered UTF-16-LE null byte encoding trick
- **Mental Health Win**: Broke through anxiety, got shit done! 💪

---

## 📅 Phases (NOT Time-Dependent!)

**IMPORTANT**: Phases are for structure and tracking progress - NOT deadlines or sprints!

**Phase 1** (Current): Core functionality
**Phase 2** (Next): UI/UX improvements with shadcn
**Phase 3** (Future): Advanced features (Civitai API, complex parsing)
**Phase 4** (Way Future): Polish, optimization, full app

### Why Phases ≠ Time
- We already have proof of concept in Python (1+ years of work there)
- What we built TODAY = ~9 months of traditional crank-ass development
- We work at whatever pace suits us
- No quarters, no weeks, no days - just when it feels right
- Phases = organizational structure for AI and human tracking
- Progress > deadlines. Always.

> **Mantra**: One feature at a time. Ship when ready. No rush.

---

**Last Updated**: 2026-01-05
**Current Focus**: Improve metadata display for ComfyUI workflows
