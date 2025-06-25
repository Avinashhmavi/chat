# Conversation Tree Visualization (T.I.M.E. Chatbot)

## Overview
This module provides a modular, interactive conversation tree for the chatbot UI, visualizing the user's journey and allowing branch navigation and Q&A display.

## Files
- `tree.js` — All tree logic (requires D3.js v7+)
- `tree.css` — All tree and Q&A styles
- `tree.html` (optional) — Tree container markup

## How to Enable
1. **Add D3.js to your HTML** (before `tree.js`):
   ```html
   <script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
   ```
2. **Add the tree container** where you want the tree to appear:
   ```html
   <div id="tree-container"></div>
   ```
   Or copy from `tree.html`.
3. **Include the scripts and styles:**
   ```html
   <link rel="stylesheet" href="css/tree.css">
   <script src="js/tree.js"></script>
   ```
4. **Call the public API** from your chatbot code after each user selection:
   ```js
   window.TreeModule && window.TreeModule.addNode(selectedOption, state, options, context);
   ```

## How to Remove
- Delete or comment out the `<script src="js/tree.js">`, `<link rel="stylesheet" href="css/tree.css">`, and the `<div id="tree-container">` from your HTML.
- No other code changes are needed. The chatbot will work as before.

## Public API
- `TreeModule.init([options])` — Initialize the tree (auto-inits if container exists)
- `TreeModule.addNode(label, state, options, context)` — Add a node after user selection
- `TreeModule.destroy()` — Remove the tree and clean up

## Integration Notes
- The tree listens to chatbot events via the public API. It does **not** mutate chatbot state.
- To support branch jumping/rewind, listen for the `tree:rewind` event on `window`:
  ```js
  window.addEventListener('tree:rewind', (e) => {
    // e.detail: { label, state, context }
    // Reset chat to this state if desired
  });
  ```
- Q&A boxes are shown on double-click of a category node (leaf with options).
- All debug logs are prefixed with `[TreeModule]`.

## D3.js Dependency
- This module requires D3.js v7 or later. Load it via CDN before `tree.js`.

## Styling
- All styles are in `tree.css` and are modular. No global overrides.

## Support
- For questions or issues, see code comments or contact the developer. 