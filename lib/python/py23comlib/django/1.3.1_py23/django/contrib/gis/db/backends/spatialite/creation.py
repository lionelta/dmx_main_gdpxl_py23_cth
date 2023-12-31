from __future__ import print_function
from builtins import str
import os
from django.conf import settings
from django.core.cache import get_cache
from django.core.cache.backends.db import BaseDatabaseCache
from django.core.exceptions import ImproperlyConfigured
from django.db.backends.sqlite3.creation import DatabaseCreation

class SpatiaLiteCreation(DatabaseCreation):

    def create_test_db(self, verbosity=1, autoclobber=False):
        """
        Creates a test database, prompting the user for confirmation if the
        database already exists. Returns the name of the test database created.

        This method is overloaded to load up the SpatiaLite initialization
        SQL prior to calling the `syncdb` command.
        """
        # Don't import django.core.management if it isn't needed.
        from django.core.management import call_command

        test_database_name = self._get_test_db_name()

        if verbosity >= 1:
            test_db_repr = ''
            if verbosity >= 2:
                test_db_repr = " ('%s')" % test_database_name
            print("Creating test database for alias '%s'%s..." % (self.connection.alias, test_db_repr))

        self._create_test_db(verbosity, autoclobber)

        self.connection.close()
        self.connection.settings_dict["NAME"] = test_database_name

        # Confirm the feature set of the test database
        self.connection.features.confirm()

        # Need to load the SpatiaLite initialization SQL before running `syncdb`.
        self.load_spatialite_sql()

        # Report syncdb messages at one level lower than that requested.
        # This ensures we don't get flooded with messages during testing
        # (unless you really ask to be flooded)
        call_command('syncdb',
            verbosity=max(verbosity - 1, 0),
            interactive=False,
            database=self.connection.alias,
            load_initial_data=False)

        # We need to then do a flush to ensure that any data installed by
        # custom SQL has been removed. The only test data should come from
        # test fixtures, or autogenerated from post_syncdb triggers.
        # This has the side effect of loading initial data (which was
        # intentionally skipped in the syncdb).
        call_command('flush',
            verbosity=max(verbosity - 1, 0),
            interactive=False,
            database=self.connection.alias)

        # One effect of calling syncdb followed by flush is that the id of the
        # default site may or may not be 1, depending on how the sequence was
        # reset.  If the sites app is loaded, then we coerce it.
        from django.db.models import get_model
        Site = get_model('sites', 'Site')
        if Site is not None and Site.objects.using(self.connection.alias).count() == 1:
            Site.objects.using(self.connection.alias).update(id=settings.SITE_ID)

        from django.core.cache import get_cache
        from django.core.cache.backends.db import BaseDatabaseCache
        for cache_alias in settings.CACHES:
            cache = get_cache(cache_alias)
            if isinstance(cache, BaseDatabaseCache):
                from django.db import router
                if router.allow_syncdb(self.connection.alias, cache.cache_model_class):
                    call_command('createcachetable', cache._table, database=self.connection.alias)

        # Get a cursor (even though we don't need one yet). This has
        # the side effect of initializing the test database.
        cursor = self.connection.cursor()

        return test_database_name

    def sql_indexes_for_field(self, model, f, style):
        "Return any spatial index creation SQL for the field."
        from django.contrib.gis.db.models.fields import GeometryField

        output = super(SpatiaLiteCreation, self).sql_indexes_for_field(model, f, style)

        if isinstance(f, GeometryField):
            gqn = self.connection.ops.geo_quote_name
            qn = self.connection.ops.quote_name
            db_table = model._meta.db_table

            output.append(style.SQL_KEYWORD('SELECT ') +
                          style.SQL_TABLE('AddGeometryColumn') + '(' +
                          style.SQL_TABLE(gqn(db_table)) + ', ' +
                          style.SQL_FIELD(gqn(f.column)) + ', ' +
                          style.SQL_FIELD(str(f.srid)) + ', ' +
                          style.SQL_COLTYPE(gqn(f.geom_type)) + ', ' +
                          style.SQL_KEYWORD(str(f.dim)) + ', ' +
                          style.SQL_KEYWORD(str(int(not f.null))) +
                          ');')

            if f.spatial_index:
                output.append(style.SQL_KEYWORD('SELECT ') +
                              style.SQL_TABLE('CreateSpatialIndex') + '(' +
                              style.SQL_TABLE(gqn(db_table)) + ', ' +
                              style.SQL_FIELD(gqn(f.column)) + ');')

        return output

    def load_spatialite_sql(self):
        """
        This routine loads up the SpatiaLite SQL file.
        """
        # Getting the location of the SpatiaLite SQL file, and confirming
        # it exists.
        spatialite_sql = self.spatialite_init_file()
        if not os.path.isfile(spatialite_sql):
            raise ImproperlyConfigured('Could not find the required SpatiaLite initialization '
                                       'SQL file (necessary for testing): %s' % spatialite_sql)

        # Opening up the SpatiaLite SQL initialization file and executing
        # as a script.
        sql_fh = open(spatialite_sql, 'r')
        try:
            cur = self.connection._cursor()
            cur.executescript(sql_fh.read())
        finally:
            sql_fh.close()

    def spatialite_init_file(self):
        # SPATIALITE_SQL may be placed in settings to tell GeoDjango
        # to use a specific path to the SpatiaLite initilization SQL.
        return getattr(settings, 'SPATIALITE_SQL',
                       'init_spatialite-%s.%s.sql' %
                       self.connection.ops.spatial_version[:2])
