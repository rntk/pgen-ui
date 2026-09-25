/**
 * Prompt Constructor - Frontend Application
 * Zero external dependencies. Pure vanilla JavaScript.
 */

(function () {
  // State
  let state = {
    prompts: [],
    appendices: [],
    activeTab: "all", // 'all' | 'prompts' | 'appendices'
    searchQuery: "",
    selectedItem: null, // For detail/preview modal
    isPreviewOpen: false,
    cursorPosition: 0,
  };

  // DOM Elements
  const editor = document.getElementById("prompt-editor");
  const itemsList = document.getElementById("items-list");
  const librarySearch = document.getElementById("library-search");
  const searchClear = document.getElementById("search-clear");
  const tabButtons = document.querySelectorAll(".tab-btn");
  const previewWrapper = document.getElementById("preview-wrapper");
  const previewContent = document.getElementById("preview-content");
  const togglePreviewBtn = document.getElementById("toggle-preview-btn");
  const previewBtnLabel = document.getElementById("preview-btn-label");
  const copyBtn = document.getElementById("copy-btn");
  const clearBtn = document.getElementById("clear-btn");
  const downloadBtn = document.getElementById("download-btn");
  const saveAsBtn = document.getElementById("save-as-btn");
  const newPromptBtn = document.getElementById("new-prompt-btn");
  const newAppendixBtn = document.getElementById("new-appendix-btn");

  // Stats Elements
  const statWords = document.getElementById("stat-words");
  const statChars = document.getElementById("stat-chars");
  const statTokens = document.getElementById("stat-tokens");
  const statLines = document.getElementById("stat-lines");

  // Counts Elements
  const countAll = document.getElementById("count-all");
  const countPrompts = document.getElementById("count-prompts");
  const countAppendices = document.getElementById("count-appendices");

  // Modal Elements
  const itemModal = document.getElementById("item-modal");
  const modalCloseBtn = document.getElementById("modal-close-btn");
  const modalTypeBadge = document.getElementById("modal-type-badge");
  const modalTitle = document.getElementById("modal-title");
  const modalFilename = document.getElementById("modal-filename");
  const modalContent = document.getElementById("modal-content");
  const modalAppendBtn = document.getElementById("modal-append-btn");
  const modalInsertBtn = document.getElementById("modal-insert-btn");
  const modalReplaceBtn = document.getElementById("modal-replace-btn");
  const modalDeleteBtn = document.getElementById("modal-delete-btn");

  // Save Modal Elements
  const saveModal = document.getElementById("save-modal");
  const saveModalCloseBtn = document.getElementById("save-modal-close-btn");
  const saveCancelBtn = document.getElementById("save-cancel-btn");
  const saveSubmitBtn = document.getElementById("save-submit-btn");
  const saveForm = document.getElementById("save-form");
  const saveType = document.getElementById("save-type");
  const saveTitle = document.getElementById("save-title");
  const saveFilename = document.getElementById("save-filename");
  const saveDesc = document.getElementById("save-desc");

  // Initialize
  function init() {
    setupEventListeners();
    fetchLibrary();
    updateStats();
  }

  // Event Listeners
  function setupEventListeners() {
    // Editor stats & cursor tracking
    editor.addEventListener("input", () => {
      updateStats();
      if (state.isPreviewOpen) {
        renderPreview();
      }
    });

    const trackCursor = () => {
      state.cursorPosition = editor.selectionStart;
    };
    editor.addEventListener("click", trackCursor);
    editor.addEventListener("keyup", trackCursor);

    // Search
    librarySearch.addEventListener("input", (e) => {
      state.searchQuery = e.target.value.trim();
      searchClear.classList.toggle("hidden", state.searchQuery === "");
      renderLibrary();
    });

    searchClear.addEventListener("click", () => {
      librarySearch.value = "";
      state.searchQuery = "";
      searchClear.classList.add("hidden");
      renderLibrary();
    });

    // Tab buttons
    tabButtons.forEach((btn) => {
      btn.addEventListener("click", () => {
        tabButtons.forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        state.activeTab = btn.dataset.tab;
        renderLibrary();
      });
    });

    // Header buttons
    copyBtn.addEventListener("click", copyToClipboard);
    clearBtn.addEventListener("click", clearEditor);
    downloadBtn.addEventListener("click", downloadPrompt);
    togglePreviewBtn.addEventListener("click", togglePreview);

    // Quick action buttons
    newPromptBtn.addEventListener("click", () => openSaveModal("prompts", true));
    newAppendixBtn.addEventListener("click", () => openSaveModal("appendices", true));
    saveAsBtn.addEventListener("click", () => openSaveModal("prompts", false));

    // Item modal actions
    modalCloseBtn.addEventListener("click", closeItemModal);
    itemModal.addEventListener("click", (e) => {
      if (e.target === itemModal) closeItemModal();
    });

    modalAppendBtn.addEventListener("click", () => {
      if (state.selectedItem) {
        appendContent(state.selectedItem.content, state.selectedItem.title);
        closeItemModal();
      }
    });

    modalInsertBtn.addEventListener("click", () => {
      if (state.selectedItem) {
        insertContentAtCursor(state.selectedItem.content, state.selectedItem.title);
        closeItemModal();
      }
    });

    modalReplaceBtn.addEventListener("click", () => {
      if (state.selectedItem) {
        replaceContent(state.selectedItem.content, state.selectedItem.title);
        closeItemModal();
      }
    });

    modalDeleteBtn.addEventListener("click", () => {
      if (state.selectedItem) {
        deleteItem(state.selectedItem);
      }
    });

    // Save modal actions
    saveModalCloseBtn.addEventListener("click", closeSaveModal);
    saveCancelBtn.addEventListener("click", closeSaveModal);
    saveSubmitBtn.addEventListener("click", handleSaveSubmit);
    saveModal.addEventListener("click", (e) => {
      if (e.target === saveModal) closeSaveModal();
    });

    // Auto-fill filename from title
    saveTitle.addEventListener("input", (e) => {
      const val = e.target.value.trim().toLowerCase();
      const slug = val
        .replace(/[^a-z0-9]+/g, "_")
        .replace(/^_+|_+$/g, "");
      saveFilename.value = slug ? `${slug}.md` : "";
    });

    // Keyboard Shortcuts
    document.addEventListener("keydown", (e) => {
      // Ctrl+Enter or Cmd+Enter to copy
      if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
        e.preventDefault();
        copyToClipboard();
      }
      // Escape to close modals
      if (e.key === "Escape") {
        closeItemModal();
        closeSaveModal();
      }
    });
  }

  // API Calls
  async function fetchLibrary() {
    try {
      const [promptsRes, appendicesRes] = await Promise.all([
        fetch("/api/prompts"),
        fetch("/api/appendices"),
      ]);

      const promptsData = await promptsRes.json();
      const appendicesData = await appendicesRes.json();

      state.prompts = (promptsData.items || []).map((it) => ({ ...it, type: "prompt" }));
      state.appendices = (appendicesData.items || []).map((it) => ({ ...it, type: "appendix" }));

      updateCounts();
      renderLibrary();
    } catch (err) {
      showToast("Error loading prompt library: " + err.message, "error");
      itemsList.innerHTML = `<div class="empty-state">Failed to load library items.</div>`;
    }
  }

  async function fetchItemDetails(type, filename) {
    const endpoint = type === "prompt" ? `/api/prompts/${encodeURIComponent(filename)}` : `/api/appendices/${encodeURIComponent(filename)}`;
    const res = await fetch(endpoint);
    if (!res.ok) throw new Error("Failed to load item");
    return await res.json();
  }

  async function deleteItem(item) {
    if (!confirm(`Are you sure you want to delete '${item.filename}'?`)) return;

    const endpoint = item.item_type === "prompt"
      ? `/api/prompts/${encodeURIComponent(item.filename)}`
      : `/api/appendices/${encodeURIComponent(item.filename)}`;

    try {
      const res = await fetch(endpoint, { method: "DELETE" });
      if (!res.ok) throw new Error("Failed to delete item");

      showToast(`Deleted '${item.filename}'`, "info");
      closeItemModal();
      fetchLibrary();
    } catch (err) {
      showToast("Delete failed: " + err.message, "error");
    }
  }

  // Render Library
  function updateCounts() {
    countAll.textContent = state.prompts.length + state.appendices.length;
    countPrompts.textContent = state.prompts.length;
    countAppendices.textContent = state.appendices.length;
  }

  function renderLibrary() {
    let list = [];
    if (state.activeTab === "all") {
      list = [...state.prompts, ...state.appendices];
    } else if (state.activeTab === "prompts") {
      list = [...state.prompts];
    } else if (state.activeTab === "appendices") {
      list = [...state.appendices];
    }

    if (state.searchQuery) {
      const q = state.searchQuery.toLowerCase();
      list = list.filter((it) => {
        return (
          it.title.toLowerCase().includes(q) ||
          it.filename.toLowerCase().includes(q) ||
          (it.description && it.description.toLowerCase().includes(q)) ||
          (it.tags && it.tags.some((t) => t.toLowerCase().includes(q)))
        );
      });
    }

    if (list.length === 0) {
      itemsList.innerHTML = `<div class="empty-state">No matching items found.</div>`;
      return;
    }

    itemsList.innerHTML = list.map((item) => createCardHTML(item)).join("");

    // Attach card event listeners
    itemsList.querySelectorAll(".item-card").forEach((card) => {
      const type = card.dataset.type;
      const filename = card.dataset.filename;

      // Click title to view detail
      card.querySelector(".card-title").addEventListener("click", async () => {
        try {
          const detail = await fetchItemDetails(type, filename);
          openItemModal(detail);
        } catch (e) {
          showToast(e.message, "error");
        }
      });

      // Append button
      card.querySelector(".btn-append").addEventListener("click", async () => {
        try {
          const detail = await fetchItemDetails(type, filename);
          appendContent(detail.content, detail.title);
        } catch (e) {
          showToast(e.message, "error");
        }
      });

      // Insert button
      card.querySelector(".btn-insert").addEventListener("click", async () => {
        try {
          const detail = await fetchItemDetails(type, filename);
          insertContentAtCursor(detail.content, detail.title);
        } catch (e) {
          showToast(e.message, "error");
        }
      });

      // Replace button
      card.querySelector(".btn-replace").addEventListener("click", async () => {
        try {
          const detail = await fetchItemDetails(type, filename);
          replaceContent(detail.content, detail.title);
        } catch (e) {
          showToast(e.message, "error");
        }
      });
    });
  }

  function createCardHTML(item) {
    const isPrompt = item.item_type === "prompt" || item.type === "prompt";
    const badgeClass = isPrompt ? "badge-prompt" : "badge-appendix";
    const badgeLabel = isPrompt ? "Prompt" : "Appendix";

    const tagsHTML = (item.tags || [])
      .map((tag) => `<span class="tag-pill">${escapeHTML(tag)}</span>`)
      .join("");

    return `
      <div class="item-card" data-type="${isPrompt ? "prompt" : "appendix"}" data-filename="${escapeHTML(item.filename)}">
        <div class="card-top">
          <div class="card-title-group">
            <h3 class="card-title" title="Click to inspect">${escapeHTML(item.title)}</h3>
            <span class="card-filename">${escapeHTML(item.filename)}</span>
          </div>
          <span class="badge ${badgeClass}">${badgeLabel}</span>
        </div>

        ${item.preview ? `<p class="card-preview">${escapeHTML(item.preview)}</p>` : ""}
        ${tagsHTML ? `<div class="card-tags">${tagsHTML}</div>` : ""}

        <div class="card-actions">
          <div class="card-actions-left">
            <button class="btn btn-sm btn-primary btn-append" title="Add to end of current workbench">
              + Append
            </button>
            <button class="btn btn-sm btn-secondary btn-insert" title="Insert at current cursor position">
              Insert
            </button>
          </div>
          <div class="card-actions-right">
            <button class="btn btn-sm btn-outline btn-replace" title="Replace entire editor content">
              Replace
            </button>
          </div>
        </div>
      </div>
    `;
  }

  // Content Manipulation
  function appendContent(contentToAdd, title) {
    const current = editor.value;
    const cleanAdd = stripFrontmatter(contentToAdd).trim();

    if (!current.trim()) {
      editor.value = cleanAdd;
    } else {
      editor.value = current.trimEnd() + "\n\n---\n\n" + cleanAdd + "\n";
    }

    editor.focus();
    editor.selectionStart = editor.selectionEnd = editor.value.length;
    state.cursorPosition = editor.value.length;

    updateStats();
    if (state.isPreviewOpen) renderPreview();
    showToast(`Appended "${title || "snippet"}"`, "success");
  }

  function insertContentAtCursor(contentToAdd, title) {
    const cleanAdd = stripFrontmatter(contentToAdd).trim();
    const startPos = editor.selectionStart;
    const endPos = editor.selectionEnd;
    const current = editor.value;

    const before = current.substring(0, startPos);
    const after = current.substring(endPos);

    editor.value = before + (before && !before.endsWith("\n") ? "\n\n" : "") + cleanAdd + (after && !after.startsWith("\n") ? "\n\n" : "") + after;

    const newPos = startPos + cleanAdd.length + 2;
    editor.focus();
    editor.selectionStart = editor.selectionEnd = Math.min(newPos, editor.value.length);
    state.cursorPosition = editor.selectionStart;

    updateStats();
    if (state.isPreviewOpen) renderPreview();
    showToast(`Inserted "${title || "snippet"}" at cursor`, "success");
  }

  function replaceContent(contentToAdd, title) {
    if (editor.value.trim() && !confirm("Replace current editor content? Any unsaved changes will be overwritten.")) {
      return;
    }
    const cleanAdd = stripFrontmatter(contentToAdd).trim();
    editor.value = cleanAdd;

    editor.focus();
    editor.selectionStart = editor.selectionEnd = editor.value.length;
    state.cursorPosition = editor.value.length;

    updateStats();
    if (state.isPreviewOpen) renderPreview();
    showToast(`Loaded "${title || "prompt"}" into workbench`, "info");
  }

  function clearEditor() {
    if (!editor.value.trim()) return;
    if (confirm("Clear prompt workbench?")) {
      editor.value = "";
      updateStats();
      if (state.isPreviewOpen) renderPreview();
      showToast("Workbench cleared", "info");
      editor.focus();
    }
  }

  function copyToClipboard() {
    const text = editor.value.trim();
    if (!text) {
      showToast("Workbench is empty!", "info");
      return;
    }

    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text).then(() => {
        showToast("Prompt copied to clipboard! Ready to paste into LLM.", "success");
      }).catch(() => fallbackCopy(text));
    } else {
      fallbackCopy(text);
    }
  }

  function fallbackCopy(text) {
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    try {
      document.execCommand("copy");
      showToast("Prompt copied to clipboard!", "success");
    } catch (err) {
      showToast("Could not copy to clipboard", "error");
    }
    document.body.removeChild(ta);
  }

  function downloadPrompt() {
    const text = editor.value.trim();
    if (!text) {
      showToast("Workbench is empty!", "info");
      return;
    }
    const blob = new Blob([text], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `prompt_${new Date().toISOString().slice(0, 10)}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast("Downloaded prompt as markdown file", "success");
  }

  // Live Markdown Preview
  function togglePreview() {
    state.isPreviewOpen = !state.isPreviewOpen;
    previewWrapper.classList.toggle("hidden", !state.isPreviewOpen);
    togglePreviewBtn.classList.toggle("btn-primary", state.isPreviewOpen);
    togglePreviewBtn.classList.toggle("btn-secondary", !state.isPreviewOpen);
    previewBtnLabel.textContent = state.isPreviewOpen ? "Hide Preview" : "Preview";

    if (state.isPreviewOpen) {
      renderPreview();
    }
  }

  function renderPreview() {
    const text = editor.value;
    previewContent.innerHTML = parseSimpleMarkdown(text);
  }

  function parseSimpleMarkdown(md) {
    if (!md.trim()) {
      return '<div class="empty-state">No content to preview yet.</div>';
    }

    let escaped = escapeHTML(md);

    // Code blocks ```code```
    escaped = escaped.replace(/```([a-zA-Z0-9_]*)\n([\s\S]*?)```/g, (match, lang, code) => {
      return `<pre><code>${code.trim()}</code></pre>`;
    });

    // Inline code `code`
    escaped = escaped.replace(/`([^`]+)`/g, "<code>$1</code>");

    // Horizontal rules
    escaped = escaped.replace(/^(?:---|\*\*\*|___)\s*$/gm, "<hr>");

    // Headers
    escaped = escaped.replace(/^### (.*$)/gm, "<h3>$1</h3>");
    escaped = escaped.replace(/^## (.*$)/gm, "<h2>$1</h2>");
    escaped = escaped.replace(/^# (.*$)/gm, "<h1>$1</h1>");

    // Blockquotes
    escaped = escaped.replace(/^> (.*$)/gm, "<blockquote>$1</blockquote>");

    // Bold & Italic
    escaped = escaped.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    escaped = escaped.replace(/\*([^*]+)\*/g, "<em>$1</em>");

    // Unordered lists
    escaped = escaped.replace(/^[\*\-] (.*$)/gm, "<li>$1</li>");
    escaped = escaped.replace(/(<li>.*<\/li>)/s, "<ul>$1</ul>");

    // Paragraphs / line breaks
    escaped = escaped.replace(/\n\n+/g, "</p><p>");
    escaped = "<p>" + escaped + "</p>";
    escaped = escaped.replace(/<p>\s*<\/p>/g, "");
    escaped = escaped.replace(/<p>(<h[1-3]>)/g, "$1");
    escaped = escaped.replace(/(<\/h[1-3]>)<\/p>/g, "$1");
    escaped = escaped.replace(/<p>(<pre>)/g, "$1");
    escaped = escaped.replace(/(<\/pre>)<\/p>/g, "$1");
    escaped = escaped.replace(/<p>(<hr>)<\/p>/g, "$1");

    return escaped;
  }

  // Modals
  function openItemModal(item) {
    state.selectedItem = item;
    const isPrompt = item.item_type === "prompt";
    modalTypeBadge.textContent = isPrompt ? "Prompt" : "Appendix";
    modalTypeBadge.className = `badge ${isPrompt ? "badge-prompt" : "badge-appendix"}`;
    modalTitle.textContent = item.title;
    modalFilename.textContent = item.filename;
    modalContent.textContent = item.content;
    itemModal.classList.remove("hidden");
  }

  function closeItemModal() {
    itemModal.classList.add("hidden");
    state.selectedItem = null;
  }

  function openSaveModal(defaultType = "prompts", isNewEmpty = false) {
    saveType.value = defaultType;
    saveTitle.value = "";
    saveFilename.value = "";
    saveDesc.value = "";
    saveModal.classList.remove("hidden");
    saveTitle.focus();
  }

  function closeSaveModal() {
    saveModal.classList.add("hidden");
  }

  async function handleSaveSubmit(e) {
    e.preventDefault();
    const type = saveType.value; // 'prompts' or 'appendices'
    const title = saveTitle.value.trim();
    const filename = saveFilename.value.trim();
    const desc = saveDesc.value.trim();

    if (!title || !filename) {
      showToast("Please provide both title and filename", "error");
      return;
    }

    const currentContent = editor.value.trim();
    const frontmatter = `---\ntitle: ${title}\n${desc ? `description: ${desc}\n` : ""}tags: custom\n---\n\n`;
    const fullContent = frontmatter + (currentContent || `# ${title}\n\nAdd prompt instructions here.`);

    const endpoint = type === "prompts" ? "/api/prompts" : "/api/appendices";

    try {
      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename, content: fullContent }),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.error || "Save failed");
      }

      showToast(`Saved '${filename}' to library!`, "success");
      closeSaveModal();
      fetchLibrary();
    } catch (err) {
      showToast("Save error: " + err.message, "error");
    }
  }

  // Utilities
  function updateStats() {
    const val = editor.value;
    const chars = val.length;
    const words = val.trim() ? val.trim().split(/\s+/).length : 0;
    const lines = val ? val.split("\n").length : 1;
    // Heuristic: ~4 characters per token
    const tokens = Math.ceil(chars / 4);

    statWords.textContent = `${words} word${words === 1 ? "" : "s"}`;
    statChars.textContent = `${chars} char${chars === 1 ? "" : "s"}`;
    statTokens.textContent = `~${tokens} token${tokens === 1 ? "" : "s"}`;
    statLines.textContent = `${lines} line${lines === 1 ? "" : "s"}`;
  }

  function stripFrontmatter(text) {
    return text.replace(/^---\s*\n.*?\n---\s*\n?/s, "");
  }

  function escapeHTML(str) {
    if (!str) return "";
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function showToast(message, type = "info") {
    const container = document.getElementById("toast-container");
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    toast.textContent = message;

    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transition = "opacity 0.3s ease";
      setTimeout(() => toast.remove(), 300);
    }, 3200);
  }

  // Start app
  init();
})();
