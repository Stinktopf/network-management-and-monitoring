# Presentation only. Never execute text from the investigation guides.
function styled_command(s, prefix,    marker, before, comment) {
    if (match(s, /[[:space:]]+#/)) {
        marker = RSTART + RLENGTH - 1
        before = substr(s, 1, marker - 1)
        comment = substr(s, marker)
        return prefix command before reset gray comment reset
    }
    return prefix command s reset
}
NR == 1 { last_blank = 1 }
{
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
    if ($0 ~ /^\034/) {
        sub(/^\034/, "")
        print $0
        last_was_command = 0
        next
    }
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
