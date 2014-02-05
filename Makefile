default: sumomo.sql

dump.out.json: dump.py utils.py
	./dump.py

validate.out.json: validate.py dump.out.json utils.py
	./validate.py

uncollide.out.json: uncollide.py validate.out.json utils.py
	./uncollide.py

sumomo.sql: tosql.py uncollide.out.json utils.py
	./tosql.py

import: sumomo.sql
	mysql --show-warnings < sumomo.sql

clean:
	rm -f dump.out.json validate.out.json uncollide.out.json sumomo.sql


.PHONY: import default clean
