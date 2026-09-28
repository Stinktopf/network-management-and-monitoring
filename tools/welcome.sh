# shellcheck shell=bash
case $- in
  *i*) ;;
  *) return 0 ;;
esac

if [[ -t 1 && -z ${NO_COLOR:-} ]]; then
  _r=$'\033[0m'; _b=$'\033[1m'; _c=$'\033[36m'; _g=$'\033[32m'; _d=$'\033[2m'
else
  _r='' _b='' _c='' _g='' _d=''
fi
printf '\n%s%sAI5049 · operations01.bob1.reefnet.test%s\n' "$_c" "$_b" "$_r"
printf '%sOperator workstation · BOB1%s\n\n' "$_d" "$_r"
printf '  %sReefNet%s      edge01.bob1.reefnet.test · edge02.bob1.reefnet.test\n' "$_b" "$_r"
printf '  %sCustomer%s     edge01.bob1.oceanresearch.test\n' "$_b" "$_r"
printf '  %sUpstreams%s    edge01.bob1.lagoontransit.test · edge01.bob1.pacifictransit.test\n' "$_b" "$_r"
printf '  %sCredentials%s  admin / NokiaSrl1!\n' "$_b" "$_r"
printf '  %sNetBox token%s TOKEN=$(cat /state/netbox-token)\n' "$_b" "$_r"
printf '\n%sTry SSH%s\n  ssh edge01.bob1.reefnet.test\n' "$_g" "$_r"
printf '\n%sgNMI client: gnmic%s\n' "$_g" "$_r"
printf '  gnmic -a edge01.bob1.reefnet.test:57400 -u admin -p '\''NokiaSrl1!'\'' --skip-verify --encoding json_ietf get --path '\''/interface[name=ethernet-1/1]/oper-state'\''\n\n'
unset _r _b _c _g _d
