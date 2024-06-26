# Installation

This section describes the installation steps.

## building binary module

Simply run `make` at the top of the source tree, then `make install` as an
appropriate user. The `PATH` environment variable should be set properly for
the target PostgreSQL for this process.

    $ tar xzvf pg_hint_plan-1.x.x.tar.gz
    $ cd pg_hint_plan-1.x.x
    $ make
    $ su
    # make install

## Loading `pg_hint_plan`

Basically `pg_hint_plan` does not require `CREATE EXTENSION`. Simply loading it
by `LOAD` command will activate it and of course you can load it globally by
setting `shared_preload_libraries` in `postgresql.conf`. Or you might be
interested in `ALTER USER SET`/`ALTER DATABASE SET` for automatic loading for
specific sessions.

```sql
postgres=# LOAD 'pg_hint_plan';
LOAD
postgres=#
```

Do `CREATE EXTENSION` and `SET pg_hint_plan.enable_hint_tables TO on` if you
are planning to use the hint table.
