# Import/Export

Baby Buddy uses the [django-import-export application](https://django-import-export.readthedocs.io/)
to provide import and export functionality.

## Export

Export actions are accessible from Baby Buddy's "Database Admin" area (the
Django admin interface). For example, to export all diaper change entries from
Baby Buddy as an Excel file:

1. Log in as a user with "staff" access.

1. From the user menu, click "Database Admin" under the "Site" heading.

1. Click "Diaper Changes" in the list of data types.

1. Click the "Export" button above the filters list on the right side of the
   screen.

1. Select the "xlxs" format and click "Submit"

Note: any applied filters will also filter the exported entries. Alternatively,
on the Diaper Change list screen (step 3 above), it is possible to select one
or many individual records and select "Export selected Diaper Changes" from the
"Actions" list.

## Import

Import actions are accessible from Baby Buddy's "Database Admin" area (the
Django admin interface). From the list of entry types in the Database Admin,
select the type to import and click the "Import" button on the list page. The
import screen for a particular type will list the fields generally expected to
be present for an import. Multiple file types -- including csv, xlsx, etc. --
are supported for the import.

The import pages do not provide _detailed_ information about the required data
and formats. All rows will be checked for errors on import and any issues will
be reported on screen and will need to be resolved before the import can be
performed.

See the [example import files](https://github.com/babybuddy/babybuddy/tree/master/core/tests/import)
used for tests to get an idea of the expected data format.
