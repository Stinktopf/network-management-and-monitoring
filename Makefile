SHELL := /bin/bash
.DEFAULT_GOAL := help
GUIDE_SCENARIO = $(or $(SCENARIO),$(shell cat .scenario 2>/dev/null || echo networking))

.PHONY: help setup doctor pull networking operations automation monitoring reset enter \
        inspect status next hint solution test healthy fault-routing clear-routing fault-link clear-link \
        traffic-10mbit traffic-25mbit traffic-40mbit traffic-50mbit traffic-60mbit traffic-75mbit traffic-status traffic-diagnostics traffic-burst-40mbit traffic-stop \
        netbox-token netbox-reset diagnostics course-check down clean ui slides check

help:
	@bash scripts/help.sh

setup:
	bash scripts/setup.sh

doctor:
	bash scripts/doctor.sh
pull:
	bash scripts/ensure-images.sh --all

networking:
	bash scripts/start-scenario.sh networking
operations:
	bash scripts/start-scenario.sh operations
automation:
	bash scripts/start-scenario.sh automation
monitoring:
	bash scripts/start-scenario.sh monitoring
reset:
	bash scripts/reset.sh

enter:
	@test -n "$(NODE)" || { echo 'usage: make enter NODE=<device-fqdn>'; exit 2; }
	bash scripts/enter.sh "$(NODE)"

inspect:
	containerlab inspect -t lab.clab.yml
status:
	bash scripts/status.sh
next:
	@bash scripts/next-steps.sh "$(GUIDE_SCENARIO)" "$(STEP)" task
hint:
	@bash scripts/next-steps.sh "$(GUIDE_SCENARIO)" "$(STEP)" hint
solution:
	@bash scripts/next-steps.sh "$(GUIDE_SCENARIO)" "$(or $(STEP),all)" solution
test:
	bash scripts/test.sh
healthy:
	bash scripts/healthy.sh

fault-routing:
	bash scripts/fault-routing.sh
clear-routing:
	bash scripts/clear-routing.sh
fault-link:
	bash scripts/fault-link.sh
clear-link:
	bash scripts/clear-link.sh
traffic-10mbit:
	bash scripts/traffic.sh set 10M
traffic-25mbit:
	bash scripts/traffic.sh set 25M
traffic-40mbit:
	bash scripts/traffic.sh set 40M
traffic-50mbit:
	bash scripts/traffic.sh set 50M
traffic-60mbit:
	bash scripts/traffic.sh set 60M
traffic-75mbit:
	bash scripts/traffic.sh set 75M
traffic-status:
	bash scripts/traffic.sh status
traffic-diagnostics:
	bash scripts/traffic-diagnostics.sh
traffic-burst-40mbit:
	bash scripts/traffic.sh burst 40M
traffic-stop:
	bash scripts/traffic.sh stop

netbox-token:
	@cat .state/netbox-token
netbox-reset:
	bash scripts/netbox-reset.sh
diagnostics:
	bash scripts/diagnostics.sh manual
course-check:
	bash scripts/course-check.sh
ui:
	code .
down:
	bash scripts/down.sh
clean:
	bash scripts/clean.sh

slides:
	./scripts/export-slides.sh all

check:
	python3 scripts/check-source.py
