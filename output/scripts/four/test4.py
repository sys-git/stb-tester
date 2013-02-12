
def test():
    print "test4::test called"
    print "test4 __file__: ", __file__
    print "test4 __name__: ", __name__
    print "test4 __srcdir__: ", __srcdir__                      #@UndefinedVariable
    print "test4 __script_root__: ", __script_root__            #@UndefinedVariable

    __loads__(["apis/original/OriginalApi?clazz=TheApi?ns=jason"])        #@UndefinedVariable
    jason.press('15')                                           #@UndefinedVariable
    return "test4::test"

if __name__ == '__main__':
    test()
