# Contacts App Changelog

## 2026-04-17 — Instant client-side sort, filter, and search

### Changes (templates/index.html)

**Client-side filtering and sorting** — all contact list filtering, sorting, and search now happen instantly in the browser with no page reload. Dropdowns and search act in real-time.

**How it works:**
- Each `<li class="contact-card">` carries `data-name`, `data-relationship`, and `data-created` attributes
- JavaScript reads these on every input/change event, filters and reorders DOM nodes in-place
- Note cycling animations preserved — DOM nodes are moved, not recreated
- Person count in header updates live as results narrow

**Note:** URL no longer reflects filter/sort state (no query params). Page refresh resets to all contacts, A→Z.

### 2026-04-17 — Add sorting and filtering

**Sorting** — dropdown with four options (all persisted in URL params):

## 2026-04-13 — Fix inconsistent spacing in contact card note preview area

### Problem
The note preview area on the contact list (index.html) had inconsistent spacing relative to the contact meta row (relationship + birthday). Root cause: the `.note-preview-area` div was a sibling of the anchor tag, with no explicit padding on the anchor bottom, relying instead on margin collapse which behaves unpredictably.

### Changes (templates/index.html)

1. **`.note-preview-area`** — removed ad-hoc `margin-top: 0` and `padding-left: 4px`; now uses a dedicated rule with explicit horizontal padding that matches the card interior:
   ```css
   .contact-card > .note-preview-area {
       padding: 0 16px 14px;
   }
   ```

2. **`.contact-card > a`** — bottom padding increased from 4px to 10px to create a consistent 4px visual gap between the meta row and the note preview, instead of relying on margin collapse.

3. **`.note-preview-text`** and **`.note-preview-cycling`** — removed the `padding-left: 18px` hack since indentation is now handled by the parent area's padding.

### Design rationale
- Horizontal alignment is now explicit — both the anchor and note-preview-area use 16px side padding as their reference
- Gap between meta and note is controlled via anchor bottom padding (10px) minus note preview top margin (0), giving a predictable 4px gap
- All spacing is now in terms of the same base unit, making it easy to adjust uniformly or add new sibling elements later
