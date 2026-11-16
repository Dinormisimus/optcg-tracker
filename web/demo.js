const API_BASE = "http://127.0.0.1:8000";
const TOKEN_KEY = "optcg-demo-tokens";

function showNotice(message, success = false) {
  const notice = document.querySelector("#notice");
  if (!notice) return;
  notice.textContent = message;
  notice.classList.toggle("success", success);
}

function getTokens() {
  try {
    return JSON.parse(localStorage.getItem(TOKEN_KEY) || "null");
  } catch {
    localStorage.removeItem(TOKEN_KEY);
    return null;
  }
}

async function api(path, options = {}) {
  const tokens = getTokens();
  const headers = new Headers(options.headers || {});
  headers.set("Content-Type", "application/json");
  if (tokens?.access_token) headers.set("Authorization", `Bearer ${tokens.access_token}`);

  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  } catch (error) {
    throw new Error("API nije dostupan. Provjeri je li backend pokrenut na portu 8000.");
  }
  if (response.status === 204) return null;

  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = body?.detail;
    const message = typeof detail === "string"
      ? detail
      : detail?.message || body?.message || `Greška API-ja (${response.status})`;
    throw new Error(message);
  }
  return body;
}

async function getAll(path) {
  const all = [];
  for (let offset = 0; ; offset += 100) {
    const page = await api(`${path}${path.includes("?") ? "&" : "?"}limit=100&offset=${offset}`);
    all.push(...page);
    if (page.length < 100) return all;
  }
}

function setOptions(select, items, labelFor, placeholder) {
  select.replaceChildren(new Option(placeholder, ""));
  for (const item of items) select.add(new Option(labelFor(item), item.id));
}

async function currentUser() {
  if (!getTokens()?.access_token) {
    window.location.href = "login.html";
    return null;
  }
  try {
    const user = await api("/auth/me");
    const userLabel = document.querySelector("#user-label");
    if (userLabel) userLabel.textContent = `${user.username} · ${user.role}`;
    return user;
  } catch {
    localStorage.removeItem(TOKEN_KEY);
    window.location.href = "login.html";
    return null;
  }
}

function logout() {
  localStorage.removeItem(TOKEN_KEY);
  window.location.href = "login.html";
}

function addItem(container, title, details, badge) {
  const article = document.createElement("article");
  article.className = "item";
  const heading = document.createElement("div");
  heading.className = "item-title";
  const name = document.createElement("strong");
  name.textContent = title;
  heading.append(name);
  if (badge) {
    const tag = document.createElement("span");
    tag.className = "badge";
    tag.textContent = badge;
    heading.append(tag);
  }
  const description = document.createElement("p");
  description.className = "muted";
  description.textContent = details;
  article.append(heading, description);
  container.append(article);
}

function addMatchItem(container, match, details) {
  addItem(container, `Meč #${match.id}`, details);
  const article = container.lastElementChild;
  const button = document.createElement("button");
  button.type = "button";
  button.className = "delete-button";
  button.dataset.deleteMatch = match.id;
  button.textContent = "Obriši meč";
  article.append(button);
}

function formatPercent(value) {
  return value == null ? "—" : `${value.toFixed(2)}%`;
}

function renderStatsTable(containerId, rows, columns, emptyMessage) {
  const container = document.querySelector(`#${containerId}`);
  container.replaceChildren();
  if (!rows.length) {
    const empty = document.createElement("p");
    empty.className = "muted";
    empty.textContent = emptyMessage;
    container.append(empty);
    return;
  }

  const wrapper = document.createElement("div");
  wrapper.className = "table-wrap";
  const table = document.createElement("table");
  const head = document.createElement("thead");
  const headerRow = document.createElement("tr");
  for (const column of columns) {
    const cell = document.createElement("th");
    cell.scope = "col";
    cell.textContent = column.label;
    headerRow.append(cell);
  }
  head.append(headerRow);

  const body = document.createElement("tbody");
  for (const row of rows) {
    const tableRow = document.createElement("tr");
    for (const column of columns) {
      const cell = document.createElement("td");
      const value = column.value(row);
      cell.textContent = column.format ? column.format(value) : String(value ?? "—");
      if (column.numeric) cell.className = "numeric";
      tableRow.append(cell);
    }
    body.append(tableRow);
  }

  table.append(head, body);
  wrapper.append(table);
  container.append(wrapper);
}

function leaderLabel(name, code) {
  return `${name} (${code})`;
}

async function initLogin() {
  if (getTokens()?.access_token) {
    try {
      await api("/auth/me");
      window.location.href = "matches.html";
      return;
    } catch {
      localStorage.removeItem(TOKEN_KEY);
    }
  }
  document.querySelector("#login-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const button = form.querySelector("button");
    button.disabled = true;
    showNotice("");
    try {
      const tokens = await api("/auth/login", {
        method: "POST",
        body: JSON.stringify({
          username: form.elements.username.value.trim(),
          password: form.elements.password.value,
        }),
      });
      localStorage.setItem(TOKEN_KEY, JSON.stringify(tokens));
      window.location.href = "matches.html";
    } catch (error) {
      showNotice(error.message);
    } finally {
      button.disabled = false;
    }
  });
}

async function initRegister() {
  document.querySelector("#register-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const button = form.querySelector("button");
    const password = form.elements.password.value;
    if (password !== form.elements.password_confirmation.value) {
      showNotice("Lozinke se ne podudaraju.");
      return;
    }
    if (new TextEncoder().encode(password).length > 72) {
      showNotice("Lozinka ne smije biti duža od 72 bajta.");
      return;
    }

    button.disabled = true;
    showNotice("");
    try {
      await api("/auth/register", {
        method: "POST",
        body: JSON.stringify({
          username: form.elements.username.value.trim(),
          email: form.elements.email.value.trim(),
          password,
        }),
      });
      form.reset();
      showNotice("Registracija je uspjela. Sada se možeš prijaviti.", true);
    } catch (error) {
      showNotice(error.message);
    } finally {
      button.disabled = false;
    }
  });
}

async function initTournaments() {
  const user = await currentUser();
  if (!user) return;
  const form = document.querySelector("#tournament-form");
  const list = document.querySelector("#tournament-list");
  if (!["admin", "super_admin"].includes(user.role)) {
    form.hidden = true;
    document.querySelector("#create-hint").textContent = "Za izradu turnira prijavi se kao organizer ili superadmin.";
  }

  async function load() {
    list.replaceChildren();
    const tournaments = await getAll("/tournaments");
    if (!tournaments.length) {
      addItem(list, "Još nema turnira", "Kreiraj prvi turnir putem obrasca.");
      return;
    }
    for (const tournament of tournaments) {
      addItem(list, tournament.name, `Organizator ID: ${tournament.organizer_id}`, tournament.format);
    }
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = form.querySelector("button");
    button.disabled = true;
    showNotice("");
    try {
      await api("/tournaments", {
        method: "POST",
        body: JSON.stringify({
          name: form.elements.name.value.trim(),
          format: form.elements.format.value,
        }),
      });
      form.reset();
      showNotice("Turnir je uspješno kreiran.", true);
      await load();
    } catch (error) {
      showNotice(error.message);
    } finally {
      button.disabled = false;
    }
  });

  try {
    await load();
  } catch (error) {
    showNotice(error.message);
  }
}

async function initMatches() {
  const user = await currentUser();
  if (!user) return;
  const form = document.querySelector("#match-form");
  const list = document.querySelector("#match-list");
  try {
    const [leaders, tournaments] = await Promise.all([
      getAll("/leaders"),
      getAll("/tournaments"),
    ]);
    setOptions(form.elements.my_leader_id, leaders, (item) => `${item.name} (${item.code})`, "Odaberi svog Leadera");
    setOptions(form.elements.opponent_leader_id, leaders, (item) => `${item.name} (${item.code})`, "Odaberi Leader protivnika");
    form.elements.tournament_id.replaceChildren(new Option("Bez turnira", ""));
    for (const tournament of tournaments) {
      form.elements.tournament_id.add(new Option(tournament.name, tournament.id));
    }
  } catch (error) {
    showNotice(error.message);
    form.querySelector("button").disabled = true;
    return;
  }

  async function load() {
    list.replaceChildren();
    const matches = await getAll("/matches");
    if (!matches.length) {
      addItem(list, "Još nema mečeva", "Zabilježeni mečevi pojavit će se ovdje.");
      return;
    }
    for (const match of matches) {
      const outcome = { WIN: "Pobjeda", LOSS: "Poraz", DRAW: "Neriješeno" }[match.result];
      const details = [
        `Protiv: ${match.opponent_name}`,
        `Ishod: ${outcome}`,
        `Kocka: ${match.dice_result === "WIN" ? "pobjeda" : "poraz"}`,
        `Igra: ${match.turn_order === "FIRST" ? "prvi" : "drugi"}`,
        match.round_number ? `Runda ${match.round_number}` : null,
        match.tournament_id ? `Turnir #${match.tournament_id}` : null,
      ].filter(Boolean).join(" · ");
      addMatchItem(list, match, details);
    }
  }

  list.addEventListener("click", async (event) => {
    if (!(event.target instanceof Element)) return;
    const button = event.target.closest("button[data-delete-match]");
    if (!button || !window.confirm(`Želiš li obrisati meč #${button.dataset.deleteMatch}?`)) {
      return;
    }

    button.disabled = true;
    showNotice("");
    try {
      await api(`/matches/${button.dataset.deleteMatch}`, { method: "DELETE" });
      showNotice("Meč je obrisan.", true);
      await load();
    } catch (error) {
      showNotice(error.message);
      button.disabled = false;
    }
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = form.querySelector("button");
    button.disabled = true;
    showNotice("");
    const data = new FormData(form);
    const tournamentId = data.get("tournament_id");
    const roundNumber = data.get("round_number");
    const payload = {
      my_leader_id: Number(data.get("my_leader_id")),
      opponent_leader_id: Number(data.get("opponent_leader_id")),
      opponent_name: data.get("opponent_name").trim(),
      result: data.get("result"),
      dice_result: data.get("dice_result"),
      turn_order: data.get("turn_order"),
      round_number: roundNumber ? Number(roundNumber) : null,
      tournament_id: tournamentId ? Number(tournamentId) : null,
    };
    try {
      await api("/matches", { method: "POST", body: JSON.stringify(payload) });
      form.reset();
      showNotice("Meč je uspješno spremljen.", true);
      await load();
    } catch (error) {
      showNotice(error.message);
    } finally {
      button.disabled = false;
    }
  });

  try {
    await load();
  } catch (error) {
    showNotice(error.message);
  }
}

async function initStats() {
  const user = await currentUser();
  if (!user) return;

  const summary = document.querySelector("#summary");
  try {
    const [overall, myLeaders, opponents, opponentLeaders, matchups] = await Promise.all([
      api("/stats/overall"),
      getAll("/stats/leaders"),
      getAll("/stats/opponents"),
      getAll("/stats/opponent-leaders"),
      getAll("/stats/matchups"),
    ]);

    const summaryItems = [
      ["Mečevi", overall.total_matches],
      ["Pobjede", overall.wins],
      ["Porazi", overall.losses],
      ["Neriješeno", overall.draws],
      ["Odlučeni mečevi", overall.decided_matches],
      ["Postotak pobjeda", formatPercent(overall.win_rate)],
    ];
    summary.replaceChildren();
    for (const [label, value] of summaryItems) {
      const card = document.createElement("article");
      card.className = "stat-card";
      const caption = document.createElement("span");
      caption.textContent = label;
      const number = document.createElement("strong");
      number.textContent = String(value ?? "—");
      card.append(caption, number);
      summary.append(card);
    }

    const resultColumns = [
      { key: "total_matches", label: "Mečevi", numeric: true },
      { key: "wins", label: "Pobjede", numeric: true },
      { key: "losses", label: "Porazi", numeric: true },
      { key: "draws", label: "Neriješeno", numeric: true },
      { key: "win_rate", label: "Pobjede %", numeric: true, format: formatPercent },
    ];
    const makeColumns = (identity) => [
      ...identity,
      ...resultColumns.map((column) => ({
        label: column.label,
        numeric: column.numeric,
        value: (row) => row[column.key],
        format: column.format,
      })),
    ];
    const textColumn = (key, label) => ({ label, value: (row) => row[key] });

    renderStatsTable(
      "by-my-leader",
      myLeaders,
      makeColumns([
        {
          label: "Moj Leader",
          value: (row) => leaderLabel(row.leader_name, row.leader_code),
        },
      ]),
      "Još nema mečeva s tvojim Leaderima.",
    );
    renderStatsTable(
      "by-opponent",
      opponents,
      makeColumns([textColumn("opponent_name", "Protivnik")]),
      "Još nema zabilježenih protivnika.",
    );
    renderStatsTable(
      "by-opponent-leader",
      opponentLeaders,
      makeColumns([
        {
          label: "Leader protivnika",
          value: (row) => leaderLabel(row.opponent_leader_name, row.opponent_leader_code),
        },
      ]),
      "Još nema mečeva protiv Leader karata.",
    );
    renderStatsTable(
      "by-matchup",
      matchups,
      makeColumns([
        textColumn("opponent_name", "Protivnik"),
        {
          label: "Leader protivnika",
          value: (row) => leaderLabel(row.opponent_leader_name, row.opponent_leader_code),
        },
      ]),
      "Još nema zabilježenih kombinacija protivnika i Leadera.",
    );
  } catch (error) {
    showNotice(error.message);
    for (const id of ["by-my-leader", "by-opponent", "by-opponent-leader", "by-matchup"]) {
      document.querySelector(`#${id}`).replaceChildren();
    }
    summary.replaceChildren();
  }
}

document.querySelectorAll("[data-logout]").forEach((button) => button.addEventListener("click", logout));
if (document.querySelector("#login-form")) initLogin();
if (document.querySelector("#register-form")) initRegister();
if (document.querySelector("#tournament-form")) initTournaments();
if (document.querySelector("#match-form")) initMatches();
if (document.querySelector("#summary")) initStats();
