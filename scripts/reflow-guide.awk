# Join hard-wrapped guide prose into paragraphs before terminal rendering.
function trim(s) {
    sub(/^[[:space:]]+/, "", s)
    sub(/[[:space:]]+$/, "", s)
    return s
}
function emit_paragraph(s, label,    words, count, i, word, line, width, continuation, mark) {
    if (s == "") return
    count = split(s, words, /[[:space:]]+/)
    width = 78
    continuation = words[1] == "-" ? "  " : ""
    line = ""
    # A labelled first line (Inspect:, Decision:) stays unmarked so the renderer bolds its label.
    mark = label ? "" : "\034"
    for (i = 1; i <= count; i++) {
        word = words[i]
        if (line == "") line = word
        else if (length(line) + 1 + length(word) <= width) line = line " " word
        else {
            print mark line
            mark = "\034"
            line = continuation word
        }
    }
    if (line != "") print mark line
}
# Wrap a long lead-in. Only its last line stays a heading for the renderer.
function emit_lead(s,    words, count, i, line) {
    count = split(s, words, /[[:space:]]+/)
    line = ""
    for (i = 1; i <= count; i++) {
        if (line == "") line = words[i]
        else if (length(line) + 1 + length(words[i]) <= 78) line = line " " words[i]
        else {
            print "\034" line
            line = words[i]
        }
    }
    print line
}
function flush_paragraph() {
    if (paragraph == "") return
    if (previous == "command" || previous == "data") print ""
    # Mark prose so a wrapped fragment cannot become a heading in the renderer.
    # Keep command lead-ins intact. The terminal can wrap the full heading.
    if (paragraph ~ /^(Inspect:|Decision:|Expected:|Expected initial evidence:|Preconditions:) /) {
        emit_paragraph(paragraph, 1)
    }
    else if (paragraph ~ /:$/) {
        # Wrap the leading sentences and keep only the final lead-in sentence intact.
        lead = paragraph
        if (length(paragraph) > 78 && match(paragraph, /.*[.?!] /)) {
            emit_paragraph(substr(paragraph, 1, RLENGTH - 1))
            lead = substr(paragraph, RLENGTH + 1)
        }
        if (length(lead) > 78) emit_lead(lead)
        else print lead
    }
    else emit_paragraph(paragraph)
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

    if ($0 ~ /^(Inspect:|Decision:|Expected:|Expected initial evidence:|Preconditions:) ./) {
        flush_paragraph()
        paragraph = $0
        next
    }
    if ($0 ~ /^(Investigation commands|Worked answer|[1-9] )/ ||
        $0 ~ /^(Inspect:|Decision:|Expected:|Expected initial evidence:|Preconditions:)/ ||
        $0 ~ /^(WSL repository:|WSL:|Start in WSL:|Inside |In the |In WSL:|Router CLI)/ ||
        (paragraph == "" && $0 ~ /:$/)) {
        flush_paragraph()
        if (length($0) > 78 && $0 ~ /:$/) emit_lead($0)
        else print $0
        previous = "heading"
        next
    }

    if ($0 ~ /^  (make |show |info |enter |delete |set |discard |commit|diff$|quit$|exit$|date |ip |ping |dig |traceroute |tracepath |mtr |curl |gnmic |cat |tail |mkdir |cp |jq |getent |hostname$|ssh |[A-Z_][A-Z0-9_]*=|[a-z][a-z0-9 -]*(, [a-z][^,]*)+$)/) {
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
