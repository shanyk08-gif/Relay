-- Run once in the Relay project's SQL Editor. No existing data is removed.
begin;
create table if not exists public.relay_records (
  kind text not null check (kind in ('workspace','session','challenge')),
  key text not null,
  value jsonb not null,
  expires double precision,
  primary key (kind,key),
  check (octet_length(value::text) <= 4200000)
);
create index if not exists relay_records_expiry on public.relay_records(expires) where expires is not null;
alter table public.relay_records enable row level security;
revoke all on public.relay_records from anon, authenticated;
grant select,insert,update,delete on public.relay_records to service_role;
create table if not exists public.relay_quotas (
  key text primary key,
  used integer not null,
  expires timestamptz not null
);
alter table public.relay_quotas enable row level security;
revoke all on public.relay_quotas from anon, authenticated;
grant select,insert,update,delete on public.relay_quotas to service_role;
create or replace function public.relay_take_quota(bucket text, maximum integer, seconds integer)
returns boolean language plpgsql set search_path = '' as $$
declare total integer;
begin
  if maximum < 1 or seconds < 1 then return false; end if;
  delete from public.relay_quotas where expires <= now();
  delete from public.relay_records where expires <= extract(epoch from now());
  insert into public.relay_quotas as q(key,used,expires)
  values(bucket,1,now()+make_interval(secs=>seconds))
  on conflict(key) do update set used=q.used+1 where q.used<maximum
  returning used into total;
  return total is not null;
end;
$$;
revoke all on function public.relay_take_quota(text,integer,integer) from public,anon,authenticated;
grant execute on function public.relay_take_quota(text,integer,integer) to service_role;
commit;
