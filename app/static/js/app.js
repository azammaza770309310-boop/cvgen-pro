/* CVGen Pro — Frontend application logic
   Vanilla JS. Cloud-AI-only. Single official template. Inline click-to-edit.
*/
(function () {
  "use strict";

  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));

  // Null-safe helpers for assignments (?. cannot be used on left side of =)
  function showEl(el, display) { if (el) el.style.display = display || "flex"; }
  function hideEl(el) { if (el) el.style.display = "none"; }
  function setText(el, text) { if (el) el.textContent = text; }



  const state = {
    data: emptyResume(),
    templateId: "official_bilingual_master",
    templates: [],
    templateIndex: 0,
    font: "Cairo",
    displayLang: "bilingual",
    providers: [],
    currentPage: 1,
    pageCount: 1,
    selectedElement: null,
    selectedSection: null,
    // Style overrides for asymmetric_dark template (saved on color picker change)
    styleOverrides: {
      sidebarColor: null,     // e.g. "#1a365d"
      pillColor: null,        // e.g. "#1a365d"
      pillRadius: null,       // e.g. "20" (pt)
      sidebarRadius: null,    // e.g. "12" (pt)
      sidebarWidth: null,     // e.g. "35" (%)
    },
    controls: { fontSize: 11, lineHeight: 1.5, sectionSpacing: 2, columnDistance: 4, margin: 15 },
    controlLimits: {
      fontSize: { min: 5.0, max: 14.0, step: 0.3 },
      lineHeight: { min: 0.8, max: 2.0, step: 0.05 },
      sectionSpacing: { min: 0, max: 20, step: 1 },
      columnDistance: { min: 0, max: 40, step: 1 },
      margin: { min: 1, max: 25, step: 0.5 },
    },
  };

  function emptyResume() {
    return {
      personal: { name_en: "", name_ar: "", title_en: "", title_ar: "", email: "", phone: "", location: "", linkedin: "", website: "", github: "" },
      summary: { en: "", ar: "" },
      objective: {},
      experience: [],
      education: [],
      skills: [],
      technical_skills: [],
      soft_skills: [],
      courses: [],
      certifications: [],
      languages: [],
      projects: [],
      volunteering: [],
      achievements: [],
      references: [],
      other: [],
    };
  }

  function toast(msg, type = "info") {
    const el = document.createElement("div");
    el.className = "toast " + type;
    el.textContent = msg;
    $("#toastContainer")?.appendChild(el);
    setTimeout(() => { el.style.opacity = "0"; el.style.transition = "opacity 0.3s"; setTimeout(() => el.remove(), 300); }, 3500);
  }

  function api(path, opts = {}) {
    const cfg = { headers: { "Content-Type": "application/json" }, ...opts };
    if (cfg.body && typeof cfg.body !== "string") cfg.body = JSON.stringify(cfg.body);
    return fetch(path, cfg).then(async (r) => {
      if (!r.ok) {
        let detail = r.statusText;
        try { const j = await r.json(); detail = j.detail || j.error || JSON.stringify(j).slice(0, 200); } catch (_) {}
        throw new Error(detail);
      }
      const ct = r.headers.get("content-type") || "";
      if (ct.includes("application/json")) return r.json();
      return r.blob();
    });
  }

  function setPath(obj, path, value) {
    const parts = path.split(".");
    let cur = obj;
    for (let i = 0; i < parts.length - 1; i++) { if (!cur[parts[i]]) cur[parts[i]] = {}; cur = cur[parts[i]]; }
    cur[parts[parts.length - 1]] = value;
  }
  function getPath(obj, path) {
    const parts = path.split(".");
    let cur = obj;
    for (const p of parts) { if (cur == null) return ""; cur = cur[p]; }
    return cur ?? "";
  }
  function esc(s) { return String(s || "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])); }

  // ---------------- Templates ----------------
  async function loadTemplates() {
    try {
      const res = await api("/api/templates/");
      const count = res.count;
      state.templates = res.templates || [];
      const fb = $("#featureBadges");
      fb.innerHTML = `<span class="feature-badge">${count} <span>قالب رسمي</span></span><span class="feature-badge">متوافق ATS</span><span class="feature-badge">عربي + إنجليزي</span><span class="feature-badge">تحرير مباشر</span>`;
      // Show the currently selected template's name (or the first one)
      const current = state.templates.find(t => t.id === state.templateId) || state.templates[0];
      if (current) {
        state.templateId = current.id;
        state.templateIndex = state.templates.indexOf(current);
        $("#tpName").textContent = current.name_ar || current.name || "—";
      }
    } catch (e) { toast("فشل تحميل القوالب: " + e.message, "error"); }
  }

  // Cycle to the next template and re-render the preview
  function cycleTemplate() {
    if (!state.templates || state.templates.length === 0) {
      toast("لا توجد قوالب متاحة", "info");
      return;
    }
    state.templateIndex = (state.templateIndex + 1) % state.templates.length;
    const next = state.templates[state.templateIndex];
    state.templateId = next.id;
    $("#tpName").textContent = next.name_ar || next.name || "—";
    toast(`تم التبديل إلى: ${next.name_ar || next.name}`, "success");
    // Re-render the preview if we're in editor mode and have data
    if ($("#editorView")?.style.display !== "none" && state.data && state.data.personal) {
      renderPreview();
    }
  }

  // ---------------- Providers ----------------
  async function loadProviders() {
    try {
      const res = await api("/api/settings/");
      state.providers = res.providers || [];
      const anyConfigured = state.providers.some(p => p.configured);
      const dot = $("#aiStatusDot"); if (dot) dot.className = "status-dot" + (anyConfigured ? "" : " off");
      setText($("#aiStatusText"), anyConfigured ? "الذكاء الاصطناعي السحابي جاهز" : "لم يتم إعداد مزود — يلزم مفتاح API");
      const sel = $("#providerSelect");
      if (sel) sel.innerHTML = "";
      const autoOpt = document.createElement("option");
      autoOpt.value = "";
      autoOpt.textContent = "تلقائي — حسب ترتيب المزودين";
      if (sel) sel.appendChild(autoOpt);
      state.providers.forEach(p => {
        const opt = document.createElement("option");
        opt.value = p.id;
        opt.textContent = `${p.name} ${p.configured ? "✓" : "✗"}`;
        if (!p.configured) opt.disabled = true;
        if (sel) sel.appendChild(opt);
      });
      renderKeyManagementUI();
    } catch (e) { toast("فشل تحميل المزودين: " + e.message, "error"); }
  }

  function renderKeyManagementUI() {
    const list = $("#providerList");
    if (!list) return;
    list.innerHTML = "";
    state.providers.forEach(p => {
      const card = document.createElement("div");
      card.className = "key-provider-card";
      const keys = p.keys || [];
      const keysHtml = keys.map(k => `<div class="kpc-key"><span class="kpc-key-masked">${esc(k.masked)}</span><span style="display:flex;align-items:center;gap:6px"><span class="kpc-key-source ${k.source}">${k.source === "env" ? "بيئة" : "مضاف"}</span><button class="kpc-key-delete" data-provider="${p.id}" data-index="${k.file_index != null ? k.file_index : -1}" ${k.deletable ? "" : "disabled"} title="${k.deletable ? "حذف" : "مفتاح بيئة"}">🗑</button></span></div>`).join("");
      const linkHtml = p.key_link ? `<a href="${esc(p.key_link)}" target="_blank" class="kpc-link">🔗 الحصول على مفتاح من ${esc(p.key_link_label)} ←</a>` : "";
      // Add "Test" button for Gemini only
      const testBtnHtml = p.id === "gemini" ? `<button class="kpc-test-btn" data-test-gemini="${p.id}" title="اختبار المفتاح بطلب حقيقي">🔬 اختبار المفتاح</button>` : "";
      card.innerHTML = `<div class="kpc-header"><div class="kpc-name"><span class="status-dot ${p.configured ? "" : "off"}"></span>${esc(p.name)} ${p.key_count > 0 ? `<span style="font-size:11px;color:var(--text-muted)">(${p.key_count} مفتاح)</span>` : ""}</div></div><div class="kpc-desc">${esc(p.description)}</div>${linkHtml}<div class="kpc-keys">${keysHtml || '<div style="font-size:12px;color:var(--text-dim);padding:4px 0">لا توجد مفاتيح</div>'}</div><div class="kpc-add"><input type="text" placeholder="الصق المفتاح هنا..." dir="ltr" id="keyInput-${p.id}"><button data-add-provider="${p.id}">+ إضافة</button>${testBtnHtml}</div><div class="kpc-test-result" id="testResult-${p.id}" style="display:none"></div>`;
      list.appendChild(card);
    });
    $$("[data-add-provider]").forEach(btn => {
      btn.addEventListener("click", async () => {
        const pid = btn.dataset.addProvider;
        const input = $(`#keyInput-${pid}`);
        const key = input.value.trim();
        if (!key) { toast("أدخل المفتاح أولاً", "warn"); return; }
        btn.disabled = true; btn.textContent = "...";
        try {
          const res = await api("/api/settings/keys", { method: "POST", body: { provider: pid, key } });
          toast(res.message || "تم إضافة المفتاح", "success");
          input.value = "";
          await loadProviders();
        } catch (e) { toast("فشل الإضافة: " + e.message, "error"); }
        btn.disabled = false; btn.textContent = "+ إضافة";
      });
    });
    // Wire up Gemini test button
    $$("[data-test-gemini]").forEach(btn => {
      btn.addEventListener("click", async () => {
        const pid = btn.dataset.testGemini;
        const input = $(`#keyInput-${pid}`);
        let key = input.value.trim();
        // If input is empty, try to use the first saved key (but we don't have it in full)
        if (!key) {
          toast("أدخل المفتاح في الحقل أولاً لاختباره", "warn");
          return;
        }
        btn.disabled = true; btn.textContent = "جاري الاختبار...";
        const resultDiv = $(`#testResult-${pid}`);
        resultDiv.style.display = "block";
        resultDiv.innerHTML = '<div style="padding:8px;color:var(--text-muted)">جاري إرسال طلب حقيقي لـ Google Gemini...</div>';
        try {
          const res = await api("/api/settings/test-gemini", { method: "POST", body: { key } });
          if (res.success) {
            resultDiv.innerHTML = `
              <div style="background:rgba(34,197,94,0.1);border:1px solid rgba(34,197,94,0.4);border-radius:6px;padding:10px;margin-top:8px">
                <div style="color:#4ade80;font-weight:700;margin-bottom:4px">✅ ${esc(res.message)}</div>
                <div style="font-size:11px;color:var(--text-muted)">
                  <div>Endpoint: <code dir="ltr">${esc(res.endpoint)}</code></div>
                  <div>Model: <code dir="ltr">${esc(res.model)}</code></div>
                  <div>HTTP Status: <strong>${res.http_status}</strong></div>
                  <div>Authenticated: <strong>${res.authenticated ? "نعم" : "لا"}</strong></div>
                  <div>Response: <code dir="ltr">${esc(res.response_text)}</code></div>
                  <div>Key: <code dir="ltr">${esc(res.key_masked)}</code></div>
                </div>
              </div>`;
          } else {
            const errorTypeLabels = {
              "invalid_key": "مفتاح API غير صالح",
              "auth_error": "خطأ في المصادقة",
              "permission_error": "خطأ في الصلاحيات",
              "model_not_found": "النموذج غير موجود",
              "quota_exceeded": "تجاوز الحصة (Rate Limit)",
              "network_error": "خطأ في الشبكة",
              "invalid_request": "طلب غير صالح",
              "server_error": "خطأ في الخادم",
              "unknown": "خطأ غير معروف",
            };
            resultDiv.innerHTML = `
              <div style="background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.4);border-radius:6px;padding:10px;margin-top:8px">
                <div style="color:#fca5a5;font-weight:700;margin-bottom:4px">❌ ${esc(errorTypeLabels[res.error_type] || "فشل")}</div>
                <div style="font-size:11px;color:var(--text-muted)">
                  <div>الخطأ من Google: <code dir="ltr">${esc(res.error)}</code></div>
                  <div>HTTP Status: <strong>${res.http_status}</strong></div>
                  <div>Endpoint: <code dir="ltr">${esc(res.endpoint)}</code></div>
                  <div>Model: <code dir="ltr">${esc(res.model)}</code></div>
                  <div>Key: <code dir="ltr">${esc(res.key_masked)}</code></div>
                </div>
              </div>`;
          }
        } catch (e) {
          resultDiv.innerHTML = `<div style="color:#fca5a5;padding:8px">خطأ: ${esc(e.message)}</div>`;
        }
        btn.disabled = false; btn.textContent = "🔬 اختبار المفتاح";
      });
    });
    $$(".kpc-key-delete:not(:disabled)").forEach(btn => {
      btn.addEventListener("click", async () => {
        const pid = btn.dataset.provider;
        const idx = parseInt(btn.dataset.index);
        if (idx < 0 || !confirm("حذف هذا المفتاح؟")) return;
        btn.disabled = true;
        try {
          await api(`/api/settings/keys/${pid}/${idx}`, { method: "DELETE" });
          toast("تم الحذف", "success");
          await loadProviders();
        } catch (e) { toast("فشل الحذف: " + e.message, "error"); }
      });
    });
  }

  // ---------------- Generate ----------------
  async function generate() {
    const text = $("#rawInput").value.trim();
    if (!text) { toast("الصق نص السيرة أولاً.", "warn"); return; }
    const anyConfigured = state.providers.some(p => p.configured);
    if (!anyConfigured) {
      showErrorBanner("لم يتم إعداد مزود ذكاء اصطناعي. يرجى إعداد مفتاح API من الإعدادات.");
      showEl($("#settingsModal"), "flex");
      return;
    }
    hideErrorBanner();
    const btn = $("#btnGenerate");
    btn.disabled = true;
    $("#ctaIcon").innerHTML = '<span class="spinner"></span>';
    $("#ctaText").textContent = "جاري تحليل السيرة بالذكاء الاصطناعي...";
    try {
      const res = await api("/api/ai/parse", { method: "POST", body: { text, provider: $("#providerSelect").value, lang: "auto" } });
      if (res.success && res.data) {
        $("#ctaText").textContent = "جاري تجهيز المعاينة...";
        state.data = res.data;
        await sleep(200);
        showEditor();
        await renderPreview();
        toast("تم توليد السيرة بنجاح", "success");
      } else if (res.code === "ai_provider_not_configured") {
        showErrorBanner(res.error);
        showEl($("#settingsModal"), "flex");
      } else {
        toast(res.error || "فشل التوليد", "error");
      }
    } catch (e) { toast("فشل التوليد: " + e.message, "error"); }
    btn.disabled = false;
    $("#ctaIcon").textContent = "⚡";
    $("#ctaText").textContent = "توليد ومعاينة السيرة الذاتية";
  }

  function showErrorBanner(msg) { setText($("#errorBannerText"), msg); showEl($("#errorBanner"), "flex"); }
  function hideErrorBanner() { hideEl($("#errorBanner")); }
  function showEditor() { hideEl($("#landingView")); showEl($("#editorView"), "flex"); }
  function hideEditor() { hideEl($("#editorView")); showEl($("#landingView"), "flex"); }
  function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

  // ---------------- Design steppers ----------------
  function initSteppers() {
    $$(".stepper-mini").forEach(st => {
      const control = st.dataset.control;
      const lim = state.controlLimits[control];
      const valEl = st.querySelector(".s-value");
      const minus = st.querySelector(".s-minus");
      const plus = st.querySelector(".s-plus");
      function refresh() {
        const v = state.controls[control];
        valEl.textContent = control === "fontSize" ? v.toFixed(1) : (control === "lineHeight" ? v.toFixed(2) : v);
        minus.disabled = v <= lim.min;
        plus.disabled = v >= lim.max;
      }
      minus.addEventListener("click", () => {
        state.controls[control] = Math.max(lim.min, +(state.controls[control] - lim.step).toFixed(2));
        refresh(); applyDesignVars();
      });
      plus.addEventListener("click", () => {
        state.controls[control] = Math.min(lim.max, +(state.controls[control] + lim.step).toFixed(2));
        refresh(); applyDesignVars();
      });
      refresh();
    });
  }

  function applyDesignVars() {
    // Apply CSS variables AND inline styles so font size + margin are VISIBLE.
    // CRITICAL: Update BOTH --cv-body-size (English) AND --cv-body-size-ar (Arabic)
    // so that both languages scale together when the user changes the font size.
    // The Arabic body uses --cv-body-size-ar with !important in templates.css,
    // so we MUST update that variable (not just set inline font-size).
    const fontSize = state.controls.fontSize;
    // Arabic body is +13% larger for visual parity (per templates.css comment)
    const fontSizeAr = (fontSize * 1.13).toFixed(1);

    const targets = [$("#a4Page"), $("#a4Content"), $(".a4-page"), document.documentElement];
    targets.forEach(el => {
      if (!el) return;
      // Set CSS variables (used by templates.css)
      el.style.setProperty("--cv-body-size", fontSize + "pt");
      el.style.setProperty("--cv-body-size-ar", fontSizeAr + "pt");  // CRITICAL: Arabic body
      el.style.setProperty("--cv-body-line-height", state.controls.lineHeight);
      el.style.setProperty("--cv-section-spacing", state.controls.sectionSpacing + "pt");
      el.style.setProperty("--cv-column-gap", state.controls.columnDistance + "pt");
      el.style.setProperty("--cv-page-padding", state.controls.margin + "mm");
    });
    // Apply font size + line height DIRECTLY to ALL text elements for immediate effect
    // This overrides the !important in templates.css because inline styles with
    // !important win over stylesheet !important.
    const content = $("#a4Content");
    if (content) {
      content.style.fontFamily = state.font + ", sans-serif";
      content.querySelectorAll(".a4-page, .section-row, .section-body, .body-en, .body-ar, .section-headings, .section-heading-en, .section-heading-ar, p, li, h1, h2, .item, .item-title, .contact-bar, .contact-item, .editable").forEach(el => {
        el.style.setProperty("font-size", fontSize + "pt", "important");
        el.style.setProperty("line-height", state.controls.lineHeight, "important");
      });
      // Also set on body-ar elements specifically (they have !important in CSS)
      content.querySelectorAll(".body-ar, .body-ar .item, .body-ar li, .body-ar .item-title").forEach(el => {
        el.style.setProperty("font-size", fontSizeAr + "pt", "important");
      });
    }
  }

  // ---------------- Preview + Inline Editing ----------------
  let previewTimer = null;
  function schedulePreview() {
    clearTimeout(previewTimer);
    previewTimer = setTimeout(renderPreview, 200);
  }

  async function renderPreview() {
    if (!state.data.personal.name_en && !state.data.personal.name_ar && !state.data.experience.length) return;
    state.data.lang = state.displayLang;
    try {
      const res = await api("/api/templates/render", { method: "POST", body: { data: state.data, template_id: state.templateId } });
      $("#a4Content").innerHTML = res.html;
      applyDesignVars();
      attachInlineEditors();
      await sleep(50);
      updatePageCount();
      fitA4ToContainer(); // re-scale + update page fill
    } catch (e) { console.error("preview error", e); }
  }

  // ----- INLINE EDITING: single click to edit -----
  function attachInlineEditors() {
    const content = $("#a4Content");
    if (!content) return;

    // Mark all .editable elements as editable (matches new template structure)
    const editables = content.querySelectorAll(".editable");
    editables.forEach(el => {
      el.setAttribute("data-editable", "true");
      // SINGLE CLICK → immediately editable, cursor at click position
      el.addEventListener("click", function(e) {
        e.stopPropagation();
        // If already editing this element, let the browser handle cursor placement
        if (el.getAttribute("contenteditable") === "true") return;
        // Deselect any previously edited element
        if (state.selectedElement && state.selectedElement !== el) {
          state.selectedElement.blur();
        }
        el.setAttribute("contenteditable", "true");
        el.focus();
        // Place cursor at click position (the browser does this automatically
        // when we focus after the click event, but we ensure it)
        selectElement(el);
      });
      // Save on blur
      el.addEventListener("blur", function() {
        el.removeAttribute("contenteditable");
        saveEditFromElement(el);
        // saveEditFromElement handles re-rendering if element was deleted
      });
      // Enter (without shift) = save & blur; Escape = cancel
      el.addEventListener("keydown", function(e) {
        if (e.key === "Enter" && !e.shiftKey && el.getAttribute("contenteditable")) {
          e.preventDefault();
          el.blur();
        }
        if (e.key === "Escape" && el.getAttribute("contenteditable")) {
          el.blur();
        }
      });
      // Prevent formatting from breaking template (paste as plain text)
      el.addEventListener("paste", function(e) {
        e.preventDefault();
        const text = (e.clipboardData || window.clipboardData).getData("text/plain");
        document.execCommand("insertText", false, text);
      });
    });

    // Section selection (click on section heading or body — not on editable text)
    const sections = content.querySelectorAll(".section");
    sections.forEach(sec => {
      sec.addEventListener("click", function(e) {
        if (e.target.closest("[data-editable]")) return; // let text edit handle it
        e.stopPropagation();
        selectSection(sec);
      });
    });

    // Deselect on click outside (on background, not on editable)
    content.addEventListener("mousedown", function(e) {
      if (!e.target.closest("[data-editable]") && !e.target.closest(".section")) {
        deselectAll();
      }
    });

    // ===== SIDEBAR & PILL COLOR PICKER + RESIZE (Canva-style) =====
    // Click on the dark sidebar or contact pill to change its color
    // and resize the sidebar width by dragging
    attachStyleControls(content);
  }

  function attachStyleControls(content) {
    // Find sidebar (dark background div) and contact pill.
    // Use data-role attributes for RELIABLE targeting — the old style* selectors
    // broke as soon as the user changed the color or width (the literal string
    // no longer matched), which is why the color picker stopped working after
    // the first change.
    const sidebar = content.querySelector('[data-role="sidebar"]');
    const pill = content.querySelector('[data-role="pill"]');

    // --- Sidebar: click to show color picker + resize handle ---
    if (sidebar) {
      sidebar.style.cursor = "pointer";
      sidebar.style.position = "relative";

      // Add resize handle (right edge of sidebar)
      const resizeHandle = document.createElement("div");
      resizeHandle.style.cssText = "position:absolute;top:0;bottom:0;right:-3px;width:6px;cursor:ew-resize;background:transparent;z-index:10;";
      resizeHandle.title = "اسحب لتغيير العرض";
      sidebar.appendChild(resizeHandle);

      // Resize logic
      let isResizing = false;
      let startX = 0;
      let startWidth = 0;
      let mainContent = null;

      resizeHandle.addEventListener("mousedown", function(e) {
        e.stopPropagation();
        e.preventDefault();
        isResizing = true;
        startX = e.clientX;
        startWidth = sidebar.offsetWidth;
        // Find main content (sibling)
        mainContent = sidebar.nextElementSibling;
        document.body.style.userSelect = "none";
      });

      document.addEventListener("mousemove", function(e) {
        if (!isResizing) return;
        const dx = e.clientX - startX;
        // In RTL layout, dragging right should DECREASE sidebar width (since sidebar is on the right visually... but actually the sidebar is on the LEFT in the DOM). The sidebar is the first child (left side), so dragging right INCREASES its width.
        const parentWidth = sidebar.parentElement.offsetWidth;
        // Clamp width between 25% and 50% of parent (matches the slider bounds)
        const minWidth = parentWidth * 0.25;
        const maxWidth = parentWidth * 0.50;
        const newWidth = Math.max(minWidth, Math.min(maxWidth, startWidth + dx));
        const widthPct = Math.round((newWidth / parentWidth) * 100);
        sidebar.style.width = widthPct + "%";
        if (mainContent) {
          mainContent.style.width = (100 - widthPct) + "%";
        }
        // Save to state for export
        state.styleOverrides.sidebarWidth = widthPct;
      });

      document.addEventListener("mouseup", function() {
        if (isResizing) {
          isResizing = false;
          document.body.style.userSelect = "";
        }
      });

      // Click on sidebar (not on text) to show color picker
      sidebar.addEventListener("click", function(e) {
        // Don't trigger if clicking on editable text or resize handle
        if (e.target.closest("[data-editable]") || e.target === resizeHandle) return;
        e.stopPropagation();
        showSidebarColorPicker(sidebar, pill);
      });
    }

    // --- Contact pill: click to change color ---
    if (pill) {
      pill.style.cursor = "pointer";
      pill.addEventListener("click", function(e) {
        if (e.target.closest("[data-editable]")) return;
        e.stopPropagation();
        showSidebarColorPicker(sidebar, pill);
      });
    }
  }

  function showSidebarColorPicker(sidebar, pill) {
    // Remove any existing color picker popup
    const existing = document.getElementById("sidebarColorPopup");
    if (existing) existing.remove();

    // Create popup
    const popup = document.createElement("div");
    popup.id = "sidebarColorPopup";
    popup.style.cssText = "position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);background:#1a1a1a;border:1px solid #444;border-radius:12px;padding:20px;z-index:9999;box-shadow:0 8px 32px rgba(0,0,0,0.5);";

    const currentColor = sidebar ? (sidebar.style.backgroundColor || "#2D3748") : "#2D3748";
    const currentRadius = pill ? (pill.style.borderRadius || "20pt") : "20pt";

    popup.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
        <h3 style="color:#fff;font-size:16px;margin:0;">تخصيص الألوان والشكل</h3>
        <button id="closeColorPopup" style="background:#333;color:#fff;border:none;width:28px;height:28px;border-radius:50%;cursor:pointer;font-size:14px;">✕</button>
      </div>

      <div style="margin-bottom:16px;">
        <label style="color:#aaa;font-size:12px;display:block;margin-bottom:6px;">لون العمود الجانبي</label>
        <div style="display:flex;gap:8px;flex-wrap:wrap;">
          ${["#2D3748","#1a365d","#1e3a8a","#581c87","#7c2d12","#064e3b","#831843","#374151"].map(c =>
            `<button class="color-swatch" data-color="${c}" data-target="sidebar" style="width:32px;height:32px;border-radius:8px;border:2px solid ${c === currentColor ? '#fff' : 'transparent'};background:${c};cursor:pointer;"></button>`
          ).join("")}
          <input type="color" id="customSidebarColor" value="${rgbToHex(currentColor)}" style="width:32px;height:32px;border:none;cursor:pointer;border-radius:8px;">
        </div>
      </div>

      <div style="margin-bottom:16px;">
        <label style="color:#aaa;font-size:12px;display:block;margin-bottom:6px;">لون شريط التواصل</label>
        <div style="display:flex;gap:8px;flex-wrap:wrap;">
          ${["#2D3748","#1a365d","#1e3a8a","#581c87","#7c2d12","#064e3b","#831843","#374151"].map(c =>
            `<button class="color-swatch" data-color="${c}" data-target="pill" style="width:32px;height:32px;border-radius:8px;border:2px solid transparent;background:${c};cursor:pointer;"></button>`
          ).join("")}
          <input type="color" id="customPillColor" value="${rgbToHex(currentColor)}" style="width:32px;height:32px;border:none;cursor:pointer;border-radius:8px;">
        </div>
      </div>

      <div style="margin-bottom:16px;">
        <label style="color:#aaa;font-size:12px;display:block;margin-bottom:6px;">انحناء الزاوية (الدمعة): <span id="radiusValue">${parseInt(currentRadius) || 20}</span>pt</label>
        <input type="range" id="radiusSlider" min="0" max="40" value="${parseInt(currentRadius) || 20}" style="width:100%;accent-color:#f97316;">
      </div>

      <div style="margin-bottom:8px;">
        <label style="color:#aaa;font-size:12px;display:block;margin-bottom:6px;">انحناء العمود الجانبي: <span id="sidebarRadiusValue">12</span>pt</label>
        <input type="range" id="sidebarRadiusSlider" min="0" max="40" value="12" style="width:100%;accent-color:#f97316;">
      </div>

      <div style="margin-bottom:8px;">
        <label style="color:#aaa;font-size:12px;display:block;margin-bottom:6px;">عرض العمود الجانبي: <span id="sidebarWidthValue">35</span>%</label>
        <input type="range" id="sidebarWidthSlider" min="25" max="50" value="35" step="1" style="width:100%;accent-color:#f97316;">
      </div>
    `;

    document.body.appendChild(popup);

    // Close button
    $("#closeColorPopup").addEventListener("click", () => popup.remove());

    // Color swatches
    $$(".color-swatch").forEach(btn => {
      btn.addEventListener("click", function() {
        const color = this.dataset.color;
        const target = this.dataset.target;
        if (target === "sidebar" && sidebar) {
          sidebar.style.backgroundColor = color;
          sidebar.style.background = color;
          state.styleOverrides.sidebarColor = color;
        }
        if (target === "pill" && pill) {
          pill.style.backgroundColor = color;
          pill.style.background = color;
          state.styleOverrides.pillColor = color;
        }
        // Update selected border
        this.parentElement.querySelectorAll(".color-swatch").forEach(b => b.style.border = "2px solid transparent");
        this.style.border = "2px solid #fff";
      });
    });

    // Custom color pickers
    const customSidebar = $("#customSidebarColor");
    if (customSidebar && sidebar) {
      customSidebar.addEventListener("input", function() {
        sidebar.style.backgroundColor = this.value;
        sidebar.style.background = this.value;
        state.styleOverrides.sidebarColor = this.value;
      });
    }
    const customPill = $("#customPillColor");
    if (customPill && pill) {
      customPill.addEventListener("input", function() {
        pill.style.backgroundColor = this.value;
        pill.style.background = this.value;
        state.styleOverrides.pillColor = this.value;
      });
    }

    // Radius slider (pill / tear shape)
    const radiusSlider = $("#radiusSlider");
    const radiusValue = $("#radiusValue");
    if (radiusSlider && pill) {
      radiusSlider.addEventListener("input", function() {
        const val = this.value;
        radiusValue.textContent = val;
        pill.style.borderRadius = val + "pt";
        state.styleOverrides.pillRadius = val;
      });
    }

    // Sidebar radius slider
    const sbRadiusSlider = $("#sidebarRadiusSlider");
    const sbRadiusValue = $("#sidebarRadiusValue");
    if (sbRadiusSlider && sidebar) {
      // Get current sidebar radius
      const sbStyle = sidebar.style.cssText;
      const radiusMatch = sbStyle.match(/border-radius:(\d+)pt/);
      const currentSbRadius = radiusMatch ? radiusMatch[1] : 12;
      sbRadiusSlider.value = currentSbRadius;
      sbRadiusValue.textContent = currentSbRadius;

      sbRadiusSlider.addEventListener("input", function() {
        const val = this.value;
        sbRadiusValue.textContent = val;
        // Keep one-sided radius (top-left only)
        sidebar.style.borderRadius = val + "pt 0 0 0";
        state.styleOverrides.sidebarRadius = val;
      });
    }

    // Sidebar WIDTH slider (third slider — controls sidebar width %)
    const sbWidthSlider = $("#sidebarWidthSlider");
    const sbWidthValue = $("#sidebarWidthValue");
    if (sbWidthSlider && sidebar) {
      // Get current sidebar width from inline style (e.g. "width:35%" or "width:40%")
      const widthMatch = sidebar.style.width && sidebar.style.width.match(/(\d+)/);
      const currentSbWidth = widthMatch ? parseInt(widthMatch[1], 10) : 35;
      // Clamp to slider bounds [25, 50]
      const clampedWidth = Math.max(25, Math.min(50, currentSbWidth));
      sbWidthSlider.value = clampedWidth;
      sbWidthValue.textContent = clampedWidth;

      sbWidthSlider.addEventListener("input", function() {
        const val = parseInt(this.value, 10);
        sbWidthValue.textContent = val;
        // Apply width to sidebar
        sidebar.style.width = val + "%";
        // Update main content (sibling) width to fill the rest
        const mainContent = sidebar.nextElementSibling;
        if (mainContent) {
          mainContent.style.width = (100 - val) + "%";
        }
        // Save to state for export
        state.styleOverrides.sidebarWidth = val;
      });
    }

    // Click outside to close
    setTimeout(() => {
      document.addEventListener("click", function closeHandler(e) {
        if (!popup.contains(e.target) && !e.target.closest('[data-role="sidebar"]') && !e.target.closest('[data-role="pill"]')) {
          popup.remove();
          document.removeEventListener("click", closeHandler);
        }
      });
    }, 100);
  }

  function selectElement(el) {
    deselectAll();
    state.selectedElement = el;
    el.classList.add("selected-item");
    // Show context bar with color picker
    const contextBar = $("#contextBar");
    const contextLabel = $("#contextLabel");
    if (contextBar) contextBar.style.display = "flex";
    // Determine what this element is
    const label = getElementLabel(el);
    contextLabel.textContent = "تحرير: " + label;
    // Set color picker to current color
    const cs = window.getComputedStyle(el);
    const color = rgbToHex(cs.color);
    $("#contextColorPicker").value = color;
    // Find parent section
    const section = el.closest(".section");
    if (section) {
      state.selectedSection = section;
      section.classList.add("selected-section");
    }
  }

  function selectSection(sec) {
    deselectAll();
    state.selectedSection = sec;
    sec.classList.add("selected-section");
    const contextBar = $("#contextBar");
    const heading = sec.querySelector("h2")?.textContent || "قسم";
    $("#contextLabel").textContent = "قسم: " + heading;
    if (contextBar) contextBar.style.display = "flex";
    const cs = window.getComputedStyle(sec.querySelector("h2") || sec);
    $("#contextColorPicker").value = rgbToHex(cs.color);
  }

  function deselectAll() {
    if (state.selectedElement) {
      state.selectedElement.classList.remove("selected-item");
      state.selectedElement = null;
    }
    if (state.selectedSection) {
      state.selectedSection.classList.remove("selected-section");
      state.selectedSection = null;
    }
    hideEl($("#contextBar"));
  }

  function getElementLabel(el) {
    if (el.classList.contains("header-name-en")) return "الاسم (EN)";
    if (el.classList.contains("header-name-ar")) return "الاسم (AR)";
    if (el.closest(".contact-bar")) return "معلومات الاتصال";
    if (el.tagName === "H2") return "عنوان القسم";
    if (el.classList.contains("item-title")) return "عنوان العنصر";
    if (el.classList.contains("item-subtitle")) return "العنوان الفرعي";
    if (el.classList.contains("item-date")) return "التاريخ";
    if (el.closest(".list-item")) return "عنصر";
    if (el.tagName === "P") return "فقرة";
    if (el.tagName === "LI") return "نقطة";
    return "نص";
  }

  function saveEditFromElement(el) {
    const text = el.textContent.trim();
    const field = el.getAttribute("data-field");

    // Helper: remove empty string from array
    function removeFromArrayIfEmpty(arr, idx) {
      if (!text && idx >= 0 && idx < arr.length) {
        arr.splice(idx, 1);
        return true;
      }
      return false;
    }

    // Helper: check if we need to re-render (element was deleted)
    let needRerender = false;

    if (field) {
      // Direct field mapping via data-field attribute
      if (field === "name_en") state.data.personal.name_en = text;
      else if (field === "name_ar") state.data.personal.name_ar = text;
      else if (field === "email") state.data.personal.email = text;
      else if (field === "phone") state.data.personal.phone = text;
      else if (field === "location" || field === "location_en" || field === "location_ar") state.data.personal.location = text;
      else if (field === "summary_en") {
        if (!text) { state.data.summary.en = ""; } else { state.data.summary.en = text; }
      }
      else if (field === "summary_ar") {
        if (!text) { state.data.summary.ar = ""; } else { state.data.summary.ar = text; }
      }
      else if (field === "skill") {
        // Find the index in the rendered list
        const list = el.closest("ul");
        if (list) {
          const items = Array.from(list.querySelectorAll("li"));
          const idx = items.indexOf(el);
          // Try to find in skills array
          if (idx >= 0) {
            // Check all skill arrays
            const allSkills = [
              ...(state.data.skills || []),
              ...(state.data.skills_en || []),
              ...(state.data.skills_ar || []),
            ];
            // Remove from the array that contains this item
            for (const arr of [state.data.skills, state.data.skills_en, state.data.skills_ar]) {
              if (arr && idx < arr.length) {
                if (!text) {
                  arr.splice(idx, 1);
                  needRerender = true;
                } else {
                  arr[idx] = text;
                }
                break;
              }
            }
          }
        }
      }
      else if (field === "technical_skill") {
        const list = el.closest("ul");
        if (list) {
          const items = Array.from(list.querySelectorAll("li"));
          const idx = items.indexOf(el);
          for (const arr of [state.data.technical_skills, state.data.technical_skills_en, state.data.technical_skills_ar]) {
            if (arr && idx < arr.length) {
              if (!text) {
                arr.splice(idx, 1);
                needRerender = true;
              } else {
                arr[idx] = text;
              }
              break;
            }
          }
        }
      }
      else if (field === "course") {
        const list = el.closest("ul");
        if (list) {
          const items = Array.from(list.querySelectorAll("li"));
          const idx = items.indexOf(el);
          if (state.data.courses && idx >= 0 && idx < state.data.courses.length) {
            if (!text) {
              state.data.courses.splice(idx, 1);
              needRerender = true;
            } else {
              state.data.courses[idx] = text;
            }
          }
        }
      }
      else if (field === "language") {
        const list = el.closest("ul");
        if (list) {
          const items = Array.from(list.querySelectorAll("li"));
          const idx = items.indexOf(el);
          if (state.data.languages && idx >= 0 && idx < state.data.languages.length) {
            if (!text) {
              state.data.languages.splice(idx, 1);
              needRerender = true;
            } else {
              const old = state.data.languages[idx];
              state.data.languages[idx] = { name: text.replace(/\s*\(.*\)$/, ""), level: old?.level || "" };
            }
          }
        }
      }
      else if (field === "bullet") {
        // Experience bullet — find parent experience item
        const expItem = el.closest(".item") || el.closest("div");
        const ul = el.closest("ul");
        if (ul) {
          const items = Array.from(ul.querySelectorAll("li"));
          const idx = items.indexOf(el);
          // Find which experience item this belongs to
          const allExp = state.data.experience || [];
          for (let i = 0; i < allExp.length; i++) {
            const bullets = allExp[i].bullets_en || allExp[i].bullets || [];
            if (idx >= 0 && idx < bullets.length) {
              if (!text) {
                // Remove the bullet
                if (allExp[i].bullets_en) allExp[i].bullets_en.splice(idx, 1);
                if (allExp[i].bullets) allExp[i].bullets.splice(idx, 1);
                if (allExp[i].bullets_ar) allExp[i].bullets_ar.splice(idx, 1);
                needRerender = true;
              } else {
                if (allExp[i].bullets_en) allExp[i].bullets_en[idx] = text;
                if (allExp[i].bullets) allExp[i].bullets[idx] = text;
              }
              break;
            }
          }
        }
      }
      else if (field === "degree" || field === "institution") {
        // Education item
        const expItem = el.closest("div");
        // Find index by counting siblings
        if (expItem) {
          const parent = expItem.parentElement;
          if (parent) {
            const items = Array.from(parent.querySelectorAll(":scope > div"));
            const idx = items.indexOf(expItem);
            if (state.data.education && idx >= 0 && idx < state.data.education.length) {
              if (field === "degree") {
                if (!text && !state.data.education[idx].institution_en && !state.data.education[idx].institution) {
                  state.data.education.splice(idx, 1);
                  needRerender = true;
                } else {
                  state.data.education[idx].degree_en = text;
                  state.data.education[idx].degree = text;
                }
              } else {
                state.data.education[idx].institution_en = text;
                state.data.education[idx].institution = text;
              }
            }
          }
        }
      }
      else if (field === "title" || field === "company" || field === "description") {
        // Experience item
        const expItem = el.closest("div");
        if (expItem) {
          const parent = expItem.parentElement;
          if (parent) {
            const items = Array.from(parent.querySelectorAll(":scope > div"));
            const idx = items.indexOf(expItem);
            if (state.data.experience && idx >= 0 && idx < state.data.experience.length) {
              if (field === "title") {
                state.data.experience[idx].title_en = text;
                state.data.experience[idx].title = text;
              } else if (field === "company") {
                state.data.experience[idx].company_en = text;
                state.data.experience[idx].company = text;
              } else {
                state.data.experience[idx].description = text;
              }
            }
          }
        }
      }
      // Only show toast if not re-rendering
      if (!needRerender) toast("تم التحديث", "success");
    } else {
      // Fallback: use class-based detection
      if (el.classList.contains("header-name-en")) {
        state.data.personal.name_en = text;
      } else if (el.classList.contains("header-name-ar")) {
        state.data.personal.name_ar = text;
      } else if (el.tagName === "LI") {
        const list = el.closest("ul.editable-list");
        const section = el.closest(".section");
        const col = el.closest(".col-en") ? "en" : "ar";
        if (section && list) {
          const items = Array.from(list.querySelectorAll("li"));
          const idx = items.indexOf(el);
          const heading = section.querySelector("h2")?.textContent || "";
          if (heading.includes("SKILLS") || heading.includes("المهارات")) {
            if (heading.includes("TECHNICAL") || heading.includes("التقنية")) {
              if (!text) {
                state.data.technical_skills.splice(idx, 1);
                needRerender = true;
              } else if (idx < state.data.technical_skills.length) {
                state.data.technical_skills[idx] = text;
              }
            } else {
              if (!text) {
                if (idx < state.data.skills.length) state.data.skills.splice(idx, 1);
                needRerender = true;
              } else if (idx < state.data.skills.length) {
                state.data.skills[idx] = text;
              }
            }
          } else if (heading.includes("COURSES") || heading.includes("الدورات")) {
            if (!text) {
              state.data.courses.splice(idx, 1);
              needRerender = true;
            } else if (idx < state.data.courses.length) {
              state.data.courses[idx] = text;
            }
          } else if (heading.includes("LANGUAGES") || heading.includes("اللغات")) {
            if (!text) {
              state.data.languages.splice(idx, 1);
              needRerender = true;
            } else if (idx < state.data.languages.length) {
              const old = state.data.languages[idx];
              state.data.languages[idx] = { name: text.replace(/\s*\(.*\)$/, ""), level: old?.level || "" };
            }
          }
        }
      } else if (el.tagName === "P") {
        const col = el.closest(".col-en") ? "en" : "ar";
        if (col === "en") state.data.summary.en = text;
        else state.data.summary.ar = text;
      }
      if (!needRerender) toast("تم التحديث", "success");
    }

    // If element was deleted (text emptied), re-render to remove it from preview
    if (needRerender) {
      toast("تم الحذف", "success");
      setTimeout(function() {
        if (state.data && state.data.personal) {
          renderPreview();
        }
      }, 100);
    }
  }

  function rgbToHex(rgb) {
    if (!rgb) return "#000000";
    const m = rgb.match(/\d+/g);
    if (!m || m.length < 3) return "#000000";
    return "#" + m.slice(0,3).map(x => parseInt(x).toString(16).padStart(2, "0")).join("");
  }

  // ----- Color control -----
  $("#contextColorPicker")?.addEventListener("input", function() {
    const color = this.value;
    if (state.selectedElement) {
      // Apply to the element OR its parent (for spans inside contact-bar)
      const target = state.selectedElement.closest(".contact-item") || state.selectedElement;
      target.style.color = color;
      // Also apply to all children (spans inside)
      target.querySelectorAll("*").forEach(el => { el.style.color = color; });
    } else if (state.selectedSection) {
      state.selectedSection.querySelectorAll("h2, .item-title, .item-subtitle, .item-date, p, li").forEach(el => {
        el.style.color = color;
      });
    }
  });

  $("#btnContextReset")?.addEventListener("click", function() {
    if (state.selectedElement) {
      state.selectedElement.style.color = "";
      // Also clear inline color on child elements
      state.selectedElement.querySelectorAll("*").forEach(el => { el.style.color = ""; });
    } else if (state.selectedSection) {
      state.selectedSection.querySelectorAll("*").forEach(el => {
        el.style.color = "";
      });
    }
    toast("تم إعادة اللون الافتراضي", "success");
  });

  $("#btnContextClose")?.addEventListener("click", function() {
    if (state.selectedElement) {
      state.selectedElement.blur();
    }
    deselectAll();
  });

  // ----- Formatting buttons (bold, italic, alignment, undo, redo) -----
  $("#btnBold")?.addEventListener("mousedown", function(e) {
    e.preventDefault();
    document.execCommand("bold", false, null);
  });
  $("#btnItalic")?.addEventListener("mousedown", function(e) {
    e.preventDefault();
    document.execCommand("italic", false, null);
  });
  $("#btnAlignLeft")?.addEventListener("mousedown", function(e) {
    e.preventDefault();
    document.execCommand("justifyLeft", false, null);
  });
  $("#btnAlignCenter")?.addEventListener("mousedown", function(e) {
    e.preventDefault();
    document.execCommand("justifyCenter", false, null);
  });
  $("#btnAlignRight")?.addEventListener("mousedown", function(e) {
    e.preventDefault();
    document.execCommand("justifyRight", false, null);
  });
  $("#btnUndo")?.addEventListener("mousedown", function(e) {
    e.preventDefault();
    document.execCommand("undo", false, null);
  });
  $("#btnRedo")?.addEventListener("mousedown", function(e) {
    e.preventDefault();
    document.execCommand("redo", false, null);
  });
  // Add item (adds a new bullet to the current list or a new experience item)
  $("#btnAddItem")?.addEventListener("click", function() {
    if (!state.selectedElement) { toast("حدد عنصراً أولاً", "warn"); return; }
    const el = state.selectedElement;
    const section = el.closest(".section");
    if (!section) return;
    const heading = section.querySelector("h2")?.textContent || "";
    // If it's a bullet list, add a new bullet
    if (el.tagName === "LI") {
      const ul = el.closest("ul.editable-list");
      if (ul) {
        const newLi = document.createElement("li");
        newLi.setAttribute("data-editable", "true");
        newLi.textContent = "عنصر جديد";
        ul.appendChild(newLi);
        attachInlineEditors();
        toast("تم إضافة عنصر", "success");
      }
    } else if (heading.includes("EXPERIENCE")) {
      // Add new experience item to data
      state.data.experience.push({ title_en: "New Position", company_en: "", start_date: "", end_date: "", bullets_en: [] });
      schedulePreview();
      toast("تم إضافة خبرة جديدة", "success");
    } else if (heading.includes("EDUCATION")) {
      state.data.education.push({ degree_en: "New Degree", institution_en: "" });
      schedulePreview();
      toast("تم إضافة تعليم جديد", "success");
    } else {
      toast("لا يمكن إضافة عناصر في هذا القسم", "warn");
    }
  });
  // Delete item
  $("#btnDeleteItem")?.addEventListener("click", function() {
    if (!state.selectedElement) { toast("حدد عنصراً للحذف", "warn"); return; }
    if (!confirm("هل تريد حذف هذا العنصر؟")) return;
    const el = state.selectedElement;
    if (el.tagName === "LI") {
      el.remove();
      toast("تم الحذف", "success");
    } else if (el.classList.contains("list-item")) {
      el.remove();
      toast("تم حذف العنصر", "success");
    } else {
      toast("لا يمكن حذف هذا العنصر", "warn");
    }
  });

  // Keyboard shortcuts for bold/italic
  document.addEventListener("keydown", function(e) {
    if (!state.selectedElement || state.selectedElement.getAttribute("contenteditable") !== "true") return;
    if (e.ctrlKey || e.metaKey) {
      if (e.key === "b" || e.key === "B") { e.preventDefault(); document.execCommand("bold"); }
      if (e.key === "i" || e.key === "I") { e.preventDefault(); document.execCommand("italic"); }
      if (e.key === "z") { e.preventDefault(); document.execCommand("undo"); }
      if (e.key === "y" || e.key === "Y") { e.preventDefault(); document.execCommand("redo"); }
    }
  });

  // ----- Page count -----
  function updatePageCount() {
    const page = $("#a4Page");
    const content = $("#a4Content");
    if (!page || !content) return;
    const A4_HEIGHT = 1123;
    const marginPx = state.controls.margin * 3.7795;
    const contentAreaPerPage = A4_HEIGHT - 2 * marginPx;
    const contentHeight = content.scrollHeight;
    if (contentHeight <= A4_HEIGHT) {
      state.pageCount = 1;
    } else {
      state.pageCount = Math.max(1, Math.ceil(contentHeight / contentAreaPerPage));
    }
    if (state.currentPage > state.pageCount) state.currentPage = state.pageCount;
    $("#pageInfo").textContent = `صفحة ${state.currentPage} من ${state.pageCount}`;
    const warn = $("#overflowWarning");
    const warnText = $("#overflowText");
    if (state.pageCount > 1) {
      warn.style.display = "flex";
      const w = state.pageCount === 2 ? "صفحتان" : state.pageCount + " صفحات";
      warnText.innerHTML = `السيرة تتجاوز صفحة واحدة — <strong>${w}</strong>. عدّل الخط أو الهوامش.`;
    } else {
      warn.style.display = "none";
    }
    const boundary = $(".page1-boundary");
    const badge = $(".page1-badge");
    if (boundary) boundary.style.top = A4_HEIGHT + "px";
    if (badge) badge.style.top = (A4_HEIGHT - 12) + "px";
    fetchTruePageCount();
  }

  let trueCountTimer = null;
  function fetchTruePageCount() {
    clearTimeout(trueCountTimer);
    trueCountTimer = setTimeout(async () => {
      try {
        const res = await api("/api/export/page-count?engine=chromium", {
          method: "POST",
          body: { data: state.data, template_id: state.templateId, lang: state.displayLang },
        });
        if (res.page_count != null) {
          state.pageCount = res.page_count;
          if (state.currentPage > state.pageCount) state.currentPage = state.pageCount;
          $("#pageInfo").textContent = `صفحة ${state.currentPage} من ${state.pageCount}`;
        }
      } catch (e) { /* silent */ }
    }, 1000);
  }

  function fitA4ToContainer() {
    // No longer uses transform:scale() — the .a4-page is now responsive
    // (width:100%, max-width:794px, margin:0 auto) which naturally fits
    // any container without clipping or scaling artifacts.
    // Just update the page fill indicator.
    const scaler = $("#a4Scaler");
    if (scaler) {
      // Clear any leftover transform from previous versions
      scaler.style.transform = "";
      scaler.style.transformOrigin = "";
      scaler.style.width = "";
      scaler.style.height = "";
      scaler.style.marginLeft = "";
      scaler.style.marginRight = "";
    }
    updatePageFill();
  }

  // ---------------- Page Fill Indicator ----------------
  function updatePageFill() {
    const a4Page = $(".a4-page");
    const fillBar = $("#pageFillBar");
    const fillText = $("#pageFillText");
    const pageInfo = $("#pageInfoText");
    if (!a4Page || !fillBar) return;
    // A4 height at 96 DPI = 297mm * 3.7795 ≈ 1123px
    // But the USABLE content height = page height - 2 * padding (top + bottom margin)
    const A4_HEIGHT_PX = 1123;
    const marginPx = (state.controls.margin || 15) * 3.7795; // mm → px
    const usableHeight = A4_HEIGHT_PX - (2 * marginPx);
    // Measure the ACTUAL content height (not scrollHeight which includes padding)
    // Use the #a4Content element's offsetHeight for accuracy
    const contentEl = $("#a4Content");
    let contentHeight = 0;
    if (contentEl) {
      contentHeight = contentEl.offsetHeight;
    } else {
      contentHeight = a4Page.scrollHeight - (2 * marginPx);
    }
    // Calculate percentage of usable area filled
    const pct = Math.min(100, Math.round((contentHeight / usableHeight) * 100));
    // Calculate number of pages (content height / usable height per page)
    const pages = Math.max(1, Math.ceil(contentHeight / usableHeight));
    fillBar.style.width = pct + "%";
    if (pct > 90) {
      fillBar.style.background = "#ef4444";
    } else if (pct > 75) {
      fillBar.style.background = "#f59e0b";
    } else {
      fillBar.style.background = "#22c55e";
    }
    if (fillText) fillText.textContent = pct + "%";
    if (pageInfo) pageInfo.textContent = pages === 1 ? "صفحة 1" : `صفحة 1 من ${pages}`;
  }

  // ---------------- Export ----------------
  async function exportPDF() {
    const btn = $("#btnPdf");
    btn.disabled = true; btn.textContent = "...";
    try {
      // CRITICAL: captureInlineStyles MUST run before building the export body.
      // It saves ALL inline edits (text changes) from the preview DOM into
      // state.data so the PDF receives the EXACT current state.
      captureInlineStyles();
      state.data.lang = state.displayLang;
      // Merge font family into controls so the PDF uses the same font as preview
      const controlsWithFont = Object.assign({}, state.controls, { fontFamily: state.font });
      const body = {
        data: state.data,
        template_id: state.templateId,
        lang: state.displayLang,
        filename: state.data.personal.name_en || state.data.personal.name || "resume",
        controls: controlsWithFont,
        font: state.font,
        style_overrides: state.styleOverrides
      };
      const blob = await api("/api/export/pdf", { method: "POST", body: body });
      downloadBlob(blob, (state.data.personal.name_en || state.data.personal.name || "resume") + ".pdf", "application/pdf");
      toast("تم تنزيل PDF", "success");
    } catch (e) { toast("فشل PDF: " + e.message, "error"); }
    btn.disabled = false; btn.textContent = "تنزيل PDF";
  }

  async function exportDOCX() {
    const btn = $("#btnDocx");
    btn.disabled = true; btn.textContent = "...";
    try {
      captureInlineStyles();
      state.data.lang = state.displayLang;
      const controlsWithFont = Object.assign({}, state.controls, { fontFamily: state.font });
      const blob = await api("/api/export/docx", { method: "POST", body: {
        data: state.data,
        template_id: state.templateId,
        lang: state.displayLang,
        filename: state.data.personal.name_en || state.data.personal.name || "resume",
        controls: controlsWithFont,
        font: state.font
      } });
      downloadBlob(blob, (state.data.personal.name_en || state.data.personal.name || "resume") + ".docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document");
      toast("تم تنزيل Word", "success");
    } catch (e) { toast("فشل Word: " + e.message, "error"); }
    btn.disabled = false; btn.textContent = "تنزيل Word";
  }

  function captureInlineStyles() {
    // Before export: blur any active editor and SAVE its text to state.data
    if (state.selectedElement) {
      saveEditFromElement(state.selectedElement);
      state.selectedElement.blur();
      state.selectedElement = null;
    }
    // Also save ALL editable elements (in case some were edited but not blurred)
    const content = $("#a4Content");
    if (content) {
      // 0. SAFETY NET: Capture inline styles from the asymmetric_dark sidebar & pill.
      // The color picker / resize handle update state.styleOverrides on each change,
      // but this is a backup to guarantee the exported PDF matches the preview DOM
      // even if some event handler was missed or the state got reset.
      // Use data-role attributes for reliable targeting (works regardless of
      // current color/width values).
      const sidebar = content.querySelector('[data-role="sidebar"]');
      const pill = content.querySelector('[data-role="pill"]');
      // Helper: accept both hex (#2D3748) and rgb() formats
      const normalizeColor = (val) => {
        if (!val) return null;
        const s = String(val).trim();
        if (/^#[0-9a-fA-F]{6}$/.test(s)) return s.toLowerCase();
        if (/^#[0-9a-fA-F]{3}$/.test(s)) {
          // expand #abc -> #aabbcc
          return ("#" + s[1]+s[1]+s[2]+s[2]+s[3]+s[3]).toLowerCase();
        }
        // rgb(r, g, b) format
        const m = s.match(/(\d+)\s*,\s*(\d+)\s*,\s*(\d+)/);
        if (m) {
          return "#" + [m[1],m[2],m[3]].map(x => parseInt(x,10).toString(16).padStart(2,"0")).join("").toLowerCase();
        }
        return null;
      };
      if (sidebar) {
        // Capture sidebar background color
        const sbBg = sidebar.style.backgroundColor || sidebar.style.background;
        const sbHex = normalizeColor(sbBg);
        if (sbHex) state.styleOverrides.sidebarColor = sbHex;
        // Capture sidebar width (%)
        const sbW = sidebar.style.width;
        if (sbW) {
          const m = sbW.match(/(\d+)/);
          if (m) {
            const pct = parseInt(m[1], 10);
            if (pct >= 20 && pct <= 60) state.styleOverrides.sidebarWidth = pct;
          }
        }
        // Capture sidebar border-radius
        const sbR = sidebar.style.borderRadius;
        if (sbR) {
          const m = sbR.match(/(\d+)/);
          if (m) state.styleOverrides.sidebarRadius = m[1];
        }
      }
      if (pill) {
        // Capture pill background color
        const pillBg = pill.style.backgroundColor || pill.style.background;
        const pillHex = normalizeColor(pillBg);
        if (pillHex) state.styleOverrides.pillColor = pillHex;
        // Capture pill border-radius
        const pillR = pill.style.borderRadius;
        if (pillR) {
          const m = pillR.match(/(\d+)/);
          if (m) state.styleOverrides.pillRadius = m[1];
        }
      }
      // 1. Save all data-field elements (name, email, phone, location, summary)
      content.querySelectorAll("[data-field]").forEach(el => {
        const text = el.textContent.trim();
        const field = el.getAttribute("data-field");
        if (field && text) {
          if (field === "name_en") state.data.personal.name_en = text;
          else if (field === "name_ar") state.data.personal.name_ar = text;
          else if (field === "email") state.data.personal.email = text;
          else if (field === "phone") state.data.personal.phone = text;
          else if (field === "location") state.data.personal.location = text;
          else if (field === "summary_en") {
            if (!state.data.summary) state.data.summary = {};
            state.data.summary.en = text;
          }
          else if (field === "summary_ar") {
            if (!state.data.summary) state.data.summary = {};
            state.data.summary.ar = text;
          }
        }
      });
      // 2. Save list items (skills, technical_skills, courses, languages)
      content.querySelectorAll("ul.editable-list li").forEach(li => {
        const text = li.textContent.trim();
        const section = li.closest(".section");
        if (section) {
          const heading = section.querySelector("h2")?.textContent || "";
          const list = li.closest("ul.editable-list");
          if (list) {
            const items = Array.from(list.querySelectorAll("li"));
            const idx = items.indexOf(li);
            if (heading.includes("SKILLS") || heading.includes("المهارات")) {
              if (heading.includes("TECHNICAL") || heading.includes("التقنية")) {
                if (idx < state.data.technical_skills.length) state.data.technical_skills[idx] = text;
                else state.data.technical_skills.push(text);
              } else {
                if (idx < state.data.skills.length) state.data.skills[idx] = text;
                else state.data.skills.push(text);
              }
            } else if (heading.includes("COURSES") || heading.includes("الدورات")) {
              if (idx < state.data.courses.length) state.data.courses[idx] = text;
              else state.data.courses.push(text);
            } else if (heading.includes("LANGUAGES") || heading.includes("اللغات")) {
              if (idx < state.data.languages.length) {
                const old = state.data.languages[idx];
                state.data.languages[idx] = { name: text.replace(/\s*\(.*\)$/, ""), level: old?.level || "" };
              }
            }
          }
        }
      });
      // 3. Save experience items (title, company, description, bullets)
      content.querySelectorAll(".item").forEach(item => {
        const section = item.closest(".section");
        if (!section) return;
        const heading = section.querySelector("h2")?.textContent || "";
        const items = Array.from(section.querySelectorAll(".item"));
        const idx = items.indexOf(item);
        if (heading.includes("EXPERIENCE") || heading.includes("الخبرة")) {
          if (idx < state.data.experience.length) {
            const exp = state.data.experience[idx];
            // Save title
            const titleEl = item.querySelector(".item-title");
            if (titleEl) exp.title = titleEl.textContent.trim();
            // Save description (paragraphs)
            const descEls = item.querySelectorAll("p:not(.item-title)");
            if (descEls.length > 0) {
              exp.description = Array.from(descEls).map(p => p.textContent.trim()).join(" ");
            }
            // Save bullets
            const bulletLis = item.querySelectorAll("ul li");
            if (bulletLis.length > 0) {
              exp.bullets = Array.from(bulletLis).map(li => li.textContent.trim());
            }
          }
        } else if (heading.includes("EDUCATION") || heading.includes("المؤهلات") || heading.includes("التعليم")) {
          if (idx < state.data.education.length) {
            const edu = state.data.education[idx];
            const titleEl = item.querySelector(".item-title");
            if (titleEl) edu.degree = titleEl.textContent.trim();
            // Save institution (usually in a sub div or paragraph)
            const subEls = item.querySelectorAll("p:not(.item-title), .sub");
            if (subEls.length > 0) {
              edu.institution = subEls[0].textContent.trim();
            }
          }
        }
      });
      // 4. Remove contenteditable and data-editable attributes (editor-only UI)
      content.querySelectorAll("[contenteditable]").forEach(el => el.removeAttribute("contenteditable"));
      content.querySelectorAll("[data-editable]").forEach(el => el.removeAttribute("data-editable"));
      // 5. Remove selection classes (editor-only UI)
      content.querySelectorAll(".selected-item, .selected-section").forEach(el => {
        el.classList.remove("selected-item", "selected-section");
      });
    }
  }

  function downloadBlob(blob, filename, type) {
    const url = URL.createObjectURL(new Blob([blob], { type }));
    const a = document.createElement("a");
    a.href = url; a.download = filename; document.body.appendChild(a); a.click();
    setTimeout(() => { URL.revokeObjectURL(url); a.remove(); }, 100);
  }

  async function save() {
    const btn = $("#btnSave");
    btn.disabled = true; btn.textContent = "...";
    try {
      const res = await api("/api/resume/save", { method: "POST", body: { data: state.data, name: state.data.personal.name_en || state.data.personal.name || "Untitled" } });
      toast("تم الحفظ", "success");
    } catch (e) { toast("فشل الحفظ: " + e.message, "error"); }
    btn.disabled = false; btn.textContent = "حفظ";
  }

  // ---------------- Wire up ----------------
  // IMPORTANT: Use optional chaining (?.) on ALL addEventListener calls.
  // If any element is missing, the TypeError would crash the entire IIFE
  // and ALL subsequent event handlers + init calls would never run.
  // This was the root cause of the "جاري التحقق..." frozen UI bug.
  $("#btnGenerate")?.addEventListener("click", generate);
  $("#btnLoadSample")?.addEventListener("click", async () => {
    try {
      const res = await api("/api/resume/sample?lang=bilingual");
      state.data = res;
      showEditor();
      await renderPreview();
      toast("تم تحميل النموذج — اضغط على أي نص لتعديله", "success");
    } catch (e) { toast("فشل تحميل النموذج: " + e.message, "error"); }
  });
  $("#btnPdf")?.addEventListener("click", exportPDF);
  $("#btnDocx")?.addEventListener("click", exportDOCX);
  $("#btnSave")?.addEventListener("click", save);
  $("#btnCloseEditor")?.addEventListener("click", hideEditor);
  // Attach to ALL btnSettings elements (there are 2: landing + editor toolbar)
  $$("#btnSettings").forEach(btn => btn.addEventListener("click", () => { showEl($("#settingsModal"), "flex"); }));
  $("#btnErrorSettings")?.addEventListener("click", () => { showEl($("#settingsModal"), "flex"); });
  $("#closeSettings")?.addEventListener("click", () => { hideEl($("#settingsModal")); });
  $("#settingsModal")?.addEventListener("click", (e) => { if (e.target.id === "settingsModal") hideEl($("#settingsModal")); });
  $("#templatePick")?.addEventListener("click", openTemplateGallery);
  // Attach to ALL fontSelect elements (there are 2: config + toolbar)
  $$("#fontSelect").forEach(sel => sel.addEventListener("change", (e) => { state.font = e.target.value; applyDesignVars(); }));

  // ---------------- Template Gallery ----------------
  function openTemplateGallery() {
    showEl($("#templateGalleryModal"), "flex");
    renderTemplateGallery("all");
  }

  function closeTemplateGallery() {
    hideEl($("#templateGalleryModal"));
  }

  function renderTemplateGallery(filter) {
    const grid = $("#templateGrid");
    if (!grid) return;
    grid.innerHTML = "";
    if (!state.templates || state.templates.length === 0) {
      grid.innerHTML = '<div style="grid-column:1/-1;text-align:center;color:#888;padding:40px">لا توجد قوالب متاحة</div>';
      return;
    }
    // Update count in header
    setText($("#tgCount"), state.templates.length + " قالب");

    state.templates.forEach(t => {
      const cat = t.category || "ats";
      let show = false;
      if (filter === "all") show = true;
      else if (filter === "ats") show = (cat === "ats");
      else if (filter === "bilingual") show = (cat === "bilingual");
      else if (filter === "creative") show = (cat === "creative" || cat === "bilingual");
      if (!show) return;

      const isSelected = (t.id === state.templateId);
      const card = document.createElement("div");
      card.className = "tg-card" + (isSelected ? " selected" : "");
      card.dataset.templateId = t.id;

      // Build REAL thumbnail that mimics the actual template layout
      const thumbHtml = buildTemplateThumbnail(t.id, t.accent || "#000");

      card.innerHTML = `
        <div class="tg-check">✓</div>
        <div class="tg-thumb">${thumbHtml}</div>
        <div class="tg-labels">
          <div class="tg-name-ar">${esc(t.name_ar || t.name)}</div>
          <div class="tg-name-en">${esc(t.name || t.id)}</div>
        </div>
      `;
      card.addEventListener("click", () => selectTemplateFromGallery(t.id));
      grid.appendChild(card);
    });
  }

  // Build a mini HTML preview that mimics each template's actual layout
  function buildTemplateThumbnail(templateId, accent) {
    switch (templateId) {
      case "official_bilingual_master":
        // Two-column bilingual: EN left, AR right, with section rows
        return `<div class="thumb-bilingual" style="--ta:${accent}">
          <div class="tb-header">
            <div class="tb-name">John Smith</div>
            <div class="tb-contact">email@ex.com | +123</div>
          </div>
          <div class="tb-divider"></div>
          <div class="tb-row">
            <div class="tb-col">
              <div class="tb-h">OBJECTIVE</div>
              <div class="tb-line w90"></div>
              <div class="tb-line w70"></div>
            </div>
            <div class="tb-col">
              <div class="tb-h">الهدف</div>
              <div class="tb-line w90"></div>
              <div class="tb-line w70"></div>
            </div>
          </div>
          <div class="tb-divider"></div>
          <div class="tb-row">
            <div class="tb-col">
              <div class="tb-h">EXPERIENCE</div>
              <div class="tb-line w80"></div>
              <div class="tb-line w60"></div>
              <div class="tb-line w75"></div>
            </div>
            <div class="tb-col">
              <div class="tb-h">الخبرة</div>
              <div class="tb-line w80"></div>
              <div class="tb-line w60"></div>
              <div class="tb-line w75"></div>
            </div>
          </div>
          <div class="tb-divider"></div>
          <div class="tb-row">
            <div class="tb-col">
              <div class="tb-h">SKILLS</div>
              <div class="tb-line w50"></div>
              <div class="tb-line w65"></div>
            </div>
            <div class="tb-col">
              <div class="tb-h">المهارات</div>
              <div class="tb-line w50"></div>
              <div class="tb-line w65"></div>
            </div>
          </div>
        </div>`;

      case "official_english_single":
        // Single-column English, centered header with blue accent
        return `<div class="thumb-single-en" style="--ta:${accent}">
          <div class="ts-name">John Smith</div>
          <div class="ts-contact">email@ex.com | +123 | NYC</div>
          <div class="ts-divider"></div>
          <div class="ts-h">OBJECTIVE</div>
          <div class="ts-line w90"></div>
          <div class="ts-line w75"></div>
          <div class="ts-h">EXPERIENCE</div>
          <div class="ts-line w80"></div>
          <div class="ts-line w60"></div>
          <div class="ts-line w70"></div>
          <div class="ts-h">EDUCATION</div>
          <div class="ts-line w85"></div>
          <div class="ts-h">SKILLS</div>
          <div class="ts-line w50"></div>
          <div class="ts-line w65"></div>
        </div>`;

      case "official_arabic_single":
        // Single-column Arabic, RTL, centered header
        return `<div class="thumb-single-ar" style="--ta:${accent}" dir="rtl">
          <div class="ts-name">أحمد محمد</div>
          <div class="ts-contact">email@ex.com | +123 | الرياض</div>
          <div class="ts-divider"></div>
          <div class="ts-h">الهدف الوظيفي</div>
          <div class="ts-line w90"></div>
          <div class="ts-line w75"></div>
          <div class="ts-h">الخبرات</div>
          <div class="ts-line w80"></div>
          <div class="ts-line w60"></div>
          <div class="ts-line w70"></div>
          <div class="ts-h">التعليم</div>
          <div class="ts-line w85"></div>
          <div class="ts-h">المهارات</div>
          <div class="ts-line w50"></div>
          <div class="ts-line w65"></div>
        </div>`;

      case "professional_classic":
        // Professional Classic: centered name, section titles with borders, two-column skills
        return `<div class="thumb-pro-classic" style="--ta:${accent}">
          <div class="tpc-name">John Smith</div>
          <div class="tpc-contact">email@ex.com | +123 | NYC</div>
          <div class="tpc-h">CAREER OBJECTIVE</div>
          <div class="tpc-line w90"></div>
          <div class="tpc-line w75"></div>
          <div class="tpc-h">EDUCATION</div>
          <div class="tpc-line w80"></div>
          <div class="tpc-h">EXPERIENCE</div>
          <div class="tpc-line w85"></div>
          <div class="tpc-line w60"></div>
          <div class="tpc-h">COURSES</div>
          <div class="tpc-line w50"></div>
          <div class="tpc-skills-row">
            <div class="tpc-skills-col">
              <div class="tpc-h">SKILLS</div>
              <div class="tpc-line w70"></div>
              <div class="tpc-line w60"></div>
              <div class="tpc-line w65"></div>
            </div>
            <div class="tpc-skills-col">
              <div class="tpc-h">TECHNICAL</div>
              <div class="tpc-line w70"></div>
              <div class="tpc-line w60"></div>
              <div class="tpc-line w65"></div>
            </div>
          </div>
          <div class="tpc-h">LANGUAGES</div>
          <div class="tpc-line w50"></div>
          <div class="tpc-line w45"></div>
        </div>`;

      case "arabic_classic":
        // Arabic Classic: same layout as professional_classic but RTL + Arabic titles
        return `<div class="thumb-ar-classic" style="--ta:${accent}" dir="rtl">
          <div class="tac-name">أحمد محمد</div>
          <div class="tac-contact">بريد | هاتف | الرياض</div>
          <div class="tac-h">الهدف الوظيفي</div>
          <div class="tac-line w90"></div>
          <div class="tac-line w75"></div>
          <div class="tac-h">المؤهلات العلمية</div>
          <div class="tac-line w80"></div>
          <div class="tac-h">الخبرات المهنية</div>
          <div class="tac-line w85"></div>
          <div class="tac-line w60"></div>
          <div class="tac-h">الدورات</div>
          <div class="tac-line w50"></div>
          <div class="tac-skills-row">
            <div class="tac-skills-col">
              <div class="tac-h">المهارات</div>
              <div class="tac-line w70"></div>
              <div class="tac-line w60"></div>
              <div class="tac-line w65"></div>
            </div>
            <div class="tac-skills-col">
              <div class="tac-h">المهارات التقنية</div>
              <div class="tac-line w70"></div>
              <div class="tac-line w60"></div>
              <div class="tac-line w65"></div>
            </div>
          </div>
          <div class="tac-h">اللغات</div>
          <div class="tac-line w50"></div>
          <div class="tac-line w45"></div>
        </div>`;

      case "asymmetric_dark":
        // Asymmetric Dark: dark sidebar on right (one-sided radius), pill contact, flexbox layout
        return `<div class="thumb-asym-dark" style="--ta:${accent}" dir="rtl">
          <div class="tad-name">أحمد محمد</div>
          <div class="tad-pill">
            <span class="tad-pill-dot"></span>
            <span class="tad-pill-dot"></span>
            <span class="tad-pill-dot"></span>
          </div>
          <div class="tad-body">
            <div class="tad-sidebar">
              <div class="tad-sb-h">التعليم</div>
              <div class="tad-sb-line w85"></div>
              <div class="tad-sb-line w60"></div>
              <div class="tad-sb-h">المهارات</div>
              <div class="tad-sb-line w75"></div>
              <div class="tad-sb-line w55"></div>
              <div class="tad-sb-line w65"></div>
              <div class="tad-sb-h">اللغات</div>
              <div class="tad-sb-line w50"></div>
              <div class="tad-sb-line w45"></div>
            </div>
            <div class="tad-main">
              <div class="tad-mc-h">نبذة عني</div>
              <div class="tad-mc-line w90"></div>
              <div class="tad-mc-line w80"></div>
              <div class="tad-mc-line w70"></div>
              <div class="tad-mc-h">الخبرات المهنية</div>
              <div class="tad-mc-line w85"></div>
              <div class="tad-mc-line w60"></div>
              <div class="tad-mc-line w75"></div>
              <div class="tad-mc-line w55"></div>
            </div>
          </div>
        </div>`;

      default:
        // Generic fallback
        return `<div class="thumb-generic" style="--ta:${accent}">
          <div class="tg-name">Template</div>
          <div class="tg-divider"></div>
          <div class="tg-line w80"></div>
          <div class="tg-line w60"></div>
          <div class="tg-line w70"></div>
        </div>`;
    }
  }

  function selectTemplateFromGallery(templateId) {
    state.templateId = templateId;
    const t = state.templates.find(x => x.id === templateId);
    if (t) {
      state.templateIndex = state.templates.indexOf(t);
      setText($("#tpName"), t.name_ar || t.name || "—");
      toast("تم اختيار القالب: " + (t.name_ar || t.name), "success");
    }
    // Close gallery immediately
    closeTemplateGallery();
    // Re-render preview if in editor mode
    if ($("#editorView") && $("#editorView").style.display !== "none" && state.data && state.data.personal) {
      renderPreview();
    }
  }

  // Wire up gallery close buttons
  $("#closeTemplateGallery")?.addEventListener("click", closeTemplateGallery);
  $("#btnCloseGallery")?.addEventListener("click", closeTemplateGallery);
  $("#templateGalleryModal")?.addEventListener("click", (e) => {
    if (e.target.id === "templateGalleryModal") closeTemplateGallery();
  });
  // Wire up filter tabs
  $$(".tg-filter-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      $$(".tg-filter-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      renderTemplateGallery(btn.dataset.filter);
    });
  });

  // Reset all design controls to defaults
  $("#btnResetAll")?.addEventListener("click", function() {
    state.controls = { fontSize: 11, lineHeight: 1.5, sectionSpacing: 2, columnDistance: 4, margin: 15 };
    // Update stepper displays
    $$(".stepper-mini").forEach(st => {
      const control = st.dataset.control;
      const lim = state.controlLimits[control];
      const valEl = st.querySelector(".s-value");
      const v = state.controls[control];
      valEl.textContent = control === "fontSize" ? v.toFixed(1) : (control === "lineHeight" ? v.toFixed(2) : v);
      st.querySelector(".s-minus").disabled = v <= lim.min;
      st.querySelector(".s-plus").disabled = v >= lim.max;
    });
    // Reset all selects
    $$("select.tb-select").forEach(sel => { sel.value = "default"; });
    applyDesignVars();
    toast("تمت إعادة الضبط", "success");
  });

  // Wire up tab buttons
  $$("[data-tab]").forEach(btn => {
    btn.addEventListener("click", () => {
      const tab = btn.dataset.tab;
      if (tab === "templates") toast("القالب الرسمي الوحيد مُفعّل", "info");
      else if (tab === "colors") toast("استخدم منتقي الألوان في شريط التحرير", "info");
      else if (tab === "content") toast("اضغط على أي نص لتعديله", "info");
      else if (tab === "ai") toast("مساعد الذكاء — الصق سيرتك في الصفحة الرئيسية", "info");
    });
  });

  // Escape closes modals + deselects
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      hideEl($("#settingsModal"));
      hideEl($("#addSectionModal"));
      deselectAll();
    }
  });

  window.addEventListener("resize", fitA4ToContainer);

  // ---------------- Add Section Feature ----------------
  function openAddSectionModal() {
    showEl($("#addSectionModal"));
    // Clear previous inputs
    const titleInput = $("#newSectionTitle");
    const contentInput = $("#newSectionContent");
    if (titleInput) titleInput.value = "";
    if (contentInput) contentInput.value = "";
    if (titleInput) titleInput.focus();
  }

  function confirmAddSection() {
    const type = $("#newSectionType")?.value || "custom";
    const title = ($("#newSectionTitle")?.value || "").trim();
    const content = ($("#newSectionContent")?.value || "").trim();

    if (!title && type === "custom") {
      toast("أدخل عنوان القسم", "warn");
      return;
    }

    // Add to state.data based on type
    if (type === "experience") {
      if (!state.data.experience) state.data.experience = [];
      state.data.experience.push({
        title: title || "وظيفة جديدة",
        company: "",
        description: content || "",
        bullets: []
      });
    } else if (type === "education") {
      if (!state.data.education) state.data.education = [];
      state.data.education.push({
        degree: title || "شهادة جديدة",
        institution: content || "",
        year: ""
      });
    } else if (type === "skill") {
      if (!state.data.skills) state.data.skills = [];
      state.data.skills.push(title || content || "مهارة جديدة");
    } else if (type === "course") {
      if (!state.data.courses) state.data.courses = [];
      state.data.courses.push(title || content || "دورة جديدة");
    } else if (type === "language") {
      if (!state.data.languages) state.data.languages = [];
      state.data.languages.push({
        name: title || "لغة جديدة",
        level: content || ""
      });
    } else if (type === "project") {
      if (!state.data.projects) state.data.projects = [];
      state.data.projects.push({
        name: title || "مشروع جديد",
        description: content || ""
      });
    } else {
      // custom section — add as a bullet to skills with title prefix
      if (!state.data.skills) state.data.skills = [];
      state.data.skills.push(title + (content ? ": " + content : ""));
    }

    hideEl($("#addSectionModal"));
    toast("✅ تم إضافة القسم: " + (title || type), "success");
    // Re-render preview
    renderPreview();
  }

  $("#btnAddSection")?.addEventListener("click", openAddSectionModal);
  $("#closeAddSection")?.addEventListener("click", () => { hideEl($("#addSectionModal")); });
  $("#btnConfirmAddSection")?.addEventListener("click", confirmAddSection);
  $("#addSectionModal")?.addEventListener("click", (e) => {
    if (e.target.id === "addSectionModal") hideEl($("#addSectionModal"));
  });

  // ---------------- Init ----------------
  initSteppers();
  loadTemplates();
  loadProviders();
})();
