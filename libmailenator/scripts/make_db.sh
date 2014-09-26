sqlite3 db/nemesis.sqlite "CREATE table IF NOT EXISTS outbox (id INTEGER PRIMARY KEY ASC AUTOINCREMENT,\
                                                              toaddr                VARCHAR(256),\
                                                              template_name         VARCHAR(256),\
                                                              template_vars_json    VARCHAR(512),\
                                                              request_time          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                                              last_error            VARCHAR(256),\
                                                              retry_count           INTEGER DEFAULT 0,\
                                                              sent_time             TIMESTAMP);"
