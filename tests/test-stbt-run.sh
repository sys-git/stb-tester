# Run with ./run-tests.sh

test_wait_for_match() {
    cat > "$scratchdir/test.py" <<-EOF
	wait_for_match("videotestsrc-redblue.png", consecutive_matches=24)
	EOF
    stbt-run "$scratchdir/test.py"
}

test_wait_for_match_no_match() {
    cat > "$scratchdir/test.py" <<-EOF
	wait_for_match("videotestsrc-bw-flipped.png", timeout_secs=1)
	EOF
    rm -f screenshot.png
    ! stbt-run "$scratchdir/test.py" &&
    [ -f screenshot.png ]
}

test_wait_for_match_changing_template() {
    # Tests that we can change the image given to templatematch.
    # Also tests the remote-control infrastructure by using the null control.
    cat > "$scratchdir/test.py" <<-EOF
	wait_for_match("videotestsrc-redblue.png", consecutive_matches=24)
	press("MENU")
	wait_for_match("videotestsrc-bw.png", consecutive_matches=24)
	press("OK")
	wait_for_match("videotestsrc-redblue.png", consecutive_matches=24)
	EOF
    stbt-run "$scratchdir/test.py"
}