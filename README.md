Get data from a SUMOMO DB, and insert it into a SUMO database.

This happens in a few stages.

### dump.py

This loads all the needed (and a lot of unneeded) data from the SUMOMO
database, and writes it to dump.out.json.

### validate.py

This reads in dump.out.json and goes through all the data and prints some
statistics about the data'a internally consistency. Probably mostly vistigial
at this point. After it is done it writes the data to validate.out.json.

### uncollide.py

This reads in validate.out.json and handles renaming documents and images
that collide with SUMO documents and images, and rewriting documents and images
to use the new names. Aftar all that, it writes the modifed data to
uncollide.out.json.

### tosql.py

This reads in uncollide.out.json and converts it into raw SQL statements, which
it write to sumomo.sql.

# Makefile

There is a Makefile that has all the stages in the pipeline declared. The
default rule is to build sumomo.sql, which means it runs all the above steps.
It also defines some phony methods:

### clean

Removes all generated files.

### import

Generates sumomo.sql, and then imports it into mysql. Will print any warnings
mysql generates.

# Notes

* Currently, the SQL file begins with `BEGIN TRANSACTION` and ends with
  `ROLLBACK`, which means it will have no effect (in theory).

  To change this, edit tosql.py and change the ROLLBACK line to COMMIT. **Be sure
  you want to import the data before you do this. There is no going back.**

* This only works with Python3 right now. It could probably work on Python2,
  but unicode is being funky.
