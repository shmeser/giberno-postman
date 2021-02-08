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