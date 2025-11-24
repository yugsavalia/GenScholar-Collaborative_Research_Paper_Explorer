# GenScholar Design Guidelines

## Design Approach
**Utility-Focused Academic Research Tool** - Dark theme optimized for extended PDF reading sessions with minimal distractions and zero animations. Focus on function, readability, and information density.

---

## Color System (Dark Theme - Eye-Friendly)

```css
--bg-primary: #121212
--bg-surface: #1E1E1E
--text-primary: #E0E0E0
--text-muted: #BDBDBD
--accent: #4FC3F7
--danger: #EF5350
--border: #2A2A2A
```

**Usage Guidelines:**
- Background: #121212 for main canvas
- Surface: #1E1E1E for cards, modals, panels
- Accent #4FC3F7 for CTAs, links, active states, logo text
- Danger #EF5350 for delete/destructive actions only

---

## Typography & Hierarchy

**Font Stack:** System fonts (-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto)

**Scale:**
- Logo text: 1.4rem, weight 600, color accent
- Headings: 2rem (h1), 1.5rem (h2), 1.25rem (h3)
- Body: 1rem, color text-primary
- Muted text: 0.9rem, color text-muted
- Form labels: 0.875rem, weight 500

---

## Layout System

**Spacing Units:** Use 8px-based spacing (8, 16, 24, 32, 40px)

**Container Widths:**
- Landing/Auth: max 600px centered
- Dashboard: max 1400px with 24px padding
- Workspace: Full-width with fixed sidebar (360px)

**Grid Patterns:**
- Workspace cards: 3-column grid on desktop, 2 on tablet, 1 on mobile
- PDF list: Single column with full metadata

---

## Component Library

### Logo Integration (CRITICAL)
**Navbar:**
```
Logo image (40px height) + "GenScholar" text
Left-aligned, horizontal flex
Image margin-right: 10px
```

**Landing:**
```
Logo image (140px width) centered above title
margin-bottom: 20px
```

### Navigation
**Navbar Structure:**
- Logo (image + text) - Left
- Links (Dashboard | Contact | Logout) - Right
- **NO "Workspace" item**
- Background: surface color with bottom border

### Buttons
- Primary: Accent background, white text
- Secondary: Border with accent, transparent bg
- On images: Blur background (backdrop-filter: blur(8px))
- No hover animations

### Forms (Formik + Yup)
- Labels above inputs
- Input background: slightly lighter than surface
- Border: 1px solid border color
- Focus: accent border
- Error text: danger color below input

### Cards
- Background: surface
- Border: 1px solid border color
- Padding: 24px
- Border-radius: 8px

### Modals
- Overlay: rgba(0,0,0,0.8)
- Content: surface background, centered
- Close on Esc key
- Max-width: 600px

### Sidebar (Workspace Only)
**Right sidebar, fixed 360px width:**
- Three tabs: Main Chat | Threaded Discussions | AI ChatBot
- Active tab: accent bottom border + accent text
- Content area: scrollable, surface background
- Message bubbles: alternating alignment (me/other)

### PDF Viewer
- Left panel: PDF list + metadata
- Center: react-pdf canvas with annotation overlays
- Toolbar: annotation modes (select/highlight/underline/textbox)
- Tool icons: simple, monochrome when inactive, accent when active

### Annotations
- Highlight: accent with 30% opacity overlay
- Underline: accent 2px solid line beneath text
- Textbox: floating note with surface background, border

---

## Page-Specific Layouts

### Landing
- Centered logo (140px) at top
- Title + subtitle
- Two buttons: "Get Started" (primary) | "Login" (secondary)
- Footer: "Follow us" text + Instagram/Twitter SVG icons

### Auth
- Tab switcher: Login | Create Account
- Active tab: accent underline
- Form centered, max 400px
- Email + password fields with validation

### Dashboard
- Header: "Workspaces" title + Create button (right)
- Search bar (full width, surface background)
- Workspace grid (3 cols desktop)
- Recent collaborations section below
- Footer with social icons

### Workspace
- Header: Workspace title + collaborator avatars (right)
- Upload PDF button (file input, accept=".pdf")
- Left panel: PDF list (name, upload date, select action)
- Center: PDF viewer with annotation toolbar above
- Right sidebar: 360px fixed, three tabs as specified

### Contact
- Centered content, max 600px
- Email, social links
- Simple layout, no forms

---

## Iconography
- Use Font Awesome or Heroicons CDN
- Social icons: Instagram, Twitter SVGs in footer
- Annotation tools: Select, Highlight, Underline, Text icons
- Size: 20-24px for UI elements

---

## Interaction Patterns

**NO animations or transitions**

**Keyboard:**
- Enter: Send chat messages
- Esc: Close modals

**PDF Selection:**
- Mouseup on text layer captures selection
- Store text + bounding rects
- Show annotation options

**Tab Navigation:**
- Click to switch sidebar content
- Active state: accent color + bottom border

---

## Images

**Logo (Required):**
- File: `src/assets/logo.jpg` (provided)
- Usage: Navbar (40px height) + Landing (140px width)
- Alt text: "GenScholar Logo"

**Social Icons:**
- Instagram and Twitter SVGs in `assets/icons/`
- Footer placement on Landing and Dashboard

**No hero images** - This is a utility-focused research tool, not a marketing site.