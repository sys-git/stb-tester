
print "test2.3 imported"

def test23():
    #    This test uses apis already defined by the caller (test or cmdline)
    print "test2::test called"
    print "test2 __file__: ", __file__
    print "test2 __name__: ", __name__
    print "test2 __srcdir__: ", __srcdir__                  #@UndefinedVariable
    print "test2 __script_root__: ", __script_root__        #@UndefinedVariable
    Velma.press('15')                                       #@UndefinedVariable

    __loads__(["apis/new/NewerApi?ns=scooby"])              #@UndefinedVariable
    scooby.sleep(1)                                         #@UndefinedVariable
    return "-".join(["test3::test23"])

if __name__ == '__main__':
    test23()
