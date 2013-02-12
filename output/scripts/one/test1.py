print "test1 imported"

def test():
    print "test1::test called"
    print "test1 __file__: ", __file__
    print "test1 __name__: ", __name__
    print "test1 __srcdir__: ", __srcdir__                  #@UndefinedVariable
    print "test1 __script_root__: ", __script_root__        #@UndefinedVariable

    __loads__(["apis/original/OriginalApi?clazz=TheApi?ns=mark"])        #@UndefinedVariable
    mark.press('15')                                        #@UndefinedVariable

    from output.scripts.four.test4 import test as test4
    #    and executing it's test, returning the result:
    return "-".join(["test1::test", test4()])

if __name__ == '__main__':
    test()
