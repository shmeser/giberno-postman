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
