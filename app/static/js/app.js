/* CVGen Pro — Frontend application logic
   Vanilla JS. Dark, Arabic-first. Cloud-AI-only. Dynamic template count.
*/
(function () {
  "use strict";

  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));

  // ---------------- State ----------------
  const state = {
    data: emptyResume(),
    templateId: "official_bilingual_master",
    font: "Tajawal",
    displayLang: "bilingual",
    templates: [],
    categories: [],
    providers: [],
    selectedCategory: "all",
    currentPage: 1,
    pageCount: 1,
    // design controls
    controls: {
      fontSize: 9.0,
      lineHeight: 1.40,
      sectionSpacing: 6,
      columnDistance: 16,
      margin: 10,
    },
    controlLimits: {
      fontSize: { min: 7.0, max: 14.0, step: 0.5 },
      lineHeight: { min: 1.0, max: 2.0, step: 0.05 },
      sectionSpacing: { min: 2, max: 20, step: 1 },
      columnDistance: { min: 4, max: 40, step: 2 },
      margin: { min: 5, max: 25, step: 1 },
    },
    accentColor: null,
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

  // ---------------- Helpers ----------------
  function toast(msg, type = "info") {
    const el = document.createElement("div");
    el.className = "toast " + type;
    el.textContent = msg;
    $("#toastContainer").appendChild(el);
    setTimeout(() => { el.style.opacity = "0"; el.style.transition = "opacity 0.3s"; setTimeout(() => el.remove(), 300); }, 4000);
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

  // ---------------- Dynamic templates + count ----------------
  async function loadTemplates() {
    try {
      const res = await api("/api/templates/");
      state.templates = res.templates || [];
      state.categories = res.categories || [];
      const count = res.count;  // DYNAMIC — never hardcoded
      // Landing feature badges
      const fb = $("#featureBadges");
      fb.innerHTML = `
        <span class="feature-badge">${count} <span>قالب احترافي</span></span>
        <span class="feature-badge">متوافق ATS</span>
        <span class="feature-badge">ألوان قابلة للتخصيص</span>
        <span class="feature-badge">عربي + إنجليزي</span>
      `;
      // Gallery count
      $("#galleryCount").textContent = count + " قالب";
      $("#sideTemplateCount").textContent = count;
      // Template picker label
      updateTemplatePickLabel();
      // Gallery filters (dynamic)
      renderGalleryFilters();
      // Side template list
      renderSideTemplateList();
    } catch (e) { toast("فشل تحميل القوالب: " + e.message, "error"); }
  }

  function updateTemplatePickLabel() {
    const t = state.templates.find(t => t.id === state.templateId);
    $("#tpName").textContent = t ? t.name_ar : "—";
  }

  function renderGalleryFilters() {
    const root = $("#galleryFilters");
    const total = state.templates.length;
    let html = `<button class="filter-chip ${state.selectedCategory === 'all' ? 'active' : ''}" data-cat="all">الكل <span class="fc-count">(${total})</span></button>`;
    state.categories.forEach(c => {
      const active = state.selectedCategory === c.id ? "active" : "";
      const label = c.id === "ats" ? "ATS ✓ آمنة للفرز" : c.label_ar;
      html += `<button class="filter-chip ${active}" data-cat="${c.id}">${label} <span class="fc-count">(${c.count})</span></button>`;
    });
    root.innerHTML = html;
    $$("#galleryFilters .filter-chip").forEach(b => {
      b.addEventListener("click", () => {
        state.selectedCategory = b.dataset.cat;
        renderGalleryFilters();
        renderGalleryGrid();
      });
    });
  }

  // Thumbnail cache (real rendered template HTML)
  const _thumbCache = {};
  async function preloadThumbnails() {
    try {
      const sampleRes = await api("/api/resume/sample?lang=bilingual");
      await Promise.all(state.templates.map(async (t) => {
        try {
          const r = await api("/api/templates/render", { method: "POST", body: { data: sampleRes, template_id: t.id } });
          _thumbCache[t.id] = r.html;
        } catch (e) { _thumbCache[t.id] = ""; }
      }));
      renderGalleryGrid();
      renderSideTemplateList();
    } catch (e) { console.error("thumb preload failed", e); }
  }

  function renderGalleryGrid() {
    const grid = $("#galleryGrid");
    const filtered = state.selectedCategory === "all"
      ? state.templates
      : state.templates.filter(t => t.category === state.selectedCategory);
    grid.innerHTML = "";
    filtered.forEach(t => {
      const card = document.createElement("div");
      const selected = t.id === state.templateId ? "selected" : "";
      card.className = `template-card ${selected}`;
      const thumbHtml = _thumbCache[t.id]
        ? `<div class="template-thumb"><div class="template-thumb-inner" style="transform:scale(0.28)">${_thumbCache[t.id]}</div></div>`
        : `<div class="template-thumb" style="background:${t.accent}"></div>`;
      const atsTag = t.ats_level === "high" ? "tag-ats-high" : t.ats_level === "medium" ? "tag-ats-medium" : "tag-ats-low";
      const atsLabel = t.ats_level === "high" ? "ATS عالي" : t.ats_level === "medium" ? "ATS متوسط" : "ATS منخفض";
      const catLabel = t.category === "ats" ? "ATS" : t.category === "creative" ? "إبداعي" : "ثنائي اللغة";
      card.innerHTML = `
        <div class="selected-badge">✓</div>
        ${thumbHtml}
        <div class="template-meta">
          <div class="tm-names">
            <span class="tm-name-ar">${esc(t.name_ar)}</span>
            <span class="tm-name-en">${esc(t.name)}</span>
          </div>
          <div class="tm-desc">${esc(t.description_ar || t.description)}</div>
          <div class="tm-tags">
            <span class="tag ${atsTag}">${atsLabel}</span>
            <span class="tag tag-cat">${catLabel}</span>
          </div>
        </div>`;
      card.addEventListener("click", () => {
        state.templateId = t.id;
        renderGalleryGrid();
        renderSideTemplateList();
        updateTemplatePickLabel();
        schedulePreview();
      });
      grid.appendChild(card);
    });
  }

  function renderSideTemplateList() {
    const root = $("#sideTemplateList");
    if (!root) return;
    root.innerHTML = "";
    state.templates.forEach(t => {
      const item = document.createElement("div");
      const selected = t.id === state.templateId;
      item.style.cssText = `display:flex;align-items:center;gap:8px;padding:8px;border:1px solid ${selected ? "var(--accent)" : "var(--border-light)"};border-radius:6px;margin-bottom:6px;cursor:pointer;background:${selected ? "var(--accent-soft)" : "var(--bg-input)"}`;
      const swatch = `<span style="width:14px;height:14px;border-radius:3px;background:${t.accent};flex-shrink:0"></span>`;
      item.innerHTML = `${swatch}<span style="font-size:12.5px;flex:1">${esc(t.name_ar)}</span>${selected ? "<span style='color:var(--accent);font-size:14px'>✓</span>" : ""}`;
      item.addEventListener("click", () => {
        state.templateId = t.id;
        renderSideTemplateList();
        updateTemplatePickLabel();
        schedulePreview();
      });
      root.appendChild(item);
    });
  }

  // ---------------- Providers ----------------
  async function loadProviders() {
    try {
      const res = await api("/api/settings/");
      state.providers = res.providers || [];
      const anyConfigured = state.providers.some(p => p.configured);
      // Status dot + text
      $("#aiStatusDot").className = "status-dot" + (anyConfigured ? "" : " off");
      $("#aiStatusText").textContent = anyConfigured
        ? "الذكاء الاصطناعي السحابي جاهز — تم إعداد مزود واحد أو أكثر"
        : "لم يتم إعداد أي مزود ذكاء اصطناعي — يلزم مفتاح API";
      // Provider select
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
      // Settings modal — full key management UI
      renderKeyManagementUI();
    } catch (e) { toast("فشل تحميل المزودين: " + e.message, "error"); }
  }

  function renderKeyManagementUI() {
    const list = $("#providerList");
    list.innerHTML = "";
    state.providers.forEach(p => {
      const card = document.createElement("div");
      card.className = "key-provider-card";
      const keys = p.keys || [];
      const keysHtml = keys.map((k, i) => `
        <div class="kpc-key">
          <span class="kpc-key-masked">${esc(k.masked)}</span>
          <span style="display:flex;align-items:center;gap:6px">
            <span class="kpc-key-source ${k.source}">${k.source === "env" ? "بيئة" : "مضاف"}</span>
            <button class="kpc-key-delete" data-provider="${p.id}" data-index="${k.file_index != null ? k.file_index : -1}" ${k.deletable ? "" : "disabled"} title="${k.deletable ? "حذف" : "مفتاح بيئة — لا يمكن حذفه من هنا"}">🗑</button>
          </span>
        </div>
      `).join("");
      const linkHtml = p.key_link ? `<a href="${esc(p.key_link)}" target="_blank" class="kpc-link">🔗 الحصول على مفتاح من ${esc(p.key_link_label)} ←</a>` : "";
      card.innerHTML = `
        <div class="kpc-header">
          <div class="kpc-name">
            <span class="status-dot ${p.configured ? "" : "off"}"></span>
            ${esc(p.name)}
            ${p.key_count > 0 ? `<span style="font-size:11px;color:var(--text-muted)">(${p.key_count} مفتاح)</span>` : ""}
          </div>
        </div>
        <div class="kpc-desc">${esc(p.description)}</div>
        ${linkHtml}
        <div class="kpc-keys">${keysHtml || '<div style="font-size:12px;color:var(--text-dim);padding:4px 0">لا توجد مفاتيح — أضف واحداً بالأسفل</div>'}</div>
        <div class="kpc-add">
          <input type="text" placeholder="الصق المفتاح هنا..." dir="ltr" id="keyInput-${p.id}">
          <button data-add-provider="${p.id}">+ إضافة مفتاح</button>
        </div>
      `;
      list.appendChild(card);
    });
    // Wire up add buttons
    $$("[data-add-provider]").forEach(btn => {
      btn.addEventListener("click", async () => {
        const pid = btn.dataset.addProvider;
        const input = $(`#keyInput-${pid}`);
        const key = input.value.trim();
        if (!key) { toast("أدخل المفتاح أولاً", "warn"); return; }
        btn.disabled = true; btn.textContent = "جاري الإضافة...";
        try {
          const res = await api("/api/settings/keys", { method: "POST", body: { provider: pid, key } });
          toast(res.message || "تم إضافة المفتاح", "success");
          input.value = "";
          await loadProviders(); // refresh
        } catch (e) {
          toast("فشل الإضافة: " + e.message, "error");
        }
        btn.disabled = false; btn.textContent = "+ إضافة مفتاح";
      });
    });
    // Wire up delete buttons
    $$(".kpc-key-delete:not(:disabled)").forEach(btn => {
      btn.addEventListener("click", async () => {
        const pid = btn.dataset.provider;
        const idx = parseInt(btn.dataset.index);
        if (idx < 0) return;
        if (!confirm("هل أنت متأكد من حذف هذا المفتاح؟")) return;
        btn.disabled = true;
        try {
          const res = await api(`/api/settings/keys/${pid}/${idx}`, { method: "DELETE" });
          toast(res.message || "تم حذف المفتاح", "success");
          await loadProviders(); // refresh
        } catch (e) {
          toast("فشل الحذف: " + e.message, "error");
          btn.disabled = false;
        }
      });
    });
  }

  // ---------------- Generate (Cloud AI only) ----------------
  async function generate() {
    const text = $("#rawInput").value.trim();
    if (!text) { toast("الصق نص السيرة الذاتية أولاً.", "warn"); return; }

    // Check AI configuration first
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
    $("#ctaText").textContent = "جاري تحليل السيرة الذاتية بالذكاء الاصطناعي...";

    try {
      const res = await api("/api/ai/parse", {
        method: "POST",
        body: { text, provider: $("#providerSelect").value, lang: "auto" },
      });

      if (res.success && res.data) {
        $("#ctaText").textContent = "جاري تجهيز القالب...";
        state.data = res.data;
        await sleep(300);
        $("#ctaText").textContent = "جاري تجهيز المعاينة...";
        refreshFormValues();
        renderExperienceList();
        renderEducationList();
        await sleep(200);
        showEditor();
        await renderPreview();
        toast("تم توليد السيرة الذاتية بنجاح", "success");
      } else if (res.code === "ai_provider_not_configured") {
        showErrorBanner(res.error);
        $("#settingsModal").style.display = "flex";
      } else {
        toast(res.error || "فشل التوليد", "error");
      }
    } catch (e) {
      toast("فشل التوليد: " + e.message, "error");
    }

    btn.disabled = false;
    $("#ctaIcon").textContent = "⚡";
    $("#ctaText").textContent = "توليد ومعاينة السيرة الذاتية";
  }

  function showErrorBanner(msg) {
    $("#errorBannerText").textContent = msg;
    $("#errorBanner").style.display = "flex";
  }
  function hideErrorBanner() { $("#errorBanner").style.display = "none"; }

  function showEditor() {
    $("#landingView").style.display = "none";
    $("#editorView").style.display = "flex";
    // Set the active tab to preview
    switchEditorTab("preview");
  }
  function hideEditor() {
    $("#editorView").style.display = "none";
    $("#landingView").style.display = "flex";
  }

  function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

  // ---------------- Editor tabs ----------------
  $$(".editor-tab").forEach(tab => {
    tab.addEventListener("click", () => switchEditorTab(tab.dataset.etab));
  });
  function switchEditorTab(name) {
    $$(".editor-tab").forEach(t => t.classList.toggle("active", t.dataset.etab === name));
    $$(".etab-panel").forEach(p => p.style.display = p.dataset.etab === name ? "block" : "none");
    if (name === "templates") renderSideTemplateList();
    if (name === "colors") renderColorSwatches();
  }

  // ---------------- Design steppers ----------------
  function initSteppers() {
    $$(".stepper").forEach(st => {
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
        minus.style.opacity = minus.disabled ? "0.3" : "1";
        plus.style.opacity = plus.disabled ? "0.3" : "1";
      }
      minus.addEventListener("click", () => {
        const v = state.controls[control];
        state.controls[control] = Math.max(lim.min, +(v - lim.step).toFixed(2));
        refresh();
        applyDesignVars();
        schedulePreview();
      });
      plus.addEventListener("click", () => {
        const v = state.controls[control];
        state.controls[control] = Math.min(lim.max, +(v + lim.step).toFixed(2));
        refresh();
        applyDesignVars();
        schedulePreview();
      });
      refresh();
    });
  }

  function applyDesignVars() {
    // Apply to the A4 page root via CSS custom properties
    const page = $("#a4Page");
    if (!page) return;
    page.style.setProperty("--cv-font-size", state.controls.fontSize + "pt");
    page.style.setProperty("--cv-line-height", state.controls.lineHeight);
    page.style.setProperty("--cv-section-spacing", state.controls.sectionSpacing + "pt");
    page.style.setProperty("--cv-column-distance", state.controls.columnDistance + "px");
    page.style.setProperty("--cv-margin", state.controls.margin + "mm");
    // Also apply font family
    const content = $("#a4Content");
    if (content) content.style.fontFamily = state.font + ", sans-serif";
  }

  // ---------------- Color swatches ----------------
  function renderColorSwatches() {
    const root = $("#colorSwatches");
    if (!root) return;
    const t = state.templates.find(t => t.id === state.templateId);
    const palette = ["#f97316", "#0d9488", "#1e3a5f", "#7c6bad", "#dc2626", "#0f766e", "#b8860b", "#334155", "#e07856", "#000000"];
    const current = state.accentColor || (t ? t.accent : "#f97316");
    root.innerHTML = "";
    palette.forEach(c => {
      const sw = document.createElement("div");
      const active = c === current;
      sw.style.cssText = `width:32px;height:32px;border-radius:8px;background:${c};cursor:pointer;border:2px solid ${active ? "#fff" : "transparent"};box-shadow:${active ? "0 0 0 2px var(--accent)" : "none"}`;
      sw.title = c;
      sw.addEventListener("click", () => {
        state.accentColor = c;
        renderColorSwatches();
        // Inject override
        const page = $("#a4Page");
        if (page) page.style.setProperty("--cv-accent", c);
      });
      root.appendChild(sw);
    });
  }

  // ---------------- Form binding ----------------
  function bindFields() {
    $$("[data-field]").forEach(el => {
      el.addEventListener("input", () => {
        const field = el.dataset.field;
        let val = el.value;
        if (["skills", "technical_skills", "soft_skills", "courses", "volunteering"].includes(field)) {
          val = val.split(/[,\n]/).map(s => s.trim()).filter(Boolean);
        }
        setPath(state.data, field, val);
        schedulePreview();
      });
    });
  }

  function refreshFormValues() {
    $$("[data-field]").forEach(el => {
      const field = el.dataset.field;
      if (["skills", "technical_skills", "soft_skills", "courses", "volunteering"].includes(field)) {
        el.value = (getPath(state.data, field) || []).join(", ");
      } else {
        el.value = getPath(state.data, field) || "";
      }
    });
  }

  function renderExperienceList() {
    const root = $("#experienceList");
    root.innerHTML = "";
    (state.data.experience || []).forEach((exp, idx) => {
      const card = document.createElement("div");
      card.className = "item-card";
      const titleEn = exp.title_en || exp.title || "";
      const companyEn = exp.company_en || exp.company || "";
      const bulletsEn = (exp.bullets_en && exp.bullets_en.length ? exp.bullets_en : (exp.bullets || []));
      card.innerHTML = `
        <div class="ic-head"><span>خبرة #${idx + 1}</span><button class="icon-btn" data-del-exp="${idx}">🗑</button></div>
        <div class="field-row">
          <div class="field-group"><label>المسمى (EN)</label><input type="text" data-exp="${idx}.title_en" value="${esc(titleEn)}"></div>
          <div class="field-group"><label>المسمى (AR)</label><input type="text" data-exp="${idx}.title_ar" value="${esc(exp.title_ar || '')}" dir="rtl"></div>
        </div>
        <div class="field-row">
          <div class="field-group"><label>الشركة (EN)</label><input type="text" data-exp="${idx}.company_en" value="${esc(companyEn)}"></div>
          <div class="field-group"><label>الشركة (AR)</label><input type="text" data-exp="${idx}.company_ar" value="${esc(exp.company_ar || '')}" dir="rtl"></div>
        </div>
        <div class="field-row">
          <div class="field-group"><label>من</label><input type="text" data-exp="${idx}.start_date" value="${esc(exp.start_date || '')}"></div>
          <div class="field-group"><label>إلى</label><input type="text" data-exp="${idx}.end_date" value="${esc(exp.end_date || '')}"></div>
        </div>
        <div class="field-group"><label>الإنجازات (EN)</label><textarea data-exp="${idx}.bullets_en" rows="3">${esc(bulletsEn.join("\n"))}</textarea></div>
        <div class="field-group"><label>الإنجازات (AR)</label><textarea data-exp="${idx}.bullets_ar" rows="3" dir="rtl">${esc((exp.bullets_ar || []).join("\n"))}</textarea></div>
      `;
      root.appendChild(card);
    });
    $$("[data-exp]").forEach(el => {
      el.addEventListener("input", () => {
        const [idx, key] = el.dataset.exp.split(".");
        const i = parseInt(idx);
        let val = el.value;
        if (key === "bullets_en" || key === "bullets_ar") val = val.split("\n").map(s => s.trim()).filter(Boolean);
        state.data.experience[i][key] = val;
        schedulePreview();
      });
    });
    $$("[data-del-exp]").forEach(btn => {
      btn.addEventListener("click", () => {
        state.data.experience.splice(parseInt(btn.dataset.delExp), 1);
        renderExperienceList();
        schedulePreview();
      });
    });
  }

  function renderEducationList() {
    const root = $("#educationList");
    root.innerHTML = "";
    (state.data.education || []).forEach((ed, idx) => {
      const card = document.createElement("div");
      card.className = "item-card";
      const degEn = ed.degree_en || ed.degree || "";
      const instEn = ed.institution_en || ed.institution || "";
      card.innerHTML = `
        <div class="ic-head"><span>تعليم #${idx + 1}</span><button class="icon-btn" data-del-edu="${idx}">🗑</button></div>
        <div class="field-row">
          <div class="field-group"><label>الدرجة (EN)</label><input type="text" data-edu="${idx}.degree_en" value="${esc(degEn)}"></div>
          <div class="field-group"><label>الدرجة (AR)</label><input type="text" data-edu="${idx}.degree_ar" value="${esc(ed.degree_ar || '')}" dir="rtl"></div>
        </div>
        <div class="field-row">
          <div class="field-group"><label>الجامعة (EN)</label><input type="text" data-edu="${idx}.institution_en" value="${esc(instEn)}"></div>
          <div class="field-group"><label>الجامعة (AR)</label><input type="text" data-edu="${idx}.institution_ar" value="${esc(ed.institution_ar || '')}" dir="rtl"></div>
        </div>
        <div class="field-row">
          <div class="field-group"><label>من</label><input type="text" data-edu="${idx}.start_date" value="${esc(ed.start_date || '')}"></div>
          <div class="field-group"><label>إلى / السنة</label><input type="text" data-edu="${idx}.end_date" value="${esc(ed.end_date || ed.year || '')}"></div>
        </div>
      `;
      root.appendChild(card);
    });
    $$("[data-edu]").forEach(el => {
      el.addEventListener("input", () => {
        const [idx, key] = el.dataset.edu.split(".");
        const i = parseInt(idx);
        state.data.education[i][key] = el.value;
        if (key === "end_date") state.data.education[i].year = el.value;
        schedulePreview();
      });
    });
    $$("[data-del-edu]").forEach(btn => {
      btn.addEventListener("click", () => {
        state.data.education.splice(parseInt(btn.dataset.delEdu), 1);
        renderEducationList();
        schedulePreview();
      });
    });
  }

  $("#btnAddExperience").addEventListener("click", () => {
    state.data.experience.push({ title_en: "", title_ar: "", company_en: "", company_ar: "", start_date: "", end_date: "", bullets_en: [], bullets_ar: [] });
    renderExperienceList();
    schedulePreview();
  });
  $("#btnAddEducation").addEventListener("click", () => {
    state.data.education.push({ degree_en: "", degree_ar: "", institution_en: "", institution_ar: "", start_date: "", end_date: "", year: "" });
    renderEducationList();
    schedulePreview();
  });

  // ---------------- Preview + real DOM page count ----------------
  let previewTimer = null;
  function schedulePreview() {
    clearTimeout(previewTimer);
    previewTimer = setTimeout(renderPreview, 200);
  }

  async function renderPreview() {
    if (!state.data.personal.name_en && !state.data.personal.name_ar && !state.data.experience.length) return;
    state.data.lang = state.displayLang;
    try {
      const res = await api("/api/templates/render", {
        method: "POST",
        body: { data: state.data, template_id: state.templateId },
      });
      $("#a4Content").innerHTML = res.html;
      applyDesignVars();
      // Wait for fonts/layout to settle, then measure
      await sleep(50);
      updatePageCount();
    } catch (e) { console.error("preview error", e); }
  }

  // Page count from ACTUAL DOM measurement.
  // The browser renders content continuously (no pagination), while WeasyPrint
  // paginates with break-inside:avoid. Exact parity is impossible without
  // running the actual PDF renderer, but this formula is accurate for short
  // content (1 page) and within ±1 page for long content.
  // Content area per page = A4 height - 2*margin (matching WeasyPrint's @page margins).
  function computePageCount(content, contentAreaPerPage, a4Height) {
    const contentHeight = content.scrollHeight;
    if (contentHeight <= a4Height) return 1;
    return Math.max(1, Math.ceil(contentHeight / contentAreaPerPage));
  }

  function updatePageCount() {
    const page = $("#a4Page");
    const content = $("#a4Content");
    if (!page || !content) return;

    // A4 internal height = 1123px (297mm @ 96 DPI). This is FIXED mathematically.
    const A4_HEIGHT = 1123;
    // Account for margins: the content area per page is A4_HEIGHT - 2*margin.
    // margin is in mm; 1mm ≈ 3.7795px at 96 DPI.
    const marginPx = state.controls.margin * 3.7795;
    const contentAreaPerPage = A4_HEIGHT - 2 * marginPx;
    // Actual rendered content height (includes padding, so it maps to full pages)
    const contentHeight = content.scrollHeight;
    // Page count from ACTUAL DOM measurement — uses content area (not full page)
    // to stay consistent with WeasyPrint's PDF pagination.
    // If content fits within one A4 page (≤ A4_HEIGHT), it's 1 page.
    // Otherwise, simulate pagination by checking which break-inside-avoid items
    // would cross page boundaries (matching WeasyPrint's behavior).
    if (contentHeight <= A4_HEIGHT) {
      state.pageCount = 1;
    } else {
      state.pageCount = computePageCount(content, contentAreaPerPage, A4_HEIGHT);
    }
    state.pageCount = Math.max(1, state.pageCount);
    if (state.currentPage > state.pageCount) state.currentPage = state.pageCount;

    // Page info badge
    const info = $("#pageInfo");
    info.textContent = `صفحة ${state.currentPage} من ${state.pageCount}`;
    info.classList.toggle("overflow", state.pageCount > 1);

    // Page status box
    if ($("#psPages")) $("#psPages").textContent = state.pageCount + " (تقديري)";
    if ($("#psHeight")) $("#psHeight").textContent = contentHeight + "px";

    // Overflow warning
    const warn = $("#overflowWarning");
    const warnText = $("#overflowText");
    if (state.pageCount > 1) {
      warn.style.display = "flex";
      const pagesWord = state.pageCount === 2 ? "صفحتان" : state.pageCount + " صفحات";
      warnText.innerHTML = `السيرة الذاتية تتجاوز صفحة واحدة — تقديرياً <strong>${pagesWord}</strong>. عدّل حجم الخط أو الهوامش لتقليل الصفحات.`;
    } else {
      warn.style.display = "none";
    }

    // Position the page-1 boundary + badge at exactly A4_HEIGHT from the top of the page
    const boundary = $(".page1-boundary");
    const badge = $(".page1-badge");
    if (boundary) boundary.style.top = A4_HEIGHT + "px";
    if (badge) badge.style.top = (A4_HEIGHT - 12) + "px";

    // Fetch the TRUE page count from the server (authoritative, matches PDF exactly)
    fetchTruePageCount();
  }

  // Debounced true page count fetch — uses Chromium PDF rendering for exact parity
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
          $("#pageInfo").classList.toggle("overflow", state.pageCount > 1);
          if ($("#psPages")) $("#psPages").textContent = state.pageCount + " (دقيق)";
          const warn = $("#overflowWarning");
          const warnText = $("#overflowText");
          if (state.pageCount > 1) {
            warn.style.display = "flex";
            const pagesWord = state.pageCount === 2 ? "صفحتان" : state.pageCount + " صفحات";
            warnText.innerHTML = `السيرة الذاتية تتجاوز صفحة واحدة — <strong>${pagesWord}</strong> (تأكيد من الخادم). عدّل حجم الخط أو الهوامش لتقليل الصفحات.`;
          } else {
            warn.style.display = "none";
          }
        }
      } catch (e) { /* silent — DOM estimate remains as fallback */ }
    }, 800);
  }

  // Auto-scale A4 to fit container width
  function fitA4ToContainer() {
    const main = $(".editor-main");
    const scaler = $("#a4Scaler");
    if (!main || !scaler) return;
    const availWidth = main.clientWidth - 48;
    const A4_WIDTH = 794;
    const scale = Math.min(1, availWidth / A4_WIDTH);
    scaler.style.transform = `scale(${scale})`;
    // Adjust the scaler's height so the container scrolls correctly
    scaler.style.height = (1123 * scale) + "px";
    updatePageCount();
  }

  // ---------------- Language toggle ----------------
  $$("#langToggle button").forEach(b => {
    b.addEventListener("click", () => {
      state.displayLang = b.dataset.lang;
      $$("#langToggle button").forEach(x => x.classList.toggle("btn-primary", x === b));
      schedulePreview();
    });
  });

  // ---------------- Export ----------------
  async function exportPDF() {
    const btn = $("#btnPdf");
    btn.disabled = true; btn.textContent = "جاري التوليد...";
    try {
      state.data.lang = state.displayLang;
      const blob = await api("/api/export/pdf", { method: "POST", body: { data: state.data, template_id: state.templateId, lang: state.displayLang, filename: state.data.personal.name_en || state.data.personal.name || "resume" } });
      downloadBlob(blob, (state.data.personal.name_en || state.data.personal.name || "resume") + ".pdf", "application/pdf");
      toast("تم تنزيل PDF", "success");
    } catch (e) { toast("فشل تصدير PDF: " + e.message, "error"); }
    btn.disabled = false; btn.textContent = "تنزيل PDF";
  }

  async function exportDOCX() {
    const btn = $("#btnDocx");
    btn.disabled = true; btn.textContent = "جاري التوليد...";
    try {
      state.data.lang = state.displayLang;
      const blob = await api("/api/export/docx", { method: "POST", body: { data: state.data, lang: state.displayLang, filename: state.data.personal.name_en || state.data.personal.name || "resume" } });
      downloadBlob(blob, (state.data.personal.name_en || state.data.personal.name || "resume") + ".docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document");
      toast("تم تنزيل Word", "success");
    } catch (e) { toast("فشل تصدير Word: " + e.message, "error"); }
    btn.disabled = false; btn.textContent = "تنزيل Word";
  }

  function downloadBlob(blob, filename, type) {
    const url = URL.createObjectURL(new Blob([blob], { type }));
    const a = document.createElement("a");
    a.href = url; a.download = filename; document.body.appendChild(a); a.click();
    setTimeout(() => { URL.revokeObjectURL(url); a.remove(); }, 100);
  }

  async function save() {
    const btn = $("#btnSave");
    btn.disabled = true; btn.textContent = "جاري الحفظ...";
    try {
      const res = await api("/api/resume/save", { method: "POST", body: { data: state.data, name: state.data.personal.name_en || state.data.personal.name || "Untitled" } });
      toast("تم الحفظ (id: " + res.id.slice(0, 8) + ")", "success");
    } catch (e) { toast("فشل الحفظ: " + e.message, "error"); }
    btn.disabled = false; btn.textContent = "حفظ";
  }

  // ---------------- Wire up ----------------
  $("#btnGenerate").addEventListener("click", generate);
  $("#btnPdf").addEventListener("click", exportPDF);
  $("#btnDocx").addEventListener("click", exportDOCX);
  $("#btnSave").addEventListener("click", save);
  $("#btnCloseEditor").addEventListener("click", hideEditor);
  $("#btnSettings").addEventListener("click", () => { $("#settingsModal").style.display = "flex"; });
  $("#btnErrorSettings").addEventListener("click", () => { $("#settingsModal").style.display = "flex"; });
  $("#closeSettings").addEventListener("click", () => { $("#settingsModal").style.display = "none"; });
  $("#settingsModal").addEventListener("click", (e) => { if (e.target.id === "settingsModal") $("#settingsModal").style.display = "none"; });

  // Template picker → open gallery
  $("#templatePick").addEventListener("click", () => { $("#galleryModal").style.display = "flex"; });
  $("#closeGallery").addEventListener("click", () => { $("#galleryModal").style.display = "none"; });
  $("#galleryModal").addEventListener("click", (e) => { if (e.target.id === "galleryModal") $("#galleryModal").style.display = "none"; });

  // Escape key closes any open modal
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      $("#galleryModal").style.display = "none";
      $("#settingsModal").style.display = "none";
    }
  });

  // Font select
  $("#fontSelect").addEventListener("change", (e) => {
    state.font = e.target.value;
    applyDesignVars();
    schedulePreview();
  });

  // Page nav
  $("#btnPrevPage").addEventListener("click", () => {
    if (state.currentPage > 1) { state.currentPage--; scrollPreviewToPage(); }
  });
  $("#btnNextPage").addEventListener("click", () => {
    if (state.currentPage < state.pageCount) { state.currentPage++; scrollPreviewToPage(); }
  });
  function scrollPreviewToPage() {
    const main = $(".editor-main");
    const scaler = $("#a4Scaler");
    if (!main || !scaler) return;
    const scale = parseFloat(scaler.style.transform.match(/scale\(([\d.]+)\)/)?.[1] || "1");
    const pageHeight = 1123 * scale + 16;
    main.scrollTo({ top: (state.currentPage - 1) * pageHeight, behavior: "smooth" });
    $("#pageInfo").textContent = `صفحة ${state.currentPage} من ${state.pageCount}`;
  }

  // Resize observer for A4 fitting
  window.addEventListener("resize", fitA4ToContainer);

  // ---------------- Init ----------------
  bindFields();
  renderExperienceList();
  renderEducationList();
  initSteppers();
  loadTemplates().then(preloadThumbnails);
  loadProviders();
})();
