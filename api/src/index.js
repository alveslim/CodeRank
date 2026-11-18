// CodeRank API — Cloudflare Worker.
// Autenticação e dados ficam no Supabase; a execução de código vai para o
// Worker "coderank-judge" (service binding JUDGE), que não tem acesso a segredos.

const MAX_SOURCE_BYTES = 50_000;
const USERNAME_RE = /^[A-Za-z0-9_]{3,20}$/;
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

class HttpError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

function cors(env) {
  return {
    "Access-Control-Allow-Origin": env.ALLOWED_ORIGIN || "*",
    "Access-Control-Allow-Methods": "GET, POST, PATCH, OPTIONS",
    "Access-Control-Allow-Headers": "Authorization, Content-Type",
    "Access-Control-Max-Age": "86400",
  };
}

function json(env, body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store", ...cors(env) },
  });
}

// ---------- Supabase ----------

async function sb(env, path, { method = "GET", token, body, headers = {} } = {}) {
  const res = await fetch(`${env.SUPABASE_URL}${path}`, {
    method,
    headers: {
      apikey: env.SUPABASE_KEY,
      Authorization: `Bearer ${token || env.SUPABASE_KEY}`,
      "Content-Type": "application/json",
      ...headers,
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const text = await res.text();
  let data = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }
  }
  return { ok: res.ok, status: res.status, data };
}

function bearer(request) {
  const h = request.headers.get("Authorization") || "";
  const m = /^Bearer\s+(.+)$/i.exec(h);
  return m ? m[1].trim() : null;
}

async function requireUser(env, request) {
  const token = bearer(request);
  if (!token) throw new HttpError(401, "Faça login para continuar.");
  const r = await sb(env, "/auth/v1/user", { token });
  if (!r.ok || !r.data?.id) throw new HttpError(401, "Sessão expirada. Entre novamente.");
  return { id: r.data.id, email: r.data.email, token };
}

async function readJson(request, limit = 80_000) {
  const text = await request.text();
  if (text.length > limit) throw new HttpError(413, "Requisição grande demais.");
  try {
    const data = JSON.parse(text || "{}");
    if (data === null || typeof data !== "object" || Array.isArray(data)) throw new Error();
    return data;
  } catch {
    throw new HttpError(400, "JSON inválido.");
  }
}

function str(value, name, { min = 0, max = 200, required = false } = {}) {
  if (value === undefined || value === null || value === "") {
    if (required) throw new HttpError(400, `Informe ${name}.`);
    return "";
  }
  if (typeof value !== "string") throw new HttpError(400, `${name} inválido.`);
  const v = value.trim();
  if (v.length < min || v.length > max) {
    throw new HttpError(400, `${name} deve ter entre ${min} e ${max} caracteres.`);
  }
  return v;
}

async function limited(env, key) {
  if (!env.RATE) return;
  const { success } = await env.RATE.limit({ key });
  if (!success) throw new HttpError(429, "Muitas requisições. Aguarde um minuto.");
}

// ---------- Auth ----------

function sessionPayload(data) {
  return {
    access_token: data.access_token,
    refresh_token: data.refresh_token,
    expires_in: data.expires_in,
    user: { id: data.user?.id, email: data.user?.email },
  };
}

function authError(r, fallback) {
  const code = r.data?.error_code || r.data?.code;
  const msg = String(r.data?.msg || r.data?.error_description || r.data?.message || "");
  if (code === "invalid_credentials" || /invalid login/i.test(msg)) return new HttpError(401, "E-mail ou senha incorretos.");
  if (code === "email_not_confirmed") return new HttpError(403, "Confirme seu e-mail antes de entrar.");
  if (code === "user_already_exists" || code === "email_exists") return new HttpError(409, "Este e-mail já está cadastrado.");
  if (code === "weak_password") return new HttpError(400, "Senha fraca. Use pelo menos 8 caracteres.");
  if (code === "over_email_send_rate_limit" || r.status === 429) return new HttpError(429, "Muitas tentativas. Aguarde um pouco.");
  if (code === "refresh_token_not_found" || code === "refresh_token_already_used") return new HttpError(401, "Sessão expirada. Entre novamente.");
  return new HttpError(r.status >= 500 ? 502 : 400, fallback);
}

async function signup(env, request) {
  const b = await readJson(request);
  const email = str(b.email, "o e-mail", { required: true, max: 120 }).toLowerCase();
  const password = typeof b.password === "string" ? b.password : "";
  const username = str(b.username, "o nome de usuário", { required: true });
  const cidade = str(b.cidade, "a cidade", { max: 60 });
  if (!EMAIL_RE.test(email)) throw new HttpError(400, "E-mail inválido.");
  if (password.length < 8 || password.length > 72) throw new HttpError(400, "A senha deve ter de 8 a 72 caracteres.");
  if (!USERNAME_RE.test(username)) {
    throw new HttpError(400, "Usuário: 3 a 20 caracteres, só letras, números e _.");
  }
  const taken = await sb(env, `/rest/v1/profiles?select=id&username=ilike.${encodeURIComponent(username)}&limit=1`);
  if (taken.ok && taken.data?.length) throw new HttpError(409, "Este nome de usuário já está em uso.");

  const r = await sb(env, "/auth/v1/signup", {
    method: "POST",
    body: { email, password, data: { username, display_name: username, cidade } },
  });
  if (!r.ok) throw authError(r, "Não foi possível criar a conta.");
  return { ok: true, needs_confirmation: !r.data?.access_token };
}

async function login(env, request) {
  const b = await readJson(request);
  const email = str(b.email, "o e-mail", { required: true, max: 120 }).toLowerCase();
  const password = typeof b.password === "string" ? b.password : "";
  if (!password) throw new HttpError(400, "Informe a senha.");
  const r = await sb(env, "/auth/v1/token?grant_type=password", { method: "POST", body: { email, password } });
  if (!r.ok) throw authError(r, "Não foi possível entrar.");
  const profile = await getProfile(env, r.data.access_token, r.data.user.id);
  return { ...sessionPayload(r.data), profile };
}

async function refresh(env, request) {
  const b = await readJson(request);
  const rt = str(b.refresh_token, "o refresh_token", { required: true, max: 500 });
  const r = await sb(env, "/auth/v1/token?grant_type=refresh_token", { method: "POST", body: { refresh_token: rt } });
  if (!r.ok) throw authError(r, "Não foi possível renovar a sessão.");
  return sessionPayload(r.data);
}

async function logout(env, request) {
  const token = bearer(request);
  if (token) await sb(env, "/auth/v1/logout", { method: "POST", token });
  return { ok: true };
}

async function recover(env, request) {
  const b = await readJson(request);
  const email = str(b.email, "o e-mail", { required: true, max: 120 }).toLowerCase();
  if (!EMAIL_RE.test(email)) throw new HttpError(400, "E-mail inválido.");
  await sb(env, "/auth/v1/recover", { method: "POST", body: { email } });
  // Resposta neutra, para não revelar quais e-mails existem.
  return { ok: true };
}

async function getProfile(env, token, uid) {
  const r = await sb(env, `/rest/v1/profiles?select=id,username,display_name,bio,cidade,points&id=eq.${uid}`, { token });
  return r.ok && r.data?.[0] ? r.data[0] : null;
}

// ---------- Desafios ----------

async function solvedSet(env, user) {
  if (!user) return new Set();
  const r = await sb(env, "/rest/v1/submissions?select=problem_id&status=eq.accepted", { token: user.token });
  return new Set(r.ok ? r.data.map((s) => s.problem_id) : []);
}

async function optionalUser(env, request) {
  try {
    return await requireUser(env, request);
  } catch {
    return null;
  }
}

async function listProblems(env, request) {
  const user = await optionalUser(env, request);
  const [r, solved] = await Promise.all([
    sb(env, "/rest/v1/problems?select=id,slug,title,difficulty,points&order=points.asc,id.asc"),
    solvedSet(env, user),
  ]);
  if (!r.ok) throw new HttpError(502, "Não foi possível carregar os desafios.");
  return { problems: r.data.map((p) => ({ ...p, solved: solved.has(p.id) })) };
}

async function getProblem(env, request, slug) {
  const user = await optionalUser(env, request);
  const r = await sb(env, `/rest/v1/problems?select=*&slug=eq.${encodeURIComponent(slug)}`);
  if (!r.ok) throw new HttpError(502, "Não foi possível carregar o desafio.");
  const p = r.data?.[0];
  if (!p) throw new HttpError(404, "Desafio não encontrado.");
  const solved = await solvedSet(env, user);
  return { problem: { ...p, solved: solved.has(p.id) } };
}

async function judgeOne(env, source, input) {
  let res;
  try {
    res = await env.JUDGE.fetch("https://judge.internal/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ source, inputs: [input] }),
    });
  } catch {
    return { status: "timeout", stdout: "", stderr: "Tempo limite de execução excedido.", ms: 0 };
  }
  const text = await res.text();
  let data = null;
  try {
    data = JSON.parse(text);
  } catch {
    // Worker encerrado pelo limite de CPU da plataforma: tratamos como tempo excedido.
    return { status: "timeout", stdout: "", stderr: "Tempo limite de execução excedido.", ms: 0 };
  }
  if (!res.ok) throw new HttpError(res.status === 413 ? 413 : 400, data?.error || "Falha ao executar o código.");
  return data.results[0];
}

// Cada teste é uma chamada separada (cada uma com seu próprio orçamento de CPU).
async function judge(env, source, inputs) {
  return Promise.all(inputs.map((input) => judgeOne(env, source, input)));
}

function readSource(b) {
  if (b.language && String(b.language).toLowerCase() !== "python") {
    throw new HttpError(400, "No momento apenas Python é suportado.");
  }
  const source = typeof b.source === "string" ? b.source : "";
  if (!source.trim()) throw new HttpError(400, "Digite algum código antes de executar.");
  if (new TextEncoder().encode(source).length > MAX_SOURCE_BYTES) throw new HttpError(413, "O código ultrapassa o limite de 50 KB.");
  return source;
}

async function runCode(env, request, slug) {
  const user = await requireUser(env, request);
  await limited(env, `run:${user.id}`);
  const b = await readJson(request);
  const source = readSource(b);
  const p = await sb(env, `/rest/v1/problems?select=id,example_input&slug=eq.${encodeURIComponent(slug)}`);
  const problem = p.data?.[0];
  if (!problem) throw new HttpError(404, "Desafio não encontrado.");
  const stdin = typeof b.stdin === "string" ? b.stdin.slice(0, 10_000) : problem.example_input;
  const [r] = await judge(env, source, [stdin]);
  return { status: r.status, stdout: r.stdout, stderr: r.stderr, ms: r.ms };
}

const norm = (s) => String(s).replace(/\r\n/g, "\n").split("\n").map((l) => l.replace(/\s+$/, "")).join("\n").replace(/\n+$/, "");

async function submit(env, request, slug) {
  const user = await requireUser(env, request);
  await limited(env, `submit:${user.id}`);
  const b = await readJson(request);
  const source = readSource(b);

  const p = await sb(env, `/rest/v1/problems?select=id,points&slug=eq.${encodeURIComponent(slug)}`);
  const problem = p.data?.[0];
  if (!problem) throw new HttpError(404, "Desafio não encontrado.");

  const t = await sb(env, "/rest/v1/rpc/worker_get_tests", {
    method: "POST",
    body: { p_secret: env.WORKER_SECRET, p_problem: problem.id },
  });
  if (!t.ok || !Array.isArray(t.data) || !t.data.length) throw new HttpError(502, "Casos de teste indisponíveis.");
  const tests = t.data;

  const results = await judge(env, source, tests.map((x) => x.input));
  let passed = 0;
  let status = "accepted";
  const detail = results.map((r, i) => {
    const ok = r.status === "ok" && norm(r.stdout) === norm(tests[i].expected);
    if (ok) {
      passed += 1;
      return { index: i + 1, ok: true, status: "ok" };
    }
    const failed = r.status === "ok" ? "wrong_answer" : r.status === "compile_error" || r.status === "output_limit" ? "runtime_error" : r.status;
    if (status === "accepted") status = failed;
    return { index: i + 1, ok: false, status: failed, stderr: r.stderr || undefined };
  });
  // Revela entrada/esperado/obtido só do primeiro teste (é o exemplo público do enunciado).
  const first = detail[0];
  if (first && !first.ok && first.status === "wrong_answer") {
    first.input = tests[0].input;
    first.expected = tests[0].expected;
    first.got = results[0].stdout.slice(0, 2000);
  }

  const rec = await sb(env, "/rest/v1/rpc/worker_record_submission", {
    method: "POST",
    body: {
      p_secret: env.WORKER_SECRET,
      p_user: user.id,
      p_problem: problem.id,
      p_language: "python",
      p_source: source,
      p_status: status,
      p_passed: passed,
      p_total: tests.length,
    },
  });
  if (!rec.ok) throw new HttpError(502, "Não foi possível registrar a submissão.");
  return { status, passed, total: tests.length, points_awarded: rec.data?.points_awarded || 0, results: detail };
}

// ---------- Ranking e perfil ----------

async function ranking(env) {
  const r = await sb(env, "/rest/v1/rpc/get_ranking", { method: "POST", body: { p_limit: 50 } });
  if (!r.ok) throw new HttpError(502, "Não foi possível carregar o ranking.");
  return { ranking: r.data };
}

async function me(env, request) {
  const user = await requireUser(env, request);
  const [profile, stats, subs] = await Promise.all([
    getProfile(env, user.token, user.id),
    sb(env, "/rest/v1/rpc/get_my_stats", { method: "POST", body: { p_user: user.id, p_secret: env.WORKER_SECRET } }),
    sb(env, "/rest/v1/submissions?select=id,status,passed,total,language,created_at,problems(title,slug)&order=created_at.desc&limit=20", {
      token: user.token,
    }),
  ]);
  if (!profile) throw new HttpError(404, "Perfil não encontrado.");
  return { email: user.email, profile, stats: stats.data || {}, submissions: subs.ok ? subs.data : [] };
}

async function updateMe(env, request) {
  const user = await requireUser(env, request);
  const b = await readJson(request);
  const patch = {};
  if (b.display_name !== undefined) patch.display_name = str(b.display_name, "o nome", { min: 1, max: 40, required: true });
  if (b.bio !== undefined) patch.bio = str(b.bio, "a bio", { max: 200 });
  if (b.cidade !== undefined) patch.cidade = str(b.cidade, "a cidade", { max: 60 });
  if (!Object.keys(patch).length) throw new HttpError(400, "Nada para atualizar.");
  const r = await sb(env, `/rest/v1/profiles?id=eq.${user.id}`, {
    method: "PATCH",
    token: user.token,
    body: patch,
    headers: { Prefer: "return=representation" },
  });
  if (!r.ok || !r.data?.[0]) throw new HttpError(400, "Não foi possível atualizar o perfil.");
  return { profile: r.data[0] };
}

// ---------- Grupos ----------

async function listGroups(env, request) {
  const user = await requireUser(env, request);
  const [g, mine] = await Promise.all([
    sb(env, "/rest/v1/groups?select=id,name,description,owner_id,created_at,group_members(count)&order=created_at.desc", { token: user.token }),
    sb(env, `/rest/v1/group_members?select=group_id&user_id=eq.${user.id}`, { token: user.token }),
  ]);
  if (!g.ok) throw new HttpError(502, "Não foi possível carregar os grupos.");
  const joined = new Set((mine.data || []).map((m) => m.group_id));
  return {
    groups: g.data.map((x) => ({
      id: x.id,
      name: x.name,
      description: x.description,
      owner: x.owner_id === user.id,
      member: joined.has(x.id),
      members: x.group_members?.[0]?.count ?? 0,
    })),
  };
}

async function createGroup(env, request) {
  const user = await requireUser(env, request);
  const b = await readJson(request);
  const name = str(b.name, "o nome do grupo", { min: 3, max: 40, required: true });
  const description = str(b.description, "a descrição", { max: 200 });
  const g = await sb(env, "/rest/v1/groups", {
    method: "POST",
    token: user.token,
    body: { name, description, owner_id: user.id },
    headers: { Prefer: "return=representation" },
  });
  if (g.status === 409) throw new HttpError(409, "Já existe um grupo com esse nome.");
  if (!g.ok || !g.data?.[0]) throw new HttpError(400, "Não foi possível criar o grupo.");
  const group = g.data[0];
  await sb(env, "/rest/v1/group_members", { method: "POST", token: user.token, body: { group_id: group.id, user_id: user.id } });
  return { group: { id: group.id, name: group.name, description: group.description } };
}

async function getGroup(env, request, id) {
  const user = await requireUser(env, request);
  const [g, m] = await Promise.all([
    sb(env, `/rest/v1/groups?select=id,name,description,owner_id&id=eq.${id}`, { token: user.token }),
    sb(env, `/rest/v1/group_members?select=user_id,joined_at,profiles(username,display_name,points)&group_id=eq.${id}`, { token: user.token }),
  ]);
  const group = g.data?.[0];
  if (!group) throw new HttpError(404, "Grupo não encontrado.");
  const members = (m.data || [])
    .map((x) => ({
      user_id: x.user_id,
      username: x.profiles?.username,
      display_name: x.profiles?.display_name,
      points: x.profiles?.points ?? 0,
      owner: x.user_id === group.owner_id,
    }))
    .sort((a, b) => b.points - a.points);
  return { group: { ...group, owner: group.owner_id === user.id, member: members.some((x) => x.user_id === user.id) }, members };
}

async function joinGroup(env, request, id) {
  const user = await requireUser(env, request);
  const r = await sb(env, "/rest/v1/group_members", { method: "POST", token: user.token, body: { group_id: id, user_id: user.id } });
  if (r.status === 409) return { ok: true };
  if (!r.ok) throw new HttpError(404, "Grupo não encontrado.");
  return { ok: true };
}

async function leaveGroup(env, request, id) {
  const user = await requireUser(env, request);
  const r = await sb(env, `/rest/v1/group_members?group_id=eq.${id}&user_id=eq.${user.id}`, { method: "DELETE", token: user.token });
  if (!r.ok) throw new HttpError(400, "Não foi possível sair do grupo.");
  return { ok: true };
}

// ---------- Rotas ----------

async function route(env, request) {
  const url = new URL(request.url);
  const path = url.pathname.replace(/\/+$/, "") || "/";
  const m = request.method;
  let x;

  if (m === "GET" && path === "/") return { service: "coderank-api", ok: true };
  if (m === "GET" && path === "/health") return { ok: true };

  if (m === "POST" && path === "/auth/signup") return signup(env, request);
  if (m === "POST" && path === "/auth/login") return login(env, request);
  if (m === "POST" && path === "/auth/refresh") return refresh(env, request);
  if (m === "POST" && path === "/auth/logout") return logout(env, request);
  if (m === "POST" && path === "/auth/recover") return recover(env, request);

  if (m === "GET" && path === "/problems") return listProblems(env, request);
  if (m === "GET" && (x = /^\/problems\/([a-z0-9-]+)$/.exec(path))) return getProblem(env, request, x[1]);
  if (m === "POST" && (x = /^\/problems\/([a-z0-9-]+)\/run$/.exec(path))) return runCode(env, request, x[1]);
  if (m === "POST" && (x = /^\/problems\/([a-z0-9-]+)\/submit$/.exec(path))) return submit(env, request, x[1]);

  if (m === "GET" && path === "/ranking") return ranking(env);
  if (m === "GET" && path === "/me") return me(env, request);
  if (m === "PATCH" && path === "/me") return updateMe(env, request);

  if (m === "GET" && path === "/groups") return listGroups(env, request);
  if (m === "POST" && path === "/groups") return createGroup(env, request);
  if (m === "GET" && (x = /^\/groups\/(\d+)$/.exec(path))) return getGroup(env, request, Number(x[1]));
  if (m === "POST" && (x = /^\/groups\/(\d+)\/join$/.exec(path))) return joinGroup(env, request, Number(x[1]));
  if (m === "POST" && (x = /^\/groups\/(\d+)\/leave$/.exec(path))) return leaveGroup(env, request, Number(x[1]));

  throw new HttpError(404, "Rota não encontrada.");
}

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: cors(env) });
    try {
      return json(env, await route(env, request));
    } catch (err) {
      if (err instanceof HttpError) return json(env, { error: err.message }, err.status);
      console.error("erro não tratado", err?.stack || err);
      return json(env, { error: "Erro interno. Tente novamente." }, 500);
    }
  },
};

export { route, norm, HttpError };
