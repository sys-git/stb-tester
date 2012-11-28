api.press('15')
api.wait_for_match('0000-15-complete.png')
api.press('10')
api.wait_for_match('0001-10-complete.png')
api.press('15')
#wait_for_match('0002-1-complete.png')
api.wait_for_motion(10)#'0002-1-complete.png')
print "done!"