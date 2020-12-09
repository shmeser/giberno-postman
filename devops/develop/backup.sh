#!/bin/bash

dir_id=1TioiW5YollsYnTLKiXSB9YuUS_-riVVB # ID директории на google-диске

cd /srv/giberno-server_develop/ # переходим в папку с проектом


postgres_db_archive_name=postgres-data-$(date +%Y-%m-%d.%H%M%S)
files_archive_name=files-$(date +%Y-%m-%d.%H%M%S)

postgres_db_path=./data/postgisdb # путь до volumes с базой данных
files_path=./files/media # путь до файлов

tar cfvj /tmp/${postgres_db_archive_name}.tar.bz2 ${postgres_db_path} # создаем архив с базой данных
tar cfvj /tmp/${files_archive_name}.tar.bz2 ${files_path} # создаем архив с файлами

# отпраляем архивы на google-диск
gdrive upload  --service-account accounts.json  --delete --parent ${dir_id} /tmp/${postgres_db_archive_name}.tar.bz2
gdrive upload  --service-account accounts.json  --delete --parent ${dir_id} /tmp/${files_archive_name}.tar.bz2

# необходимо удалить с google-диска старые бекапы, чтобы не забивать место

rotationDate=$(date -d "-3 day" +"%Y-%m-%d")
echo $rotationDate
files=$(gdrive list --no-header --service-account accounts.json --query "'$dir_id' in parents and modifiedTime < '$rotationDate'" | awk '{ print $1 }')

for file in $files
do
gdrive --service-account accounts.json delete $file
done
