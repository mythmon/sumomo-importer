export PYTHONPATH = .


default: sumomo.sql

out.dump.json: ./sumomomig/dump.py sumomomig/utils.py
	./sumomomig/dump.py

out.validate.json: sumomomig/validate.py out.dump.json sumomomig/utils.py
	./sumomomig/validate.py

out.uncollide.json: sumomomig/uncollide.py out.validate.json sumomomig/utils.py
	./sumomomig/uncollide.py

sumomo.sql: sumomomig/tosql.py out.uncollide.json sumomomig/utils.py
	./sumomomig/tosql.py

import: sumomo.sql
	mysql --show-warnings < sumomo.sql

clean:
	rm -f out.dump.json out.validate.json out.uncollide.json sumomo.sql


.PHONY: import default clean
