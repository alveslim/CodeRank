import test from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import worker from "../src/index.js";

// --- Supabase simulado em memória ---
const TESTS = { 1: [{ input: "2 3", expected: "5" }, { input: "-4 10", expected: "6" }] };
const db = { submissions: [], points: 0, users: { tok: { id: "u1", email: "a@b.com" } } };
let calls = [];

globalThis.fetch = async (url, init = {}) => {
  const u = new URL(url);
  const path = u.pathname + u.search;
  calls.push(`${init.method || "GET"} ${path}`);
  const body = init.body ? JSON.parse(init.body) : null;
  const auth = (init.headers?.Authorization || "").replace("Bearer ", "");
  const ok = (data, status = 200) => new Response(JSON.stringify(data), { status });
  if (u.pathname === "/auth/v1/user") return db.users[auth] ? ok(db.users[auth]) : ok({ msg: "bad" }, 401);
  if (u.pathname === "/auth/v1/token" && u.searchParams.get("grant_type") === "password") {
    return body.password === "senha1234"
      ? ok({ access_token: "tok", refresh_token: "r", expires_in: 3600, user: { id: "u1", email: body.email } })
      : ok({ error_code: "invalid_credentials", msg: "Invalid login credentials" }, 400);
  }
  if (u.pathname === "/auth/v1/signup") return body.email === "dup@x.com" ? ok({ error_code: "user_already_exists" }, 422) : ok({ id: "new" });
  if (u.pathname === "/rest/v1/profiles" && (init.method || "GET") === "GET") {
    if (u.searchParams.has("username")) return ok(u.searchParams.get("username").includes("usado") ? [{ id: "x" }] : []);
    return ok([{ id: "u1", username: "ana", display_name: "Ana", bio: "", cidade: "", points: db.points }]);
  }
  if (u.pathname === "/rest/v1/problems") {
    const slug = u.searchParams.get("slug");
    if (slug === "eq.soma") return ok([{ id: 1, points: 10, example_input: "2 3", slug: "soma" }]);
    if (slug) return ok([]);
    return ok([{ id: 1, slug: "soma", title: "Soma", difficulty: "facil", points: 10 }]);
  }
  if (u.pathname === "/rest/v1/submissions") return ok(db.submissions.filter((s) => s.status === "accepted").map((s) => ({ problem_id: s.problem_id })));
  if (u.pathname === "/rest/v1/rpc/worker_get_tests") return body.p_secret === "S" ? ok(TESTS[body.p_problem]) : ok({}, 403);
  if (u.pathname === "/rest/v1/rpc/worker_record_submission") {
    const first = body.p_status === "accepted" && !db.submissions.some((s) => s.status === "accepted");
    db.submissions.push({ problem_id: body.p_problem, status: body.p_status });
    if (first) db.points += 10;
    return ok({ id: db.submissions.length, points_awarded: first ? 10 : 0 });
  }
  if (u.pathname === "/rest/v1/rpc/get_ranking") return ok([{ username: "ana", display_name: "Ana", points: db.points, solved: 1 }]);
  throw new Error("rota simulada ausente: " + path);
};

// --- Judge real (Python) via subprocesso ---
const JUDGE = {
  async fetch(_url, init) {
    const out = execFileSync("python3", ["-c", `
import sys, json
sys.path.insert(0, "../judge")
import entry
d = json.loads(sys.stdin.read())
body, status = entry.run_all(d["source"], d["inputs"])
print(json.dumps({"status": status, "body": body}))
`], { input: init.body, encoding: "utf8" });
    const { status, body } = JSON.parse(out);
    return new Response(JSON.stringify(body), { status });
  },
};

const env = { SUPABASE_URL: "https://sb.test", SUPABASE_KEY: "anon", WORKER_SECRET: "S", JUDGE };
const call = async (method, path, body, token) => {
  const res = await worker.fetch(new Request("https://api.test" + path, {
    method,
    headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    body: body === undefined ? undefined : JSON.stringify(body),
  }), env);
  return { status: res.status, body: await res.json(), headers: res.headers };
};

test("CORS preflight", async () => {
  const res = await worker.fetch(new Request("https://api.test/me", { method: "OPTIONS" }), env);
  assert.equal(res.status, 204);
  assert.equal(res.headers.get("Access-Control-Allow-Origin"), "*");
});

test("login ok e erro", async () => {
  const ok = await call("POST", "/auth/login", { email: "a@b.com", password: "senha1234" });
  assert.equal(ok.status, 200);
  assert.equal(ok.body.access_token, "tok");
  assert.equal(ok.body.profile.username, "ana");
  const bad = await call("POST", "/auth/login", { email: "a@b.com", password: "errada123" });
  assert.equal(bad.status, 401);
  assert.equal(bad.body.error, "E-mail ou senha incorretos.");
});

test("cadastro valida e trata duplicados", async () => {
  assert.equal((await call("POST", "/auth/signup", { email: "x", password: "senha1234", username: "bob" })).status, 400);
  assert.equal((await call("POST", "/auth/signup", { email: "a@x.com", password: "curta", username: "bob" })).status, 400);
  assert.equal((await call("POST", "/auth/signup", { email: "a@x.com", password: "senha1234", username: "b!" })).status, 400);
  assert.equal((await call("POST", "/auth/signup", { email: "a@x.com", password: "senha1234", username: "usado" })).status, 409);
  assert.equal((await call("POST", "/auth/signup", { email: "dup@x.com", password: "senha1234", username: "novo" })).status, 409);
  const ok = await call("POST", "/auth/signup", { email: "n@x.com", password: "senha1234", username: "novo" });
  assert.deepEqual(ok.body, { ok: true, needs_confirmation: true });
});

test("rotas protegidas exigem token", async () => {
  assert.equal((await call("GET", "/me")).status, 401);
  assert.equal((await call("POST", "/problems/soma/submit", { source: "print(1)" })).status, 401);
  assert.equal((await call("GET", "/me", undefined, "invalido")).status, 401);
});

test("lista desafios sem login e detalhe 404", async () => {
  const l = await call("GET", "/problems");
  assert.equal(l.status, 200);
  assert.equal(l.body.problems[0].solved, false);
  assert.equal((await call("GET", "/problems/nao-existe")).status, 404);
});

test("submit: errado, correto (pontua uma vez) e erros", async () => {
  const wrong = await call("POST", "/problems/soma/submit", { source: "print(0)" }, "tok");
  assert.equal(wrong.body.status, "wrong_answer");
  assert.equal(wrong.body.passed, 0);
  assert.equal(wrong.body.results[0].expected, "5");
  assert.equal(wrong.body.results[1].expected, undefined, "teste oculto não revela esperado");

  const right = "a,b=map(int,input().split())\nprint(a+b)";
  const ok = await call("POST", "/problems/soma/submit", { source: right }, "tok");
  assert.equal(ok.body.status, "accepted");
  assert.equal(ok.body.points_awarded, 10);
  const again = await call("POST", "/problems/soma/submit", { source: right }, "tok");
  assert.equal(again.body.points_awarded, 0, "pontos só na primeira aceitação");
  const l = await call("GET", "/problems", undefined, "tok");
  assert.equal(l.body.problems[0].solved, true);

  const rt = await call("POST", "/problems/soma/submit", { source: "print(1/0)" }, "tok");
  assert.equal(rt.body.status, "runtime_error");
  assert.match(rt.body.results[0].stderr, /ZeroDivisionError/);
  const syn = await call("POST", "/problems/soma/submit", { source: "def f(:" }, "tok");
  assert.equal(syn.body.status, "runtime_error");
  const to = await call("POST", "/problems/soma/submit", { source: "while True: pass" }, "tok");
  assert.equal(to.body.status, "timeout");
  assert.equal((await call("POST", "/problems/soma/submit", { source: "" }, "tok")).status, 400);
  assert.equal((await call("POST", "/problems/soma/submit", { source: "x", language: "java" }, "tok")).status, 400);
  assert.equal((await call("POST", "/problems/nada/submit", { source: "print(1)" }, "tok")).status, 404);
});

test("run executa com stdin do exemplo", async () => {
  const r = await call("POST", "/problems/soma/run", { source: "a,b=map(int,input().split())\nprint(a*b)" }, "tok");
  assert.equal(r.body.stdout.trim(), "6");
  const c = await call("POST", "/problems/soma/run", { source: "print(input())", stdin: "oi" }, "tok");
  assert.equal(c.body.stdout.trim(), "oi");
});

test("ranking público", async () => {
  const r = await call("GET", "/ranking");
  assert.equal(r.status, 200);
  assert.equal(r.body.ranking[0].username, "ana");
});

test("rota inexistente", async () => {
  assert.equal((await call("GET", "/xyz")).status, 404);
});
