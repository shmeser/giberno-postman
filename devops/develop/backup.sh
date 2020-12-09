#!/bin/bash

dir_id=1r1sFc6MSPs-BvkcG9-Pap1XBeUkYuL9R # ID директории на google-диске

PROJ_DIR=/srv/giberno-server_develop
GDRIVE_DIR=$PROJ_DIR/devops

cd $PROJ_DIR # переходим в папку с проектом

postgres_db_archive_name=postgres-data-$(date +%Y-%m-%d.%H%M%S)
files_archive_name=files-$(date +%Y-%m-%d.%H%M%S)

postgres_db_path=./data/postgisdb # путь до volumes с базой данных
files_path=./files/media # путь до файлов

tar cfvj /tmp/${postgres_db_archive_name}.tar.bz2 ${postgres_db_path} # создаем архив с базой данных
tar cfvj /tmp/${files_archive_name}.tar.bz2 ${files_path} # создаем архив с файлами

# отпраляем архивы на google-диск
$GDRIVE_DIR/gdrive upload  --config $GDRIVE_DIR --service-account /develop/gdrive-account.json  --delete --parent ${dir_id} /tmp/${postgres_db_archive_name}.tar.bz2
$GDRIVE_DIR/gdrive upload  --config $GDRIVE_DIR --service-account /develop/gdrive-account.json  --delete --parent ${dir_id} /tmp/${files_archive_name}.tar.bz2

# необходимо удалить с google-диска старые бекапы, чтобы не забивать место

rotationDate=$(date -d "-3 day" +"%Y-%m-%d")
echo $rotationDate
files=$($GDRIVE_DIR/gdrive list --no-header --config $GDRIVE_DIR --service-account /develop/gdrive-account.json --query "'$dir_id' in parents and modifiedTime < '$rotationDate'" | awk '{ print $1 }')

for file in $files
do
$GDRIVE_DIR/gdrive --config $GDRIVE_DIR --service-account /develop/gdrive-account.json delete $file
done
