-- MVP: a live beacon may reference an active catalog course before term-specific
-- course_offerings are populated. Term offerings remain the source of truth once
-- available, especially for enrollment-restricted beacons.
drop function if exists public.create_map_beacon(
  double precision, double precision, uuid, text, text, integer, integer, boolean
);

create function public.create_map_beacon(
  p_longitude double precision,
  p_latitude double precision,
  p_course_offering_id uuid,
  p_title text,
  p_description text,
  p_duration_minutes integer default 120,
  p_max_attendees integer default null,
  p_course_members_only boolean default false,
  p_course_id uuid default null
) returns uuid
language plpgsql security definer set search_path = public as $$
declare
  v_id uuid;
  v_course_code text;
begin
  if auth.uid() is null then raise exception 'Authentication required'; end if;
  if p_longitude is null or p_latitude is null
     or p_longitude not between -180 and 180
     or p_latitude not between -90 and 90 then
    raise exception 'Invalid map coordinates';
  end if;
  if p_duration_minutes is null or p_duration_minutes not between 1 and 180 then
    raise exception 'Beacon duration must be between 1 and 180 minutes';
  end if;
  if p_max_attendees is not null and p_max_attendees < 1 then
    raise exception 'Maximum attendees must be positive';
  end if;
  if char_length(trim(coalesce(p_title, ''))) not between 2 and 80 then
    raise exception 'A beacon title must be 2 to 80 characters';
  end if;

  if p_course_offering_id is not null then
    select c.course_code into v_course_code
    from public.course_offerings o
    join public.courses c on c.id = o.course_id
    where o.id = p_course_offering_id and o.active and c.active;
  else
    select c.course_code into v_course_code
    from public.courses c
    where c.id = p_course_id and c.active;
  end if;

  if v_course_code is null then
    raise exception 'Active course is unavailable';
  end if;
  if coalesce(p_course_members_only, false) and p_course_offering_id is null then
    raise exception 'Course enrollment restriction requires an active course offering';
  end if;

  insert into public.map_beacons(
    user_id, course_offering_id, course_code, title, description,
    coordinates, expires_at, max_attendees, course_members_only
  ) values (
    auth.uid(), p_course_offering_id, v_course_code, trim(p_title), trim(p_description),
    extensions.st_setsrid(extensions.st_makepoint(p_longitude, p_latitude), 4326),
    now() + make_interval(mins => p_duration_minutes), p_max_attendees,
    coalesce(p_course_members_only, false)
  ) returning id into v_id;

  return v_id;
end;
$$;

grant execute on function public.create_map_beacon(
  double precision, double precision, uuid, text, text, integer, integer, boolean, uuid
) to authenticated;
