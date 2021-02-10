# giberno-server

## Backups to Google Drive

crontab -e
```bash

PATH="/bin:/root"

0 4 * * * bash /srv/giberno-server_release/devops/release/backup.sh > /var/log/backup.sh.log 2>&1
```

#### GEO
Для создания миграций в приложении геоданных нужно установить расширение HSTORE для POSTGRES

```sql
CREATE EXTENSION hstore;
```


## Триггеры

```sql
DROP TRIGGER app_geo__cities__names_tsv__trigger ON app_geo__cities;
DROP TRIGGER app_geo__cities__native_tsv__trigger ON app_geo__cities;

CREATE OR REPLACE FUNCTION update_h_store_tsv() RETURNS trigger AS $$
    begin
      new.names_tsv = to_tsvector('pg_catalog.english', COALESCE(array_to_string(avals(new.names), ' '), ''));
      return new;
    end
    $$ LANGUAGE plpgsql;

CREATE TRIGGER app_geo__cities__names_tsv__trigger BEFORE INSERT OR UPDATE
    ON app_geo__cities FOR EACH ROW EXECUTE PROCEDURE 
    update_h_store_tsv();

CREATE TRIGGER app_geo__cities__native_tsv__trigger BEFORE INSERT OR UPDATE
    ON app_geo__cities FOR EACH ROW EXECUTE FUNCTION
    tsvector_update_trigger(native_tsv, 'pg_catalog.english', native);

UPDATE app_geo__cities set ID = ID;
```


##### Поддержка процедурных языков для PostgresQL

##### Windows
../PostgreSQL/13/doc/installation-notes.html


###### ENV
Добавить в переменные среды

`PYTHON_PATH` - `C:\Users\{user}\AppData\Local\Programs\Python\Python37`

`PATH` - `C:\Users\shmeser\AppData\Local\Programs\Python\Python37`

###### PostgresQL console

`create extension plpython3u;`

##### SQL для создания функций на базе python в postgres

```sql
CREATE OR REPLACE FUNCTION _pc_after(
    t_rule TEXT,
    t_after TIMESTAMP,
    inc BOOLEAN DEFAULT TRUE)
    RETURNS TIMESTAMP AS
$$
    from dateutil.rrule import rrulestr
    from dateutil.parser import parse

    rule = rrulestr(t_rule)
    _after = parse(t_after)
    occurence = rule.before(_after, inc=False)
    return occurence
$$
LANGUAGE 'plpython3u' VOLATILE;

-- = simple before function =
CREATE OR REPLACE FUNCTION _pc_before(
    t_rule TEXT, 
    t_before TIMESTAMP,
    inc BOOLEAN DEFAULT TRUE) 
    RETURNS TIMESTAMP AS
$$
    from dateutil.rrule import rrulestr
    from dateutil.parser import parse

    _rule = rrulestr(t_rule)
    _before = parse(t_before)
    occurence = _rule.before(_before, inc=False)
    return occurence
$$
LANGUAGE 'plpython3u' VOLATILE;

-- = simple between function =
CREATE OR REPLACE FUNCTION _pc_between(
    t_rule TEXT, 
    t_after TIMESTAMP, 
    t_before TIMESTAMP,
    inc BOOLEAN DEFAULT FALSE) 
    RETURNS SETOF TIMESTAMP AS
$$
    from dateutil.rrule import rrulestr
    from dateutil.parser import parse

    _rule = rrulestr(t_rule)
    _after = parse(t_after)
    _before = parse(t_before)
    occurences = _rule.between(_after, _before, inc)

    return occurences
$$
LANGUAGE 'plpython3u' VOLATILE;

-- = simple rrule_list_occurences function =
CREATE OR REPLACE FUNCTION rrule_list_occurences(
    frequency INTEGER, 
    by_weekday INTEGER[] DEFAULT NULL, 
    by_monthday INTEGER[] DEFAULT NULL,
    by_month INTEGER[] DEFAULT NULL,
    dt_start TIMESTAMPTZ DEFAULT CURRENT_DATE,
    dt_end TIMESTAMPTZ DEFAULT CURRENT_DATE + INTERVAL '1 month') 
    RETURNS TIMESTAMP[] AS
$$
    from dateutil.rrule import rrule
    from dateutil.parser import parse
    occurences = rrule(freq=frequency, byweekday=by_weekday, bymonthday=by_monthday, bymonth=by_month, dtstart=dt_start, until=dt_end)
    return list(occurences)
$$
LANGUAGE 'plpython3u' VOLATILE;

```