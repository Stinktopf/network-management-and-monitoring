# Presentation only. Never execute text from the guides or command reference.
function trim(s) { sub(/^[[:space:]]+/, "", s); sub(/[[:space:]]+$/, "", s); return s }
function inline(s,    out, token, marker, style, start, finish) {
    out = ""
    while (match(s, /`[^`]+`|\*\*[^*]+\*\*/)) {
        out = out substr(s, 1, RSTART - 1)
        token = substr(s, RSTART, RLENGTH)
        marker = substr(token, 1, 1) == "`" ? 1 : 2
        style = marker == 1 ? command : bold
        out = out style substr(token, marker + 1, length(token) - 2 * marker) reset
        s = substr(s, RSTART + RLENGTH)
    }
    return out s
}
function plain(s) { gsub(/`|\*\*/, "", s); return s }
function table_flush(    i, j, value, pad) {
    if (!rows) return
    for (i = 1; i <= rows; i++) {
        printf "  "
        for (j = 1; j <= columns; j++) {
            value = cells[i, j]
            if (i == 1) printf "%s%s%s", bold, plain(value), reset
            else printf "%s", inline(value)
            pad = widths[j] - length(plain(value)) + 3
            if (j < columns) printf "%*s", pad, ""
        }
        printf "\n"
    }
    delete cells; delete widths; rows = 0; columns = 0
}
mode == "guide" {
    if ($0 ~ /^[0-9]+ / || $0 == "Investigation commands" || $0 == "Worked answer")
        print blue bold $0 reset
    else if ($0 ~ /^(WSL|Start in WSL|Inside |In the |In WSL|Router CLI)/)
        print cyan bold $0 reset
    else if ($0 ~ /^  (make |show |info |enter |delete |commit|diff$|quit$|exit$|date |ip |ping |dig |traceroute |curl |gnmic |cat |tail |mkdir |cp |jq |[A-Z_][A-Z0-9_]*=)/)
        print command $0 reset
    else print $0
    next
}
NR == 1 && /^---$/ { metadata = 1; next }
metadata && /^---$/ { metadata = 0; next }
metadata { next }
/^```/ { table_flush(); fenced = !fenced; next }
fenced { print "  " command $0 reset; next }
/^\|/ {
    if ($0 ~ /^\|[ :|\-]+$/) next
    line = $0; sub(/^\|/, "", line); sub(/\|$/, "", line)
    n = split(line, parts, "|"); rows++; columns = n
    for (j = 1; j <= n; j++) {
        cells[rows, j] = trim(parts[j])
        width = length(plain(cells[rows, j]))
        if (width > widths[j]) widths[j] = width
    }
    next
}
{ table_flush() }
/^---$/ { print gray "--------------------------------------------------------------------" reset; next }
/^# / { print blue bold arrow reset " " bold substr($0, 3) reset; next }
/^## / { print bold substr($0, 4) reset; next }
{ print inline($0) }
END { table_flush() }
