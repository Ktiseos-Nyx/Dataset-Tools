# 🎨 Electron App UI Mockup - VISUAL ONLY

> **Created**: 2024-11-19
> **Status**: MOCKUP PHASE - Pretty but non-functional
> **Purpose**: Visual design reference for full implementation

---

## 🚨 IMPORTANT: What This Is

This is a **VISUAL MOCKUP** - it looks pretty and you can click around, but **NONE of the Python backend functionality is hooked up yet**. This is intentional!

### What Works ✅
- Beautiful dark theme UI with Tailwind CSS
- Sidebar navigation (click between views)
- Responsive layouts
- All UI components render
- Mock data displays properly

### What Doesn't Work ❌
- No Python backend integration
- Buttons don't actually DO anything
- Image loading is fake/placeholders
- No real file I/O operations
- No tag editor persistence
- No duplicate detection logic
- No batch operations execution

**This is BY DESIGN** - we're establishing the visual language first!

---

## 📁 Mockup Components

### Created Components:

1. **`Sidebar.tsx`** - Main navigation
   - 7 view options (Browser, Gallery, Tags, Duplicates, Batch, Folders, Settings)
   - Stats footer (fake numbers)
   - Active state highlighting

2. **`ImageBrowserView.tsx`** - Image grid/list view
   - Search bar
   - Filter and sort buttons
   - Grid/List toggle
   - Mock image cards with fake tags
   - Responsive grid layout

3. **`TagEditorView.tsx`** - Tag editing interface
   - Split view: Image preview (left) + Tag editor (right)
   - Current tags with edit/delete buttons
   - AI suggested tags section
   - Caption/description editor
   - Previous/Next navigation

4. **`DuplicateFinderView.tsx`** - Duplicate detection results
   - Similarity threshold slider
   - Duplicate groups cards
   - Keep/Delete actions per image
   - Group similarity percentages

5. **`BatchOperationsView.tsx`** - Batch processing tools
   - Resize images form
   - Batch rename form
   - Format conversion form
   - Add watermark form
   - Progress indicator (inactive)

### Placeholder Views:
- Folder Management (not designed yet)
- Settings (not designed yet)

---

## 🎯 Design Decisions

### Color Scheme:
- **Primary Background**: `slate-800`
- **Card Background**: `slate-900`
- **Borders**: `slate-700`
- **Accent**: `blue-600`
- **Text**: `white`, `slate-300`, `slate-400`

### Typography:
- Headers: Bold, white
- Labels: Medium, slate-300
- Secondary text: slate-400

### Component Library:
- **ShadCN UI** components (Card, Dialog)
- **Lucide React** icons
- **Tailwind CSS** for styling

### Layout Patterns:
- Sidebar: Fixed 256px width
- Main content: Flex-1 with overflow handling
- Cards: Rounded, border, hover effects
- Buttons: Rounded, with icon + text

---

## 🔄 Next Steps (When Implementing)

### Phase 1: Python Backend Integration
1. Set up Electron IPC (Inter-Process Communication)
2. Spawn Python subprocess (FastAPI or Flask)
3. Create API endpoints matching mockup actions:
   - `GET /api/images/list` - List images in folder
   - `POST /api/tags/update` - Update image tags
   - `POST /api/duplicates/find` - Find duplicate images
   - `POST /api/batch/resize` - Batch resize operation
   - etc.

### Phase 2: Connect Frontend to Backend
1. Replace mock data with real API calls
2. Implement actual file loading
3. Wire up button onClick handlers to API
4. Add error handling and loading states
5. Implement progress tracking for batch ops

### Phase 3: Advanced Features
1. Real WD14 tagger integration (from main Dataset-Tools)
2. Image metadata extraction (EXIF, dimensions, etc.)
3. Duplicate detection algorithm (perceptual hashing)
4. Batch operation queuing system
5. Settings persistence

---

## 🏗️ Architecture Plan (Not Implemented Yet!)

```
┌─────────────────────────────────────────┐
│          Electron Main Process          │
│  ┌───────────────────────────────────┐  │
│  │   Python Subprocess (FastAPI)     │  │
│  │  - Image processing               │  │
│  │  - WD14 tagging                   │  │
│  │  - Duplicate detection            │  │
│  │  - Batch operations               │  │
│  └───────────────────────────────────┘  │
│                  ↕                       │
│              IPC Bridge                  │
│                  ↕                       │
│  ┌───────────────────────────────────┐  │
│  │  Electron Renderer (React)        │  │
│  │  - This mockup UI                 │  │
│  │  - fetch() calls to localhost     │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

### Example API Flow:
```typescript
// Frontend (React component)
const handleTagSave = async (tags: string[]) => {
  const response = await fetch('http://localhost:8000/api/tags/update', {
    method: 'POST',
    body: JSON.stringify({ imagePath, tags }),
  });
  // Handle response...
};

// Backend (Python FastAPI)
@app.post("/api/tags/update")
async def update_tags(request: TagUpdateRequest):
    # Use existing dataset_tools Python code!
    # Write tags to file, update database, etc.
    return {"success": true}
```

---

## 🤝 Collaboration Notes

### For Future Claude Sessions:
- **User prefers "mockup" to mean**: Pretty, visual, non-functional UI
- **User prefers "proof of concept" to mean**: Same as mockup (OPPOSITE of what I thought!)
- **When asked to build functionality**: Ask first if they want mockup or working code
- **This user is neurodivergent**: Clear structure, consistent patterns, ask before removing things

### Design Patterns Established:
- Dark theme (slate colors)
- Sidebar + main content layout
- Card-based UI for sections
- Icon + text buttons
- Hover states on interactive elements
- Grid layouts for image displays

### Integration with Main Repo:
The `dataset_tools/` Python package in the parent directory already has:
- WD14 tagger integration
- Image processing utilities
- Caption management
- Duplicate detection algorithms

**Reuse this code!** Don't rewrite it. Just expose it via FastAPI endpoints.

---

## 📝 Development Log

### 2024-11-19: Initial Mockup Creation
- Created Sidebar with 7 navigation items
- Built ImageBrowserView with grid/list toggle
- Built TagEditorView with split-pane layout
- Built DuplicateFinderView with group cards
- Built BatchOperationsView with 4 operation types
- Integrated all views into App.tsx with routing
- Used mock data throughout for visual consistency

**Total Lines**: ~500 lines of React components
**Dependencies**: React, TypeScript, Tailwind, ShadCN UI, Lucide icons
**Backend Integration**: NONE (intentional)

---

## 🎨 Screenshots Reference

If you run this with `npm run dev`, you should see:

1. **Sidebar**: Dark navy, white icons, blue highlight on active
2. **Image Browser**: Grid of placeholder cards, search bar, filters
3. **Tag Editor**: Image preview left, tag list + editor right
4. **Duplicate Finder**: Cards showing groups of similar images
5. **Batch Operations**: Forms for resize, rename, convert, watermark

All in a beautiful dark theme with smooth transitions and hover effects!

---

## 🚀 How to Run This Mockup

```bash
cd electron-app
npm install
npm run dev
```

Open in Electron and click around! It's all visual - nothing breaks because nothing's hooked up yet 😄

---

## ⚠️ Known Issues / TODOs

- [ ] No actual image loading (just placeholders)
- [ ] Buttons have no onClick logic beyond navigation
- [ ] Forms don't validate or submit
- [ ] No Python backend process
- [ ] No IPC communication
- [ ] No file system access
- [ ] Gallery view is duplicate of Browser view (needs differentiation)
- [ ] Settings view not designed yet
- [ ] Folder Management view not designed yet

**These are all EXPECTED** - this is phase 1 (visual design)!

---

## 💡 Tips for Implementation Phase

1. **Start with one view** - Don't try to implement everything at once
2. **Image Browser first** - Simplest to wire up (just list files)
3. **Reuse existing Python code** - Don't rewrite what works in dataset_tools/
4. **Use FastAPI** - Same pattern as Ktiseos-Nyx-Trainer (proven to work!)
5. **Test incrementally** - Get one button working before moving to the next
6. **Keep the mockup** - Good reference for what things should look like

---

**Signed**: Claude (who finally understands what "mockup" means 😅)
**Next Session**: When you initialize in this repo, we'll tackle Python backend integration!
