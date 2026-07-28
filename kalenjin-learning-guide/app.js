import { assessments, corePhrases, weeks } from "./guide-data.js";

const STORAGE_KEY = "kalenjin-teacher-guide-v1";
const defaultState = {
  currentWeek: 0,
  values: {},
  checks: {},
  translatorNotes: {},
};

const state = loadState();
const elements = {
  nav: document.querySelector("#week-nav"),
  content: document.querySelector("#lesson-content"),
  coursePercent: document.querySelector("#course-percent"),
  courseProgressBar: document.querySelector("#course-progress-bar"),
  courseProgressCopy: document.querySelector("#course-progress-copy"),
  saveStatus: document.querySelector("#save-status"),
  search: document.querySelector("#search-input"),
  searchResults: document.querySelector("#search-results"),
  sidebar: document.querySelector("#sidebar"),
  menuToggle: document.querySelector("#menu-toggle"),
  modalBackdrop: document.querySelector("#modal-backdrop"),
  modalBody: document.querySelector("#modal-body"),
  restoreInput: document.querySelector("#restore-input"),
  toast: document.querySelector("#toast"),
};

let saveTimer;
let toastTimer;

function loadState() {
  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY));
    return {
      ...defaultState,
      ...saved,
      values: saved?.values || {},
      checks: saved?.checks || {},
      translatorNotes: saved?.translatorNotes || {},
    };
  } catch {
    return { ...defaultState };
  }
}

function persist() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  elements.saveStatus.textContent = "Saving…";
  window.clearTimeout(saveTimer);
  saveTimer = window.setTimeout(() => {
    elements.saveStatus.textContent = "Saved on this device";
  }, 450);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function getValue(key, fallback = "") {
  return Object.hasOwn(state.values, key) ? state.values[key] : fallback;
}

function fieldKey(weekIndex, section, itemIndex) {
  return `w${weekIndex + 1}-${section}-${itemIndex}`;
}

function checkKey(weekIndex, section, itemIndex) {
  return `w${weekIndex + 1}-${section}-${itemIndex}`;
}

function renderNav() {
  elements.nav.innerHTML = weeks
    .map((week, index) => {
      const percent = getWeekProgress(index);
      return `
        <button
          class="week-nav-item ${index === state.currentWeek ? "active" : ""}"
          type="button"
          data-week="${index}"
          aria-current="${index === state.currentWeek ? "page" : "false"}"
        >
          <span class="week-number ${week.color}">${String(index + 1).padStart(2, "0")}</span>
          <span class="week-nav-copy">
            <strong>${escapeHtml(week.shortTitle)}</strong>
            <span>${percent}% complete</span>
          </span>
          <span class="week-tick" aria-hidden="true">${percent === 100 ? "✓" : ""}</span>
        </button>
      `;
    })
    .join("");
}

function renderWeek(index, focusContent = false) {
  state.currentWeek = index;
  const week = weeks[index];
  elements.content.innerHTML = `
    <article class="lesson-page">
      <section class="lesson-hero ${week.color}">
        <div class="hero-pattern" aria-hidden="true"></div>
        <div class="hero-content">
          <span class="eyebrow">Week ${index + 1} of 12</span>
          <h1>${escapeHtml(week.title)}</h1>
          <p>Build confidence from individual words to full conversation.</p>
          <div class="hero-meta">
            <span>60 min Saturday</span>
            <span>30–45 min midweek</span>
            <span>Ages 6–15</span>
          </div>
        </div>
        <div class="week-score">
          <strong id="week-percent">${getWeekProgress(index)}%</strong>
          <span>week ready</span>
        </div>
      </section>

      ${renderObjectives(week)}
      ${renderCorePhrases(index)}
      ${renderTranslationSection(index, "vocab", "Key vocabulary", week.vocabulary)}
      ${renderTranslationSection(index, "target", "Sentence targets", week.targets)}
      ${renderDialogueSection(index, week.dialogue)}
      ${renderLessonFlow(index, week)}
      ${renderTeacherReflection(index)}

      <footer class="lesson-footer">
        <button class="button button-secondary" type="button" data-action="previous-week"
          ${index === 0 ? "disabled" : ""}>Previous week</button>
        <p>Changes save automatically on this device.</p>
        <button class="button button-primary" type="button" data-action="next-week"
          ${index === weeks.length - 1 ? "disabled" : ""}>Next week</button>
      </footer>
    </article>
  `;
  renderNav();
  updateProgress();
  persist();
  closeMobileNav();
  if (focusContent) {
    elements.content.focus({ preventScroll: true });
    window.scrollTo({ top: 0, behavior: "smooth" });
  }
}

function renderObjectives(week) {
  return `
    <section class="section objectives-section">
      <div class="section-heading">
        <span class="section-kicker">Learning outcomes</span>
        <h2>By the end of this week</h2>
      </div>
      <div class="objective-grid">
        ${week.objectives
          .map(
            (objective, index) => `
              <div class="objective-card">
                <span>${String(index + 1).padStart(2, "0")}</span>
                <p>${escapeHtml(objective)}</p>
              </div>
            `,
          )
          .join("")}
      </div>
    </section>
  `;
}

function renderCorePhrases(weekIndex) {
  if (weekIndex !== 0) {
    return `
      <details class="section card collapsible">
        <summary>
          <span><span class="section-kicker">Weekly rhythm</span>Core phrases to recycle</span>
          <span class="summary-action">Show phrases</span>
        </summary>
        <div class="phrase-cloud">
          ${corePhrases.map((phrase) => `<span>${escapeHtml(phrase)}</span>`).join("")}
        </div>
      </details>
    `;
  }
  return `
    <section class="section card">
      <div class="section-heading compact">
        <span class="section-kicker">Weekly rhythm</span>
        <h2>Core phrases to recycle</h2>
        <p>Return to these phrases every week until they feel natural.</p>
      </div>
      <div class="phrase-cloud">
        ${corePhrases.map((phrase) => `<span>${escapeHtml(phrase)}</span>`).join("")}
      </div>
    </section>
  `;
}

function renderTranslationSection(weekIndex, type, title, items) {
  const isVocabulary = type === "vocab";
  return `
    <section class="section card translation-card">
      <div class="section-heading split">
        <div>
          <span class="section-kicker">${isVocabulary ? "Words first" : "Build the phrase"}</span>
          <h2>${title}</h2>
        </div>
        <span class="field-count">${items.length} ${isVocabulary ? "words" : "phrases"}</span>
      </div>
      <div class="translation-table">
        <div class="translation-head">
          <span>English</span>
          <span>Kalenjin translation or teacher note</span>
        </div>
        ${items
          .map((item, itemIndex) => {
            const english = isVocabulary ? item.english : item;
            const fallback = isVocabulary ? item.translation : "";
            const key = fieldKey(weekIndex, type, itemIndex);
            return `
              <label class="translation-row">
                <span class="row-english">
                  <span class="row-number">${String(itemIndex + 1).padStart(2, "0")}</span>
                  <strong>${escapeHtml(english)}</strong>
                </span>
                <span class="input-wrap">
                  <input
                    type="text"
                    data-field="${key}"
                    data-default="${escapeHtml(fallback)}"
                    value="${escapeHtml(getValue(key, fallback))}"
                    placeholder="Add Kalenjin translation or note"
                    autocomplete="off"
                  />
                  <span class="filled-mark" aria-hidden="true">✓</span>
                </span>
              </label>
            `;
          })
          .join("")}
      </div>
    </section>
  `;
}

function renderDialogueSection(weekIndex, items) {
  return `
    <section class="section card">
      <div class="section-heading split">
        <div>
          <span class="section-kicker">Put it together</span>
          <h2>Practice dialogue</h2>
          <p>Read the exchange, then write the final line you want students to use.</p>
        </div>
        <span class="role-badge">Pair practice</span>
      </div>
      <div class="dialogue-list">
        ${items
          .map((item, itemIndex) => {
            const key = fieldKey(weekIndex, "dialogue", itemIndex);
            return `
              <div class="dialogue-card">
                <div class="speech speech-a">
                  <span>A</span><p>${escapeHtml(item.speakerA)}</p>
                </div>
                <div class="speech speech-b">
                  <span>B</span><p>${escapeHtml(item.speakerB)}</p>
                </div>
                <label class="dialogue-input">
                  <span>Kalenjin teaching line</span>
                  <textarea
                    rows="2"
                    data-field="${key}"
                    placeholder="Write the translated exchange or pronunciation note"
                  >${escapeHtml(getValue(key))}</textarea>
                </label>
              </div>
            `;
          })
          .join("")}
      </div>
    </section>
  `;
}

function renderLessonFlow(weekIndex, week) {
  return `
    <section class="section">
      <div class="section-heading">
        <span class="section-kicker">Teach, practise, repeat</span>
        <h2>Lesson plan</h2>
      </div>
      <div class="plan-grid">
        ${renderChecklist(
          weekIndex,
          "saturday",
          "Saturday class",
          "60 minutes",
          week.saturday,
          "primary",
        )}
        ${renderChecklist(
          weekIndex,
          "midweek",
          "Midweek SI",
          "30–45 minutes",
          week.midweek,
          "secondary",
        )}
        ${renderChecklist(
          weekIndex,
          "homework",
          "Home practice",
          "Keep it light",
          week.homework,
          "accent",
        )}
      </div>
      <div class="teacher-note">
        <span aria-hidden="true">→</span>
        <p><strong>Teacher note</strong> Move from word → phrase → conversation. Let
        younger learners answer briefly; push older learners toward full sentences
        and short role plays.</p>
      </div>
    </section>
  `;
}

function renderChecklist(weekIndex, type, title, duration, items, tone) {
  return `
    <div class="plan-card ${tone}">
      <div class="plan-card-heading">
        <div>
          <span>${duration}</span>
          <h3>${title}</h3>
        </div>
        <span class="plan-count">${items.length}</span>
      </div>
      <div class="checklist">
        ${items
          .map((item, itemIndex) => {
            const key = checkKey(weekIndex, type, itemIndex);
            return `
              <label class="check-item">
                <input type="checkbox" data-check="${key}" ${state.checks[key] ? "checked" : ""} />
                <span class="custom-check" aria-hidden="true">✓</span>
                <span>${escapeHtml(item)}</span>
              </label>
            `;
          })
          .join("")}
      </div>
    </div>
  `;
}

function renderTeacherReflection(weekIndex) {
  const key = fieldKey(weekIndex, "reflection", 0);
  return `
    <section class="section reflection">
      <div>
        <span class="section-kicker">After the lesson</span>
        <h2>Teacher reflection</h2>
        <p>Capture dialect choices, pronunciation reminders, and what to revisit.</p>
      </div>
      <label>
        <span class="sr-only">Teacher reflection for this week</span>
        <textarea
          rows="5"
          data-field="${key}"
          placeholder="What worked well? Which words need another round?"
        >${escapeHtml(getValue(key))}</textarea>
      </label>
    </section>
  `;
}

function weekCompletionUnits(weekIndex) {
  const week = weeks[weekIndex];
  const valueUnits = [
    ...week.vocabulary.map((item, itemIndex) => ({
      key: fieldKey(weekIndex, "vocab", itemIndex),
      fallback: item.translation,
    })),
    ...week.targets.map((_, itemIndex) => ({
      key: fieldKey(weekIndex, "target", itemIndex),
      fallback: "",
    })),
    ...week.dialogue.map((_, itemIndex) => ({
      key: fieldKey(weekIndex, "dialogue", itemIndex),
      fallback: "",
    })),
  ];
  const checkUnits = ["saturday", "midweek", "homework"].flatMap((type) =>
    week[type].map((_, itemIndex) => checkKey(weekIndex, type, itemIndex)),
  );
  const completedValues = valueUnits.filter(({ key, fallback }) =>
    getValue(key, fallback).trim(),
  ).length;
  const completedChecks = checkUnits.filter((key) => state.checks[key]).length;
  return {
    complete: completedValues + completedChecks,
    total: valueUnits.length + checkUnits.length,
  };
}

function getWeekProgress(weekIndex) {
  const { complete, total } = weekCompletionUnits(weekIndex);
  return Math.round((complete / total) * 100);
}

function updateProgress() {
  const totals = weeks.reduce(
    (sum, _, index) => {
      const units = weekCompletionUnits(index);
      return {
        complete: sum.complete + units.complete,
        total: sum.total + units.total,
      };
    },
    { complete: 0, total: 0 },
  );
  const percent = Math.round((totals.complete / totals.total) * 100);
  elements.coursePercent.textContent = `${percent}%`;
  elements.courseProgressBar.setAttribute("aria-valuenow", String(percent));
  elements.courseProgressBar.querySelector("span").style.width = `${percent}%`;
  elements.courseProgressCopy.textContent =
    percent === 100
      ? "The full course is ready."
      : `${totals.complete} of ${totals.total} guide steps completed`;
  const weekPercent = document.querySelector("#week-percent");
  if (weekPercent) weekPercent.textContent = `${getWeekProgress(state.currentWeek)}%`;
}

function showToast(message) {
  elements.toast.textContent = message;
  elements.toast.classList.add("show");
  window.clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => elements.toast.classList.remove("show"), 2600);
}

function handleInput(event) {
  const field = event.target.closest("[data-field]");
  if (field) {
    state.values[field.dataset.field] = field.value;
    persist();
    updateProgress();
    renderNav();
    return;
  }
  const check = event.target.closest("[data-check]");
  if (check) {
    state.checks[check.dataset.check] = check.checked;
    persist();
    updateProgress();
    renderNav();
  }
}

function handleContentClick(event) {
  const action = event.target.closest("[data-action]")?.dataset.action;
  if (action === "previous-week" && state.currentWeek > 0) {
    renderWeek(state.currentWeek - 1, true);
  }
  if (action === "next-week" && state.currentWeek < weeks.length - 1) {
    renderWeek(state.currentWeek + 1, true);
  }
}

function searchGuide(query) {
  const normalized = query.trim().toLowerCase();
  if (normalized.length < 2) {
    elements.searchResults.hidden = true;
    return;
  }
  const matches = weeks.flatMap((week, weekIndex) => {
    const collections = [
      { label: "Topic", values: [week.title] },
      { label: "Objective", values: week.objectives },
      { label: "Vocabulary", values: week.vocabulary.map((item) => item.english) },
      { label: "Sentence", values: week.targets },
      {
        label: "Dialogue",
        values: week.dialogue.flatMap((item) => [item.speakerA, item.speakerB]),
      },
    ];
    return collections.flatMap(({ label, values }) =>
      values
        .filter((value) => value.toLowerCase().includes(normalized))
        .slice(0, 3)
        .map((value) => ({ weekIndex, week, label, value })),
    );
  });
  elements.searchResults.innerHTML = matches.length
    ? `
      <div class="search-result-heading">
        <strong>${matches.length} result${matches.length === 1 ? "" : "s"}</strong>
        <button type="button" data-clear-search>Clear</button>
      </div>
      ${matches
        .slice(0, 18)
        .map(
          (match) => `
            <button type="button" class="search-result" data-result-week="${match.weekIndex}">
              <span>Week ${match.weekIndex + 1} · ${match.label}</span>
              <strong>${highlightMatch(match.value, normalized)}</strong>
            </button>
          `,
        )
        .join("")}
    `
    : `<div class="empty-search"><strong>No matches yet</strong><span>Try a shorter word or another spelling.</span></div>`;
  elements.searchResults.hidden = false;
}

function highlightMatch(value, query) {
  const safeValue = escapeHtml(value);
  const index = value.toLowerCase().indexOf(query);
  if (index < 0) return safeValue;
  const before = escapeHtml(value.slice(0, index));
  const match = escapeHtml(value.slice(index, index + query.length));
  const after = escapeHtml(value.slice(index + query.length));
  return `${before}<mark>${match}</mark>${after}`;
}

function clearSearch() {
  elements.search.value = "";
  elements.searchResults.hidden = true;
}

function openModal(content) {
  elements.modalBody.innerHTML = content;
  elements.modalBackdrop.hidden = false;
  document.body.classList.add("modal-open");
  document.querySelector("#modal-close").focus();
}

function closeModal() {
  elements.modalBackdrop.hidden = true;
  document.body.classList.remove("modal-open");
}

function showAssessments() {
  openModal(`
    <div class="modal-header">
      <span class="section-kicker">Measure speaking confidence</span>
      <h2 id="modal-title">Simple assessment plan</h2>
      <p>Use these as friendly speaking checks, not written tests.</p>
    </div>
    <div class="assessment-list">
      ${assessments
        .map(
          (assessment, assessmentIndex) => `
            <section class="assessment-card">
              <div><span>After week ${assessment.afterWeek}</span><h3>${assessment.title}</h3></div>
              <div class="checklist">
                ${assessment.items
                  .map((item, itemIndex) => {
                    const key = `assessment-${assessmentIndex}-${itemIndex}`;
                    return `
                      <label class="check-item">
                        <input type="checkbox" data-check="${key}" ${state.checks[key] ? "checked" : ""} />
                        <span class="custom-check" aria-hidden="true">✓</span>
                        <span>${escapeHtml(item)}</span>
                      </label>
                    `;
                  })
                  .join("")}
              </div>
            </section>
          `,
        )
        .join("")}
    </div>
  `);
}

function showTranslatorNotes() {
  const fields = [
    "Dialect choice",
    "Greeting variants",
    "Family terms",
    "Food words",
    "Place names",
    "Pronunciation reminders",
  ];
  openModal(`
    <div class="modal-header">
      <span class="section-kicker">Keep language decisions consistent</span>
      <h2 id="modal-title">Translator notes</h2>
      <p>Record dialect choices, alternate spellings, and pronunciation reminders.</p>
    </div>
    <div class="translator-note-list">
      ${fields
        .map(
          (label, index) => `
            <label>
              <span>${label}</span>
              <textarea rows="3" data-translator-note="${index}" placeholder="Add notes">${escapeHtml(
                state.translatorNotes[index] || "",
              )}</textarea>
            </label>
          `,
        )
        .join("")}
    </div>
  `);
}

function showBackup() {
  openModal(`
    <div class="modal-header">
      <span class="section-kicker">Keep your work portable</span>
      <h2 id="modal-title">Back up or restore</h2>
      <p>Your entries save in this browser. Download a backup before changing devices or clearing browser data.</p>
    </div>
    <div class="backup-grid">
      <button class="backup-option" type="button" data-backup-action="download">
        <span class="backup-symbol">↓</span>
        <strong>Download backup</strong>
        <span>Save all translations, notes, and checklist progress as a JSON file.</span>
      </button>
      <button class="backup-option" type="button" data-backup-action="restore">
        <span class="backup-symbol">↑</span>
        <strong>Restore backup</strong>
        <span>Continue from a previously downloaded Kalenjin guide backup.</span>
      </button>
    </div>
  `);
}

function downloadBackup() {
  const payload = {
    app: "Kalenjin Learning Guide",
    version: 1,
    exportedAt: new Date().toISOString(),
    data: state,
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `kalenjin-guide-backup-${new Date().toISOString().slice(0, 10)}.json`;
  link.click();
  URL.revokeObjectURL(url);
  closeModal();
  showToast("Backup downloaded");
}

async function restoreBackup(file) {
  try {
    const payload = JSON.parse(await file.text());
    if (payload.app !== "Kalenjin Learning Guide" || !payload.data) {
      throw new Error("Unrecognized backup");
    }
    Object.assign(state, defaultState, payload.data);
    state.values ||= {};
    state.checks ||= {};
    state.translatorNotes ||= {};
    persist();
    renderWeek(Number(state.currentWeek) || 0);
    closeModal();
    showToast("Backup restored");
  } catch {
    showToast("That file is not a valid guide backup");
  } finally {
    elements.restoreInput.value = "";
  }
}

function toggleMobileNav() {
  const open = elements.sidebar.classList.toggle("open");
  elements.menuToggle.setAttribute("aria-expanded", String(open));
}

function closeMobileNav() {
  elements.sidebar.classList.remove("open");
  elements.menuToggle.setAttribute("aria-expanded", "false");
}

elements.nav.addEventListener("click", (event) => {
  const button = event.target.closest("[data-week]");
  if (button) renderWeek(Number(button.dataset.week), true);
});
elements.content.addEventListener("input", handleInput);
elements.content.addEventListener("change", handleInput);
elements.content.addEventListener("click", handleContentClick);
elements.search.addEventListener("input", (event) => searchGuide(event.target.value));
elements.searchResults.addEventListener("click", (event) => {
  const result = event.target.closest("[data-result-week]");
  if (result) {
    renderWeek(Number(result.dataset.resultWeek), true);
    clearSearch();
  }
  if (event.target.closest("[data-clear-search]")) clearSearch();
});
elements.menuToggle.addEventListener("click", toggleMobileNav);
document.querySelector("#show-assessments").addEventListener("click", showAssessments);
document
  .querySelector("#show-translator-notes")
  .addEventListener("click", showTranslatorNotes);
document.querySelector("#backup-button").addEventListener("click", showBackup);
document.querySelector("#print-button").addEventListener("click", () => window.print());
document.querySelector("#modal-close").addEventListener("click", closeModal);
elements.modalBackdrop.addEventListener("click", (event) => {
  if (event.target === elements.modalBackdrop) closeModal();
});
elements.modalBody.addEventListener("change", handleInput);
elements.modalBody.addEventListener("input", (event) => {
  handleInput(event);
  const note = event.target.closest("[data-translator-note]");
  if (note) {
    state.translatorNotes[note.dataset.translatorNote] = note.value;
    persist();
  }
});
elements.modalBody.addEventListener("click", (event) => {
  const action = event.target.closest("[data-backup-action]")?.dataset.backupAction;
  if (action === "download") downloadBackup();
  if (action === "restore") elements.restoreInput.click();
});
elements.restoreInput.addEventListener("change", (event) => {
  const [file] = event.target.files;
  if (file) restoreBackup(file);
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    if (!elements.modalBackdrop.hidden) closeModal();
    else {
      clearSearch();
      closeMobileNav();
    }
  }
});

renderWeek(Math.min(Math.max(Number(state.currentWeek) || 0, 0), weeks.length - 1));
