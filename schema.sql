-- Banco de dados do CodeRank para Supabase/PostgreSQL.
-- Execute este arquivo no SQL Editor de um projeto Supabase novo.

create extension if not exists pgcrypto;

create table if not exists public.profiles (
    id uuid primary key references auth.users(id) on delete cascade,
    email text not null,
    name text not null check (char_length(trim(name)) between 2 and 80),
    cep text,
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
create index if not exists idx_submissions_user on public.submissions(user_id, created_at desc);
create index if not exists idx_submissions_challenge on public.submissions(challenge_id, correct);
create index if not exists idx_notifications_user on public.notifications(user_id, read);

create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
    insert into public.profiles (id, email, name, cep, city, state, course, institution)
    values (
        new.id,
        coalesce(new.email, ''),
        coalesce(nullif(trim(new.raw_user_meta_data->>'name'), ''), split_part(coalesce(new.email, 'usuario'), '@', 1)),
        nullif(new.raw_user_meta_data->>'cep', ''),
        nullif(new.raw_user_meta_data->>'city', ''),
        nullif(new.raw_user_meta_data->>'state', ''),
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
for each row execute procedure public.handle_new_user();

create or replace function public.create_group(p_name text)
returns setof public.groups
language plpgsql
security definer set search_path = public
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
    values (trim(p_name), upper(substr(encode(gen_random_bytes(8), 'hex'), 1, 8)), auth.uid())
    returning * into created_group;

    insert into public.group_members (group_id, user_id, role)
    values (created_group.id, auth.uid(), 'owner');
    return next created_group;
end;
$$;

create or replace function public.join_group(p_invite_code text)
returns setof public.groups
language plpgsql
security definer set search_path = public
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
returns table (user_id uuid, name text, points integer, position bigint)
language sql
security definer set search_path = public
as $$
    select gm.user_id, p.name, gm.points,
           row_number() over (order by gm.points desc, lower(p.name) asc) as position
    from public.group_members gm
    join public.profiles p on p.id = gm.user_id
    where gm.group_id = p_group_id
      and exists (
          select 1 from public.group_members viewer
          where viewer.group_id = p_group_id and viewer.user_id = auth.uid()
      )
    order by gm.points desc, lower(p.name) asc;
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
security definer set search_path = public
as $$
declare
    challenge_points integer;
    already_solved boolean;
    awarded integer := 0;
begin
    if auth.uid() is null then
        raise exception 'Usuario nao autenticado';
    end if;
    select points into challenge_points from public.challenges where id = p_challenge_id and active;
    if challenge_points is null then
        raise exception 'Desafio nao encontrado';
    end if;

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
        p_exit_code, p_correct, p_execution_ms
    );

    if p_correct and not already_solved and p_group_id is not null then
        update public.group_members
        set points = points + challenge_points
        where group_id = p_group_id and user_id = auth.uid();
        if found then awarded := challenge_points; end if;
    end if;
    return query select p_correct, awarded;
end;
$$;

alter table public.profiles enable row level security;
alter table public.groups enable row level security;
alter table public.group_members enable row level security;
alter table public.challenges enable row level security;
alter table public.submissions enable row level security;
alter table public.notifications enable row level security;

create or replace function public.is_group_member(p_group_id uuid)
returns boolean
language sql
stable
security definer set search_path = public
as $$
    select exists (
        select 1 from public.group_members
        where group_id = p_group_id and user_id = auth.uid()
    );
$$;

create or replace function public.shares_group_with(p_user_id uuid)
returns boolean
language sql
stable
security definer set search_path = public
as $$
    select exists (
        select 1
        from public.group_members mine
        join public.group_members theirs on theirs.group_id = mine.group_id
        where mine.user_id = auth.uid() and theirs.user_id = p_user_id
    );
$$;

drop policy if exists profiles_select_related on public.profiles;
create policy profiles_select_related on public.profiles for select to authenticated
using (id = auth.uid() or public.shares_group_with(id));
drop policy if exists profiles_update_own on public.profiles;
create policy profiles_update_own on public.profiles for update to authenticated
using (id = auth.uid()) with check (id = auth.uid());

drop policy if exists groups_select_member on public.groups;
create policy groups_select_member on public.groups for select to authenticated
using (public.is_group_member(id));

drop policy if exists members_select_group on public.group_members;
create policy members_select_group on public.group_members for select to authenticated
using (public.is_group_member(group_id));

drop policy if exists challenges_select_active on public.challenges;
create policy challenges_select_active on public.challenges for select to authenticated
using (active);

drop policy if exists submissions_select_own on public.submissions;
create policy submissions_select_own on public.submissions for select to authenticated
using (user_id = auth.uid());

drop policy if exists notifications_own on public.notifications;
create policy notifications_own on public.notifications for select to authenticated
using (user_id = auth.uid());
drop policy if exists notifications_update_own on public.notifications;
create policy notifications_update_own on public.notifications for update to authenticated
using (user_id = auth.uid()) with check (user_id = auth.uid());

revoke all on function public.create_group(text) from public;
revoke all on function public.join_group(text) from public;
revoke all on function public.get_group_ranking(uuid) from public;
revoke all on function public.record_submission(uuid, uuid, text, text, text, text, integer, boolean, integer) from public;
revoke all on function public.is_group_member(uuid) from public;
revoke all on function public.shares_group_with(uuid) from public;
grant execute on function public.create_group(text) to authenticated;
grant execute on function public.join_group(text) to authenticated;
grant execute on function public.get_group_ranking(uuid) to authenticated;
grant execute on function public.record_submission(uuid, uuid, text, text, text, text, integer, boolean, integer) to authenticated;
grant execute on function public.is_group_member(uuid) to authenticated;
grant execute on function public.shares_group_with(uuid) to authenticated;

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
