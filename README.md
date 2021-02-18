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

`PATH` - `C:\Users\{user}\AppData\Local\Programs\Python\Python37`

http://apt.postgresql.org/pub/repos/apt/pool/main/p/postgresql-13/


```
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'

wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -

sudo apt-get update

sudo apt-get install postgresql-plpython3-13
```

###### PostgresQL console

`create extension plpython3u;`

##### SQL для создания функций на базе python в postgres

```sql
CREATE EXTENSION plpython3u;



-- = simple rrule_list_occurences function =
CREATE OR REPLACE FUNCTION rrule_list_occurences(
	frequency INTEGER, 
	by_month INTEGER[],
	by_monthday INTEGER[],
	by_weekday INTEGER[], 
	dt_start CHAR DEFAULT NULL,
	dt_end CHAR DEFAULT NULL
) 
	RETURNS TIMESTAMPTZ[] AS
$$
from dateutil.rrule import rrule
from dateutil.parser import parse

if frequency is None:
    return []

kwargs = {}
if by_weekday:
	kwargs['byweekday']=by_weekday 
if by_monthday:
	kwargs['bymonthday']=by_monthday 
if by_month:
	kwargs['bymonth']=by_month 

if dt_start is not None and dt_end is not None:
	kwargs['dtstart']=parse(dt_start)
	kwargs['until']=parse(dt_end)
elif dt_start is not None and dt_end is None:
	kwargs['dtstart']=parse(dt_start)
	kwargs['count']=10
elif dt_start is None and dt_end is not None:
	kwargs['until']=parse(dt_end)
else:
	kwargs['count']=10  

occurences = rrule(freq=frequency, **kwargs)
return list(occurences)

$$
LANGUAGE 'plpython3u' VOLATILE;

```