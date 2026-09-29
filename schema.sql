-- Banco de dados do CodeRank para Supabase/PostgreSQL.
-- Execute este arquivo no SQL Editor de um projeto Supabase novo.

create extension if not exists pgcrypto;

-- Funcoes auxiliares de autorizacao ficam fora do schema exposto pela Data API.
create schema if not exists private;
revoke all on schema private from public, anon, authenticated;
grant usage on schema private to authenticated;

-- Novas funcoes nao devem nascer executaveis pela API por padrao.
alter default privileges in schema public revoke execute on functions from public, anon, authenticated;
alter default privileges in schema private revoke execute on functions from public, anon, authenticated;

create table if not exists public.profiles (
    id uuid primary key references auth.users(id) on delete cascade,
    email text not null,
    name text not null check (char_length(trim(name)) between 2 and 80),
    cep text constraint profiles_cep_format
        check (cep is null or cep ~ '^[0-9]{8}$'),
    city text,
    state text,
    course text default 'Engenharia de Software',
    institution text default 'FAMETRO',
    avatar_url text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.groups (
    id uuid primary key default gen_random_uuid(),
    name text not null check (char_length(trim(name)) between 3 and 30),
    invite_code text not null unique,
    owner_id uuid not null references public.profiles(id) on delete cascade,
    created_at timestamptz not null default now()
);

create table if not exists public.group_members (
    group_id uuid not null references public.groups(id) on delete cascade,
    user_id uuid not null references public.profiles(id) on delete cascade,
    role text not null default 'member' check (role in ('owner', 'admin', 'member')),
    points integer not null default 0 check (points >= 0),
    joined_at timestamptz not null default now(),
    primary key (group_id, user_id)
);

create table if not exists public.challenges (
    id uuid primary key default gen_random_uuid(),
    title text not null,
    description text not null,
    language text not null check (language in ('python', 'java', 'any')),
    difficulty text not null default 'Facil' check (difficulty in ('Facil', 'Medio', 'Dificil')),
    points integer not null default 100 check (points > 0),
    expected_output text not null,
    active boolean not null default true,
    created_at timestamptz not null default now(),
    unique (title, language)
);

create table if not exists public.submissions (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.profiles(id) on delete cascade,
    challenge_id uuid not null references public.challenges(id) on delete cascade,
    group_id uuid references public.groups(id) on delete set null,
    language text not null check (language in ('python', 'java')),
    source_code text not null check (octet_length(source_code) <= 50000),
    stdout text not null default '',
    stderr text not null default '',
    exit_code integer not null,
    correct boolean not null default false,
    execution_ms integer not null default 0 check (execution_ms >= 0),
    created_at timestamptz not null default now()
);

create table if not exists public.notifications (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.profiles(id) on delete cascade,
    message text not null,
    read boolean not null default false,
    created_at timestamptz not null default now()
);

create index if not exists idx_group_members_user on public.group_members(user_id);
create index if not exists idx_groups_owner on public.groups(owner_id);
create index if not exists idx_submissions_user on public.submissions(user_id, created_at desc);
create index if not exists idx_submissions_challenge on public.submissions(challenge_id, correct);
create index if not exists idx_submissions_group on public.submissions(group_id);
create index if not exists idx_notifications_user on public.notifications(user_id, read);

create or replace function private.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = pg_catalog
as $$
begin
    insert into public.profiles (id, email, name, cep, city, state, course, institution)
    values (
        new.id,
        coalesce(new.email, ''),
        coalesce(nullif(trim(new.raw_user_meta_data->>'name'), ''), split_part(coalesce(new.email, 'usuario'), '@', 1)),
        case
            when coalesce(new.raw_user_meta_data->>'cep', '') ~ '^[0-9]{8}$'
            then new.raw_user_meta_data->>'cep'
            else null
        end,
        case
            when coalesce(new.raw_user_meta_data->>'cep', '') ~ '^[0-9]{8}$'
            then nullif(new.raw_user_meta_data->>'city', '')
            else null
        end,
        case
            when coalesce(new.raw_user_meta_data->>'cep', '') ~ '^[0-9]{8}$'
            then nullif(new.raw_user_meta_data->>'state', '')
            else null
        end,
        coalesce(nullif(new.raw_user_meta_data->>'course', ''), 'Engenharia de Software'),
        coalesce(nullif(new.raw_user_meta_data->>'institution', ''), 'FAMETRO')
    )
    on conflict (id) do nothing;
    return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
after insert on auth.users
for each row execute procedure private.handle_new_user();

create or replace function private.is_group_member(p_group_id uuid)
returns boolean
language sql
stable
security definer set search_path = pg_catalog
as $$
    select exists (
        select 1 from public.group_members
        where group_id = p_group_id and user_id = auth.uid()
    );
$$;

create or replace function private.shares_group_with(p_user_id uuid)
returns boolean
language sql
stable
security definer set search_path = pg_catalog
as $$
    select exists (
        select 1
        from public.group_members mine
        join public.group_members theirs on theirs.group_id = mine.group_id
        where mine.user_id = auth.uid() and theirs.user_id = p_user_id
    );
$$;

create or replace function public.create_group(p_name text)
returns setof public.groups
language plpgsql
security definer set search_path = pg_catalog
as $$
declare
    created_group public.groups;
begin
    if auth.uid() is null then
        raise exception 'Usuario nao autenticado';
    end if;
    if char_length(trim(p_name)) not between 3 and 30 then
        raise exception 'O nome do grupo deve ter entre 3 e 30 caracteres';
    end if;

    insert into public.groups (name, invite_code, owner_id)
    values (trim(p_name), upper(substr(replace(gen_random_uuid()::text, '-', ''), 1, 8)), auth.uid())
    returning * into created_group;

    insert into public.group_members (group_id, user_id, role)
    values (created_group.id, auth.uid(), 'owner');
    return next created_group;
end;
$$;

create or replace function public.join_group(p_invite_code text)
returns setof public.groups
language plpgsql
security definer set search_path = pg_catalog
as $$
declare
    selected_group public.groups;
begin
    if auth.uid() is null then
        raise exception 'Usuario nao autenticado';
    end if;
    select * into selected_group
    from public.groups
    where invite_code = upper(trim(p_invite_code));
    if selected_group.id is null then
        raise exception 'Codigo de convite invalido';
    end if;
    insert into public.group_members (group_id, user_id, role)
    values (selected_group.id, auth.uid(), 'member')
    on conflict (group_id, user_id) do nothing;
    return next selected_group;
end;
$$;

create or replace function public.get_group_ranking(p_group_id uuid)
returns table (user_id uuid, name text, points integer, "position" bigint)
language sql
security invoker set search_path = pg_catalog
as $$
    select gm.user_id, p.name, gm.points,
           row_number() over (order by gm.points desc, lower(p.name) asc) as "position"
    from public.group_members gm
    join public.profiles p on p.id = gm.user_id
    where gm.group_id = p_group_id
      and exists (
          select 1 from public.group_members viewer
          where viewer.group_id = p_group_id and viewer.user_id = auth.uid()
      )
    order by gm.points desc, lower(p.name) asc;
$$;

create or replace function public.remove_group_member(p_group_id uuid, p_user_id uuid)
returns void
language plpgsql
security definer set search_path = pg_catalog
as $$
declare
    current_role text;
    target_role text;
begin
    select role into current_role from public.group_members
    where group_id = p_group_id and user_id = auth.uid();
    select role into target_role from public.group_members
    where group_id = p_group_id and user_id = p_user_id;

    if current_role not in ('owner', 'admin') then
        raise exception 'Somente administradores podem remover membros';
    end if;
    if target_role is null then
        raise exception 'Membro nao encontrado';
    end if;
    if target_role = 'owner' or p_user_id = auth.uid() then
        raise exception 'O proprietario nao pode ser removido';
    end if;
    if current_role = 'admin' and target_role = 'admin' then
        raise exception 'Um administrador nao pode remover outro administrador';
    end if;
    delete from public.group_members where group_id = p_group_id and user_id = p_user_id;
end;
$$;

create or replace function public.record_submission(
    p_challenge_id uuid,
    p_group_id uuid,
    p_language text,
    p_source_code text,
    p_stdout text,
    p_stderr text,
    p_exit_code integer,
    p_correct boolean,
    p_execution_ms integer
)
returns table (accepted boolean, points_awarded integer)
language plpgsql
security definer set search_path = pg_catalog
as $$
declare
    challenge_points integer;
    v_expected_output text;
    v_correct boolean;
    already_solved boolean;
    awarded integer := 0;
begin
    if auth.uid() is null then
        raise exception 'Usuario nao autenticado';
    end if;
    if p_group_id is not null and not private.is_group_member(p_group_id) then
        raise exception 'Usuario nao participa deste grupo';
    end if;
    select points, expected_output into challenge_points, v_expected_output
    from public.challenges where id = p_challenge_id and active;
    if challenge_points is null then
        raise exception 'Desafio nao encontrado';
    end if;

    -- O sinal enviado pelo cliente e mantido por compatibilidade, mas nao e confiavel.
    -- A aprovacao e recalculada com a saida registrada e o codigo de retorno.
    v_correct := p_exit_code = 0
        and btrim(replace(coalesce(p_stdout, ''), E'\r\n', E'\n'))
            = btrim(replace(v_expected_output, E'\r\n', E'\n'));

    select exists(
        select 1 from public.submissions
        where user_id = auth.uid()
          and challenge_id = p_challenge_id
          and group_id is not distinct from p_group_id
          and correct
    ) into already_solved;

    insert into public.submissions (
        user_id, challenge_id, group_id, language, source_code,
        stdout, stderr, exit_code, correct, execution_ms
    ) values (
        auth.uid(), p_challenge_id, p_group_id, p_language, p_source_code,
        left(coalesce(p_stdout, ''), 50000), left(coalesce(p_stderr, ''), 50000),
        p_exit_code, v_correct, p_execution_ms
    );

    if v_correct and not already_solved and p_group_id is not null then
        update public.group_members
        set points = points + challenge_points
        where group_id = p_group_id and user_id = auth.uid();
        if found then awarded := challenge_points; end if;
    end if;
    if awarded > 0 then
        insert into public.notifications (user_id, message)
        select auth.uid(), 'Voce ganhou ' || awarded || ' pontos em ' || title || '.'
        from public.challenges where id = p_challenge_id;
    end if;
    return query select v_correct, awarded;
end;
$$;

alter table public.profiles enable row level security;
alter table public.groups enable row level security;
alter table public.group_members enable row level security;
alter table public.challenges enable row level security;
alter table public.submissions enable row level security;
alter table public.notifications enable row level security;

drop policy if exists profiles_select_related on public.profiles;
create policy profiles_select_related on public.profiles for select to authenticated
using (id = (select auth.uid()) or private.shares_group_with(id));
drop policy if exists profiles_update_own on public.profiles;
create policy profiles_update_own on public.profiles for update to authenticated
using (id = (select auth.uid())) with check (id = (select auth.uid()));

drop policy if exists groups_select_member on public.groups;
create policy groups_select_member on public.groups for select to authenticated
using (private.is_group_member(id));

drop policy if exists members_select_group on public.group_members;
create policy members_select_group on public.group_members for select to authenticated
using (private.is_group_member(group_id));

drop policy if exists challenges_select_active on public.challenges;
create policy challenges_select_active on public.challenges for select to authenticated
using (active);

drop policy if exists submissions_select_own on public.submissions;
create policy submissions_select_own on public.submissions for select to authenticated
using (user_id = (select auth.uid()));

drop policy if exists notifications_own on public.notifications;
create policy notifications_own on public.notifications for select to authenticated
using (user_id = (select auth.uid()));
drop policy if exists notifications_update_own on public.notifications;
create policy notifications_update_own on public.notifications for update to authenticated
using (user_id = (select auth.uid())) with check (user_id = (select auth.uid()));

revoke all on function public.create_group(text) from public, anon, authenticated;
revoke all on function public.join_group(text) from public, anon, authenticated;
revoke all on function public.get_group_ranking(uuid) from public, anon, authenticated;
revoke all on function public.remove_group_member(uuid, uuid) from public, anon, authenticated;
revoke all on function public.record_submission(uuid, uuid, text, text, text, text, integer, boolean, integer) from public, anon, authenticated;
revoke all on function private.handle_new_user() from public, anon, authenticated;
revoke all on function private.is_group_member(uuid) from public, anon;
revoke all on function private.shares_group_with(uuid) from public, anon;
grant execute on function public.create_group(text) to authenticated;
grant execute on function public.join_group(text) to authenticated;
grant execute on function public.get_group_ranking(uuid) to authenticated;
grant execute on function public.remove_group_member(uuid, uuid) to authenticated;
grant execute on function public.record_submission(uuid, uuid, text, text, text, text, integer, boolean, integer) to authenticated;
grant execute on function private.is_group_member(uuid) to authenticated;
grant execute on function private.shares_group_with(uuid) to authenticated;

-- A opcao "automatic RLS" do projeto cria este gatilho auxiliar no schema
-- publico. O gatilho continua funcionando sem ser chamavel pela Data API.
do $$
begin
    if to_regprocedure('public.rls_auto_enable()') is not null then
        execute 'revoke execute on function public.rls_auto_enable() from public, anon, authenticated';
    end if;
end;
$$;

revoke all on table public.profiles from anon;
revoke all on table public.groups from anon;
revoke all on table public.group_members from anon;
revoke all on table public.challenges from anon;
revoke all on table public.submissions from anon;
revoke all on table public.notifications from anon;
grant select on table public.profiles to authenticated;
grant update (name, cep, city, state, course, institution, avatar_url, updated_at)
    on table public.profiles to authenticated;
grant select on table public.groups to authenticated;
grant select on table public.group_members to authenticated;
grant select on table public.challenges to authenticated;
grant select on table public.submissions to authenticated;
grant select, update (read) on table public.notifications to authenticated;

insert into public.challenges (title, description, language, difficulty, points, expected_output)
values
    ('Soma simples', 'Imprima o resultado de 2 + 3.', 'python', 'Facil', 100, '5'),
    ('Soma simples em Java', 'Imprima o resultado de 2 + 3.', 'java', 'Facil', 100, '5'),
    ('Maior numero', 'Imprima o maior valor da lista [3, 8, 2, 5].', 'python', 'Medio', 150, '8')
on conflict (title, language) do nothing;
