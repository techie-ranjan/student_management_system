(() => {
  const { subjects, labels, grades } = window.SMS;
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];

  const state = { students: [], editingId: null, deleteId: null };

  // ---------------------------------------------------------------- helpers
  const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const gradeClass = (g) => "g-" + g.replace("+", "plus");
  const fmt = (n) => (Number.isInteger(n) ? n : Number(n).toFixed(1));

  async function api(path, options = {}) {
    const res = await fetch(path, {
      headers: { "Content-Type": "application/json" },
      ...options,
      body: options.body ? JSON.stringify(options.body) : undefined,
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const err = new Error(data.error || "Something went wrong.");
      err.fields = data.fields || {};
      throw err;
    }
    return data;
  }

  let toastTimer;
  function toast(msg, isError = false) {
    const t = $("#toast");
    t.textContent = msg;
    t.className = "toast show" + (isError ? " error" : "");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => (t.className = "toast"), 2800);
  }

  const debounce = (fn, ms = 250) => {
    let id;
    return (...a) => { clearTimeout(id); id = setTimeout(() => fn(...a), ms); };
  };

  // ---------------------------------------------------------------- loading
  function query() {
    const [sort, order] = $("#sortBy").value.split(":");
    const p = new URLSearchParams({
      q: $("#search").value, grade: $("#gradeFilter").value,
      status: $("#statusFilter").value, sort, order,
    });
    return p.toString();
  }

  async function load() {
    try {
      const [students, stats] = await Promise.all([api("/api/students?" + query()), api("/api/stats")]);
      state.students = students;
      renderTable();
      renderStats(stats);
    } catch (e) {
      toast(e.message, true);
    }
  }

  // ----------------------------------------------------------------- render
  function renderTable() {
    const rows = $("#rows"), empty = $("#empty");
    const filtering = $("#search").value || $("#gradeFilter").value || $("#statusFilter").value;

    rows.innerHTML = state.students.map((s) => `
      <tr data-id="${s.id}">
        <td class="rank c-rank ${s.rank <= 3 ? "top" : ""}">${s.rank}</td>
        <td class="who c-who"><strong>${esc(s.name)}</strong><span>${esc(s.roll_no)} · ${esc(s.course)}</span></td>
        <td class="c-sem">Sem ${s.semester}</td>
        <td class="marks c-marks">${fmt(s.percentage)}%</td>
        <td class="c-grade"><span class="badge ${gradeClass(s.grade)}">${s.grade}</span></td>
        <td class="c-res ${s.passed ? "res-pass" : "res-fail"}">${s.passed ? "Pass" : "Fail"}</td>
        <td class="c-act"><div class="actions">
          <button class="btn small" data-act="view">Details</button>
          <button class="btn small" data-act="edit">Edit</button>
          <button class="btn small" data-act="delete">Delete</button>
        </div></td>
      </tr>`).join("");

    $("#shownCount").textContent = `${state.students.length} ${state.students.length === 1 ? "student" : "students"} shown`;
    $(".table-wrap").hidden = state.students.length === 0;
    empty.hidden = state.students.length > 0;
    if (!state.students.length) {
      empty.innerHTML = filtering
        ? `<h3>No students match these filters</h3><p>Try a different name, grade or result.</p>`
        : `<h3>No students yet</h3><p>Add your first student, or load sample data to explore the app.</p>
           <button class="btn primary" data-empty="add">Add student</button>
           <button class="btn" data-empty="seed">Load sample data</button>`;
    }
  }

  function barRow(label, value, max, cls = "") {
    const pct = max ? Math.min(100, (value / max) * 100) : 0;
    return `<div class="bar-row"><span class="lbl">${esc(label)}</span>
      <div class="track"><div class="fill ${cls}" style="width:${pct}%"></div></div>
      <span class="val">${fmt(value)}</span></div>`;
  }

  function renderStats(st) {
    $("#sCount").textContent = st.count;
    $("#sAvg").textContent = fmt(st.average) + "%";
    $("#sPass").textContent = fmt(st.pass_rate) + "%";
    $("#sHigh").textContent = st.highest ? fmt(st.highest.percentage) + "%" : "–";
    $("#sHighName").textContent = st.highest ? "Highest · " + st.highest.name : "Highest score";
    $("#sLow").textContent = st.lowest ? fmt(st.lowest.percentage) + "%" : "–";
    $("#sLowName").textContent = st.lowest ? "Lowest · " + st.lowest.name : "Lowest score";

    $("#leaders").innerHTML = st.toppers.length
      ? st.toppers.map((t) => `<li><span class="pos">${t.rank}</span>
          <span class="nm">${esc(t.name)}</span><span class="pc">${fmt(t.percentage)}%</span></li>`).join("")
      : `<li class="muted">Rankings appear once you add students.</li>`;

    const maxG = Math.max(1, ...Object.values(st.grade_distribution));
    $("#gradeBars").innerHTML = grades.map((g) =>
      barRow("Grade " + g, st.grade_distribution[g], maxG, g === "F" ? "bad" : g === "A+" || g === "A" ? "" : "dim")
    ).join("");

    $("#subjectBars").innerHTML = subjects.map((s) =>
      barRow(labels[s], st.subject_averages[s], 100, st.subject_averages[s] < 40 ? "bad" : "")
    ).join("");
  }

  // ----------------------------------------------------------------- dialogs
  const formDlg = $("#formDialog"), form = $("#studentForm");

  function clearErrors() {
    $$("[data-err]", form).forEach((e) => (e.textContent = ""));
    $$(".field", form).forEach((f) => f.classList.remove("invalid"));
  }
  function showErrors(fields) {
    Object.entries(fields).forEach(([name, msg]) => {
      const el = $(`[data-err="${name}"]`, form);
      if (el) { el.textContent = msg; el.closest(".field").classList.add("invalid"); }
    });
    const first = $(".field.invalid input, .field.invalid select", form);
    if (first) first.focus();
  }

  function livePreview() {
    const vals = subjects.map((s) => parseFloat(form.elements[s].value) || 0);
    const pct = vals.reduce((a, b) => a + b, 0) / subjects.length;
    const g = pct >= 90 ? "A+" : pct >= 80 ? "A" : pct >= 70 ? "B+" : pct >= 60 ? "B" : pct >= 50 ? "C" : pct >= 40 ? "D" : "F";
    $("#livePreview").innerHTML = `Average <b>${fmt(Math.round(pct * 100) / 100)}%</b> · Grade <b>${g}</b>`;
  }

  function openForm(student = null) {
    state.editingId = student ? student.id : null;
    form.reset();
    clearErrors();
    $("#formTitle").textContent = student ? "Edit student" : "Add student";
    $("#saveBtn").textContent = student ? "Save changes" : "Save student";
    if (student) {
      ["roll_no", "name", "email", "course", "semester", ...subjects].forEach((k) => (form.elements[k].value = student[k]));
    }
    livePreview();
    formDlg.showModal();
    form.elements.roll_no.focus();
  }

  form.addEventListener("input", livePreview);
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearErrors();
    const body = Object.fromEntries(new FormData(form).entries());
    const btn = $("#saveBtn");
    btn.disabled = true;
    try {
      const editing = state.editingId !== null;
      await api(editing ? `/api/students/${state.editingId}` : "/api/students", {
        method: editing ? "PUT" : "POST", body,
      });
      formDlg.close();
      toast(editing ? "Changes saved" : "Student added");
      load();
    } catch (err) {
      showErrors(err.fields);
      if (!Object.keys(err.fields).length) toast(err.message, true);
    } finally {
      btn.disabled = false;
    }
  });

  function openView(s) {
    const best = [...subjects].sort((a, b) => s[b] - s[a])[0];
    $("#viewBody").innerHTML = `
      <div class="detail">
        <div class="detail-top">
          <div><h2>${esc(s.name)}</h2>
            <p>${esc(s.roll_no)} · ${esc(s.course)} · Semester ${s.semester}${s.email ? " · " + esc(s.email) : ""}</p></div>
          <button class="icon-btn" data-close aria-label="Close">&times;</button>
        </div>
        <div class="detail-stats">
          <div><b>${s.rank}</b><span>Class rank</span></div>
          <div><b>${fmt(s.percentage)}%</b><span>Average</span></div>
          <div><b>${s.grade}</b><span>Grade</span></div>
          <div><b class="${s.passed ? "res-pass" : "res-fail"}">${s.passed ? "Pass" : "Fail"}</b><span>Result</span></div>
        </div>
        <div class="bars">${subjects.map((k) => barRow(labels[k], s[k], 100, s[k] < 40 ? "bad" : "")).join("")}</div>
        <p class="muted" style="margin-top:14px">Total ${fmt(s.total)} out of ${subjects.length * 100}. Strongest subject: ${esc(labels[best])}.</p>
      </div>`;
    $("#viewDialog").showModal();
  }

  function askDelete(s) {
    state.deleteId = s.id;
    $("#confirmText").textContent = `${s.name} (${s.roll_no}) and their marks will be removed. This can't be undone.`;
    $("#confirmDialog").showModal();
  }

  $("#confirmDelete").addEventListener("click", async () => {
    try {
      await api(`/api/students/${state.deleteId}`, { method: "DELETE" });
      $("#confirmDialog").close();
      toast("Student deleted");
      load();
    } catch (e) { toast(e.message, true); }
  });

  // ------------------------------------------------------------------ events
  document.addEventListener("click", async (e) => {
    if (e.target.closest("[data-close]")) { e.target.closest("dialog").close(); return; }
    if (e.target.tagName === "DIALOG") { e.target.close(); return; } // click on backdrop

    const empty = e.target.closest("[data-empty]");
    if (empty) {
      if (empty.dataset.empty === "add") openForm();
      else { const r = await api("/api/seed", { method: "POST" }); toast(`Loaded ${r.added} sample students`); load(); }
      return;
    }
    const btn = e.target.closest("[data-act]");
    if (!btn) return;
    const s = state.students.find((x) => x.id === Number(btn.closest("tr").dataset.id));
    if (!s) return;
    ({ view: openView, edit: openForm, delete: askDelete })[btn.dataset.act](s);
  });

  $("#addBtn").addEventListener("click", () => openForm());
  $("#search").addEventListener("input", debounce(load));
  ["gradeFilter", "statusFilter", "sortBy"].forEach((id) => $("#" + id).addEventListener("change", load));

  load();
})();
