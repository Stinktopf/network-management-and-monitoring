# Join hard-wrapped guide prose into paragraphs before terminal rendering.
function trim(s) {
    sub(/^[[:space:]]+/, "", s)
    sub(/[[:space:]]+$/, "", s)
    return s
}
function emit_paragraph(s,    words, count, i, word, line, width, continuation) {
    if (s == "") return
    count = split(s, words, /[[:space:]]+/)
    width = 78
    continuation = words[1] == "-" ? "  " : ""
    line = ""
    for (i = 1; i <= count; i++) {
        word = words[i]
        if (line == "") line = word
        else if (length(line) + 1 + length(word) <= width) line = line " " word
        else {
            print line
            line = continuation word
        }
    }
    if (line != "") print line
}
function flush_paragraph() {
    if (paragraph == "") return
    if (previous == "command" || previous == "data") print ""
    emit_paragraph(paragraph)
    paragraph = ""
    previous = "prose"
}

{
    if ($0 == "") {
        flush_paragraph()
        print ""
        previous = "blank"
        next
    }

    if ($0 ~ /^(Investigation commands|Worked answer|[1-9] )/ ||
        $0 ~ /^(Inspect:|Decision:|Expected:|Expected initial evidence:|Preconditions:)/ ||
        $0 ~ /^(WSL repository:|WSL:|Start in WSL:|Inside |In the |In WSL:|Router CLI)/ ||
        (paragraph == "" && $0 ~ /:$/)) {
        flush_paragraph()
        print $0
        previous = "heading"
        next
    }

    if ($0 ~ /^  (make |show |info |enter |delete |set |discard |commit|diff$|quit$|exit$|date |ip |ping |dig |traceroute |curl |gnmic |cat |tail |mkdir |cp |jq |getent |hostname$|ssh |[A-Z_][A-Z0-9_]*=)/) {
        flush_paragraph()
        print $0
        previous = "command"
        next
    }
    if ($0 ~ /^    / && previous == "command") {
        print $0
        next
    }

    if ($0 ~ /^  /) {
        if (paragraph ~ /^- /) {
            paragraph = paragraph " " trim($0)
        } else {
            flush_paragraph()
            print $0
            previous = "data"
        }
        next
    }

    if ($0 ~ /^- /) {
        flush_paragraph()
        paragraph = $0
        next
    }
    if (paragraph == "") paragraph = trim($0)
    else paragraph = paragraph " " trim($0)
}

END { flush_paragraph() }
