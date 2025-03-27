#!/bin/bash

mypath=`realpath "$0"`
mybase=`dirname "$mypath"`
cd $mybase

datadir="${1:-data/}"
if [ ! -d $datadir ] ; then
    echo "$datadir does not exist under $mybase"
    exit 1
fi

source ../.flaskenv
dbname=$DB_NAME

export PGPASSWORD=$DB_PASSWORD

if [[ -n `psql -U $DB_USER -h $DB_HOST -p $DB_PORT -lqt | cut -d \| -f 1 | grep -w "$dbname"` ]]; then
    dropdb -U $DB_USER -h $DB_HOST -p $DB_PORT $dbname
fi
createdb -U $DB_USER -h $DB_HOST -p $DB_PORT $dbname

psql -U $DB_USER -h $DB_HOST -p $DB_PORT -af create.sql $dbname
cd $datadir
psql -U $DB_USER -h $DB_HOST -p $DB_PORT -af $mybase/load.sql $dbname