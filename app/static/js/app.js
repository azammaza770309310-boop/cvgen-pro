/* CVGen Pro — Frontend application logic
   Vanilla JS. Cloud-AI-only. Single official template. Inline click-to-edit.
*/
(function () {
  "use strict";

  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));

  const state = {
    data: emptyResume(),
    templateId: "official_bilingual_master",
    font: "Cairo",
    displayLang: "bilingual",
    providers: [],
    currentPage: 1,
    pageCount: 1,
    selectedElement: null,
    selectedSection: null,
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
    $("#toastContainer").appendChild(el);
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
      const fb = $("#featureBadges");
      fb.innerHTML = `<span class="feature-badge">${count} <span>قالب رسمي</span></span><span class="feature-badge">متوافق ATS</span><span class="feature-badge">عربي + إنجليزي</span><span class="feature-badge">تحرير مباشر</span>`;
      $("#tpName").textContent = res.templates[0]?.name_ar || "—";
    } catch (e) { toast("فشل تحميل القوالب: " + e.message, "error"); }
  }

  // ---------------- Providers ----------------
  async function loadProviders() {
    try {
      const res = await api("/api/settings/");
      state.providers = res.providers || [];
      const anyConfigured = state.providers.some(p => p.configured);
      $("#aiStatusDot").className = "status-dot" + (anyConfigured ? "" : " off");
      $("#aiStatusText").textContent = anyConfigured ? "الذكاء الاصطناعي السحابي جاهز" : "لم يتم إعداد مزود — يلزم مفتاح API";
      const sel = $("#providerSelect");
      sel.innerHTML = "";
      const autoOpt = document.createElement("option");
      autoOpt.value = "";
      autoOpt.textContent = "تلقائي — حسب ترتيب المزودين";
      sel.appendChild(autoOpt);
      state.providers.forEach(p => {
        const opt = document.createElement("option");
        opt.value = p.id;
        opt.textContent = `${p.name} ${p.configured ? "✓" : "✗"}`;
        if (!p.configured) opt.disabled = true;
        sel.appendChild(opt);
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
      $("#settingsModal").style.display = "flex";
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
        $("#settingsModal").style.display = "flex";
      } else {
        toast(res.error || "فشل التوليد", "error");
      }
    } catch (e) { toast("فشل التوليد: " + e.message, "error"); }
    btn.disabled = false;
    $("#ctaIcon").textContent = "⚡";
    $("#ctaText").textContent = "توليد ومعاينة السيرة الذاتية";
  }

  function showErrorBanner(msg) { $("#errorBannerText").textContent = msg; $("#errorBanner").style.display = "flex"; }
  function hideErrorBanner() { $("#errorBanner").style.display = "none"; }
  function showEditor() { $("#landingView").style.display = "none"; $("#editorView").style.display = "flex"; }
  function hideEditor() { $("#editorView").style.display = "none"; $("#landingView").style.display = "flex"; }
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
    // STRUCTURAL typography (name, headings, contact, dates) is FIXED in CSS
    // via --cv-name-size, --cv-heading-size, --cv-contact-size, --cv-date-size.
    // Only BODY TEXT (p, li, .item) is adjustable via --cv-body-size.
    // We NEVER set el.style.fontSize inline — that would override the fixed
    // structural CSS and cause Preview ≠ PDF mismatch.
    const targets = [$("#a4Page"), $("#a4Content"), $(".a4-page")];
    targets.forEach(el => {
      if (!el) return;
      // Only set the body-size variable — CSS uses this for p, li, .item only
      el.style.setProperty("--cv-body-size", state.controls.fontSize + "pt");
      el.style.setProperty("--cv-body-line-height", state.controls.lineHeight);
      el.style.setProperty("--cv-section-spacing", state.controls.sectionSpacing + "pt");
      el.style.setProperty("--cv-column-gap", state.controls.columnDistance + "pt");
      el.style.setProperty("--cv-page-padding", state.controls.margin + "mm");
      // Do NOT set global fontSize/lineHeight inline — they override structural CSS
    });
    // Apply font family only (does not affect sizes)
    const content = $("#a4Content");
    if (content) {
      content.style.fontFamily = state.font + ", sans-serif";
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
  }

  function selectElement(el) {
    deselectAll();
    state.selectedElement = el;
    el.classList.add("selected-item");
    // Show context bar with color picker
    const contextBar = $("#contextBar");
    const contextLabel = $("#contextLabel");
    contextBar.style.display = "flex";
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
    contextBar.style.display = "flex";
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
    $("#contextBar").style.display = "none";
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
    // Map element to data field using data-field attribute
    const field = el.getAttribute("data-field");
    if (field) {
      // Direct field mapping via data-field attribute
      if (field === "name_en") state.data.personal.name_en = text;
      else if (field === "name_ar") state.data.personal.name_ar = text;
      else if (field === "email") state.data.personal.email = text;
      else if (field === "phone") state.data.personal.phone = text;
      else if (field === "location" || field === "location_en" || field === "location_ar") state.data.personal.location = text;
      else if (field === "summary_en") state.data.summary.en = text;
      else if (field === "summary_ar") state.data.summary.ar = text;
      toast("تم التحديث", "success");
      return;
    }
    // Fallback: use class-based detection
    if (el.classList.contains("header-name-en")) {
      state.data.personal.name_en = text;
    } else if (el.classList.contains("header-name-ar")) {
      state.data.personal.name_ar = text;
    } else if (el.tagName === "LI") {
      // Bullet item — find which list and section
      const list = el.closest("ul.editable-list");
      const section = el.closest(".section");
      const col = el.closest(".col-en") ? "en" : "ar";
      if (section && list) {
        const items = Array.from(list.querySelectorAll("li"));
        const idx = items.indexOf(el);
        const heading = section.querySelector("h2")?.textContent || "";
        if (heading.includes("SKILLS") || heading.includes("المهارات")) {
          if (heading.includes("TECHNICAL") || heading.includes("التقنية")) {
            if (idx < state.data.technical_skills.length) state.data.technical_skills[idx] = text;
          } else {
            if (idx < state.data.skills.length) state.data.skills[idx] = text;
          }
        } else if (heading.includes("COURSES") || heading.includes("الدورات")) {
          if (idx < state.data.courses.length) state.data.courses[idx] = text;
        } else if (heading.includes("LANGUAGES") || heading.includes("اللغات")) {
          if (idx < state.data.languages.length) {
            const old = state.data.languages[idx];
            state.data.languages[idx] = { name: text.replace(/\s*\(.*\)$/, ""), level: old?.level || "" };
          }
        }
      }
    } else if (el.tagName === "P") {
      // Summary paragraph
      const col = el.closest(".col-en") ? "en" : "ar";
      if (col === "en") state.data.summary.en = text;
      else state.data.summary.ar = text;
    }
    toast("تم التحديث", "success");
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
    const area = $(".editor-preview-area");
    const scaler = $("#a4Scaler");
    if (!area || !scaler) return;
    const availWidth = area.clientWidth - 40;
    const A4_WIDTH = 794;
    const scale = Math.min(1, availWidth / A4_WIDTH);
    scaler.style.transform = `scale(${scale})`;
    scaler.style.height = (1123 * scale) + "px";
  }

  // ---------------- Export ----------------
  async function exportPDF() {
    const btn = $("#btnPdf");
    btn.disabled = true; btn.textContent = "...";
    try {
      // Apply inline color edits to data before export
      captureInlineStyles();
      state.data.lang = state.displayLang;
      // Send design controls so PDF matches preview exactly
      const body = {
        data: state.data,
        template_id: state.templateId,
        lang: state.displayLang,
        filename: state.data.personal.name_en || state.data.personal.name || "resume",
        controls: state.controls
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
      state.data.lang = state.displayLang;
      const blob = await api("/api/export/docx", { method: "POST", body: { data: state.data, lang: state.displayLang, filename: state.data.personal.name_en || state.data.personal.name || "resume" } });
      downloadBlob(blob, (state.data.personal.name_en || state.data.personal.name || "resume") + ".docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document");
      toast("تم تنزيل Word", "success");
    } catch (e) { toast("فشل Word: " + e.message, "error"); }
    btn.disabled = false; btn.textContent = "تنزيل Word";
  }

  function captureInlineStyles() {
    // Before export: blur any active editor and strip editing-only attributes
    if (state.selectedElement) {
      state.selectedElement.blur();
    }
    const content = $("#a4Content");
    if (!content) return;
    // Remove contenteditable and data-editable attributes (editor-only UI)
    content.querySelectorAll("[contenteditable]").forEach(el => el.removeAttribute("contenteditable"));
    content.querySelectorAll("[data-editable]").forEach(el => el.removeAttribute("data-editable"));
    // Remove selection classes (editor-only UI)
    content.querySelectorAll(".selected-item, .selected-section").forEach(el => {
      el.classList.remove("selected-item", "selected-section");
    });
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
  $("#btnGenerate").addEventListener("click", generate);
  $("#btnLoadSample").addEventListener("click", async () => {
    try {
      const res = await api("/api/resume/sample?lang=bilingual");
      state.data = res;
      showEditor();
      await renderPreview();
      toast("تم تحميل النموذج — اضغط على أي نص لتعديله", "success");
    } catch (e) { toast("فشل تحميل النموذج: " + e.message, "error"); }
  });
  $("#btnPdf").addEventListener("click", exportPDF);
  $("#btnDocx").addEventListener("click", exportDOCX);
  $("#btnSave").addEventListener("click", save);
  $("#btnCloseEditor").addEventListener("click", hideEditor);
  $("#btnSettings").addEventListener("click", () => { $("#settingsModal").style.display = "flex"; });
  $("#btnErrorSettings").addEventListener("click", () => { $("#settingsModal").style.display = "flex"; });
  $("#closeSettings").addEventListener("click", () => { $("#settingsModal").style.display = "none"; });
  $("#settingsModal").addEventListener("click", (e) => { if (e.target.id === "settingsModal") $("#settingsModal").style.display = "none"; });
  $("#templatePick").addEventListener("click", () => { toast("القالب الرسمي الوحيد مُفعّل", "info"); });
  $("#fontSelect").addEventListener("change", (e) => { state.font = e.target.value; applyDesignVars(); });

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
      $("#settingsModal").style.display = "none";
      deselectAll();
    }
  });

  window.addEventListener("resize", fitA4ToContainer);

  // ---------------- Init ----------------
  initSteppers();
  loadTemplates();
  loadProviders();
})();
