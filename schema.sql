-- CodeRank — esquema do banco (Supabase / Postgres).
-- Aplique no SQL Editor do projeto Supabase. Depois defina o segredo da API:
--   insert into private.worker_secret(id, secret) values (1, '<segredo-aleatorio>');
-- O mesmo valor deve ser o secret WORKER_SECRET do Worker coderank-api.
-- Os desafios e casos de teste (public.problems / public.problem_tests) são
-- carregados à parte para que os testes ocultos não fiquem no repositório.

create schema if not exists private;
revoke all on schema private from public, anon, authenticated;
create table private.worker_secret (id int primary key default 1 check (id = 1), secret text not null);
alter table private.worker_secret enable row level security;

create table public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  username text not null unique check (username ~ '^[A-Za-z0-9_]{3,20}$'),
  display_name text,
  bio text not null default '',
  points int not null default 0,
  created_at timestamptz not null default now(),
  cidade text not null default '' check (char_length(cidade) <= 60)
);
create unique index profiles_username_lower_idx on public.profiles (lower(username));

create table public.problems (
  id serial primary key,
  slug text not null unique,
  title text not null,
  description text not null,
  difficulty text not null check (difficulty in ('facil','medio','dificil')),
  points int not null check (points > 0),
  example_input text not null default '',
  example_output text not null default '',
  created_at timestamptz not null default now()
);

create table public.problem_tests (
  id serial primary key,
  problem_id int not null references public.problems(id) on delete cascade,
  input text not null,
  expected text not null,
  position int not null default 0
);

create table public.submissions (
  id bigserial primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  problem_id int not null references public.problems(id) on delete cascade,
  language text not null,
  source text not null,
  status text not null check (status in ('accepted','wrong_answer','runtime_error','timeout','error')),
  passed int not null default 0,
  total int not null default 0,
  created_at timestamptz not null default now()
);
create index on public.submissions (user_id, created_at desc);
create index on public.submissions (problem_id, user_id, status);

create table public.groups (
  id serial primary key,
  name text not null unique check (char_length(name) between 3 and 40),
  description text not null default '',
  owner_id uuid references auth.users(id) on delete set null,
  created_at timestamptz not null default now()
);

create table public.group_members (
  group_id int not null references public.groups(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  joined_at timestamptz not null default now(),
  primary key (group_id, user_id),
  constraint group_members_profile_fk foreign key (user_id) references public.profiles(id) on delete cascade
);
create index on public.group_members (user_id);

alter table public.profiles enable row level security;
alter table public.problems enable row level security;
alter table public.problem_tests enable row level security;
alter table public.submissions enable row level security;
alter table public.groups enable row level security;
alter table public.group_members enable row level security;

create policy profiles_read on public.profiles for select using (true);
create policy profiles_update_own on public.profiles for update to authenticated
  using (auth.uid() = id) with check (auth.uid() = id);
revoke update on public.profiles from anon, authenticated;
grant update (display_name, bio, cidade) on public.profiles to authenticated;
revoke insert, delete on public.profiles from anon, authenticated;

create policy problems_read on public.problems for select using (true);
revoke insert, update, delete on public.problems from anon, authenticated;

revoke all on public.problem_tests from anon, authenticated;   -- só via worker_get_tests

create policy submissions_read_own on public.submissions for select to authenticated using (auth.uid() = user_id);
revoke insert, update, delete on public.submissions from anon, authenticated;

create policy groups_read on public.groups for select using (true);
create policy groups_insert_own on public.groups for insert to authenticated with check (auth.uid() = owner_id);
revoke update, delete on public.groups from anon, authenticated;

create policy members_read on public.group_members for select using (true);
create policy members_join_self on public.group_members for insert to authenticated with check (auth.uid() = user_id);
create policy members_leave_self on public.group_members for delete to authenticated using (auth.uid() = user_id);
revoke update on public.group_members from anon, authenticated;

-- Perfil criado automaticamente no cadastro
create or replace function public.handle_new_user() returns trigger
language plpgsql security definer set search_path = public as $$
declare base text; candidate text; n int := 0;
begin
  base := regexp_replace(coalesce(new.raw_user_meta_data->>'username', split_part(new.email,'@',1)), '[^A-Za-z0-9_]', '', 'g');
  if char_length(base) < 3 then base := base || 'user'; end if;
  base := left(base, 16);
  candidate := base;
  while exists (select 1 from public.profiles where lower(username) = lower(candidate)) loop
    n := n + 1; candidate := base || n::text;
  end loop;
  insert into public.profiles (id, username, display_name, cidade)
  values (new.id, candidate, left(coalesce(new.raw_user_meta_data->>'display_name', candidate), 40),
          left(coalesce(new.raw_user_meta_data->>'cidade', ''), 60));
  return new;
end $$;
create trigger on_auth_user_created after insert on auth.users
  for each row execute function public.handle_new_user();

-- Funções chamadas somente pela API (Cloudflare Worker), protegidas por segredo compartilhado
create or replace function public.worker_check(p_secret text) returns void
language plpgsql security definer set search_path = '' as $$
begin
  if not exists (select 1 from private.worker_secret where secret = p_secret) then
    raise exception 'forbidden' using errcode = '42501';
  end if;
end $$;

create or replace function public.worker_get_tests(p_secret text, p_problem int) returns jsonb
language plpgsql security definer set search_path = '' as $$
begin
  perform public.worker_check(p_secret);
  return coalesce((select jsonb_agg(jsonb_build_object('input', input, 'expected', expected) order by position, id)
                   from public.problem_tests where problem_id = p_problem), '[]'::jsonb);
end $$;

create or replace function public.worker_record_submission(
  p_secret text, p_user uuid, p_problem int, p_language text, p_source text,
  p_status text, p_passed int, p_total int) returns jsonb
language plpgsql security definer set search_path = '' as $$
declare first_ok boolean := false; pts int := 0; sid bigint;
begin
  perform public.worker_check(p_secret);
  if p_status = 'accepted' and not exists (
      select 1 from public.submissions where user_id = p_user and problem_id = p_problem and status = 'accepted') then
    first_ok := true;
    select points into pts from public.problems where id = p_problem;
    update public.profiles set points = points + pts where id = p_user;
  end if;
  insert into public.submissions (user_id, problem_id, language, source, status, passed, total)
  values (p_user, p_problem, p_language, left(p_source, 50000), p_status, p_passed, p_total) returning id into sid;
  return jsonb_build_object('id', sid, 'points_awarded', case when first_ok then pts else 0 end);
end $$;

create or replace function public.get_ranking(p_limit int default 50) returns table (
  username text, display_name text, points int, solved bigint)
language sql stable security definer set search_path = '' as $$
  select p.username, p.display_name, p.points,
         (select count(distinct s.problem_id) from public.submissions s where s.user_id = p.id and s.status = 'accepted')
  from public.profiles p order by p.points desc, p.created_at asc limit least(greatest(p_limit,1),200)
$$;

create or replace function public.get_my_stats(p_user uuid, p_secret text) returns jsonb
language plpgsql security definer set search_path = '' as $$
begin
  perform public.worker_check(p_secret);
  return jsonb_build_object(
    'solved', (select count(distinct problem_id) from public.submissions where user_id = p_user and status = 'accepted'),
    'submissions', (select count(*) from public.submissions where user_id = p_user),
    'rank', (select count(*) + 1 from public.profiles where points > (select points from public.profiles where id = p_user)));
end $$;

revoke execute on all functions in schema public from public, anon, authenticated;
grant execute on function public.worker_get_tests(text,int) to anon, authenticated;
grant execute on function public.worker_record_submission(text,uuid,int,text,text,text,int,int) to anon, authenticated;
grant execute on function public.get_my_stats(uuid,text) to anon, authenticated;
grant execute on function public.get_ranking(int) to anon, authenticated;
