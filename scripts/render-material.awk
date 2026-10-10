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
function styled_command(s, prefix,    marker, before, comment) {
    if (match(s, /[[:space:]]+#/)) {
        marker = RSTART + RLENGTH - 1
        before = substr(s, 1, marker - 1)
        comment = substr(s, marker)
        return prefix command before reset gray comment reset
    }
    return prefix command s reset
}
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
mode == "guide" && NR == 1 { last_blank = 1 }
mode == "guide" {
    if ($0 == "") {
        if (skip_heading_gap) {
            skip_heading_gap = 0
            last_blank = 0
            tight_after_heading = 1
            next
        }
        if (!last_blank) pending_blank = 1
        last_blank = 1
        last_was_command = 0
        next
    }
    had_heading = skip_heading_gap || tight_after_heading
    skip_heading_gap = 0
    tight_after_heading = 0
    if (pending_blank) {
        if (!had_heading) print ""
        pending_blank = 0
    }
    had_blank = last_blank
    last_blank = 0
    if ($0 ~ /^[1-9] /) {
        if (!had_blank) print ""
        print blue bold $0 reset
        print ""
        last_blank = 1
        last_was_command = 0
    }
    else if ($0 == "Investigation commands") {
        if (!had_blank) print ""
        print blue bold $0 reset
        last_blank = 0
        last_was_command = 0
        skip_heading_gap = 1
    }
    else if ($0 == "Worked answer") {
        if (!had_blank) print ""
        print blue bold $0 reset
        last_blank = 0
        last_was_command = 0
        skip_heading_gap = 1
    }
    else if ($0 ~ /^(Inspect:|Decision:|Expected:|Expected initial evidence:|Preconditions:)/) {
        if (!had_blank && !had_heading) print ""
        match($0, /^[^:]+:/)
        print bold substr($0, 1, RLENGTH) reset substr($0, RLENGTH + 1)
        last_was_command = 0
    }
    else if ($0 ~ /^(WSL repository:|WSL:|Start in WSL:|Inside |In the |In WSL:|Router CLI)/) {
        if (!had_blank && !had_heading) print ""
        print cyan bold $0 reset
        last_blank = 0
        last_was_command = 0
        skip_heading_gap = 1
    }
    else if ($0 ~ /:$/) {
        if (!had_blank && !had_heading) print ""
        print cyan bold $0 reset
        last_blank = 0
        last_was_command = 0
        skip_heading_gap = 1
    }
    else if (last_was_command && $0 ~ /^    /) {
        print styled_command(substr($0, 3), "")
        last_was_command = 1
    }
    else if ($0 ~ /^  (make |show |info |enter |delete |set |discard |commit|diff$|quit$|exit$|date |ip |ping |dig |traceroute |curl |gnmic |cat |tail |mkdir |cp |jq |getent |hostname$|ssh |[A-Z_][A-Z0-9_]*=)/) {
        if (!had_blank && !last_was_command && !had_heading) print ""
        print styled_command(substr($0, 3), "")
        last_was_command = 1
    }
    else print $0
    if ($0 !~ /^(WSL repository:|WSL:|Start in WSL:|Inside |In the |In WSL:|Router CLI|Investigation commands|Worked answer|[1-9] )/ && $0 !~ /:$/) last_blank = 0
    next
}
NR == 1 && /^---$/ { metadata = 1; next }
metadata && /^---$/ { metadata = 0; next }
metadata { next }
/^```/ { table_flush(); fenced = !fenced; next }
fenced { print styled_command($0, "  "); next }
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
