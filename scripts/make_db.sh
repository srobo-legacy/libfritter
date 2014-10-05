#!/bin/sh
DB_PATH="$1"
if [ -z "$DB_PATH" ]
then
    name=`basename "$0"`
    echo "Usage: $name path/to/database.db"
    exit 1
fi
echo "Creating a libfritter compatible sqlite database at '$DB_PATH'."
sqlite3 "$DB_PATH" "CREATE table IF NOT EXISTS outbox (id INTEGER PRIMARY KEY ASC AUTOINCREMENT,\
                                                       toaddr                VARCHAR(256),\
                                                       template_name         VARCHAR(256),\
                                                       template_vars_json    VARCHAR(512),\
                                                       request_time          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                                       last_error            VARCHAR(256),\
                                                       retry_count           INTEGER DEFAULT 0,\
                                                       sent_time             TIMESTAMP);"
exit $?
