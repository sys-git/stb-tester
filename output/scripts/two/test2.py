
print "test2 imported"

def test():
    print "test2::test called"
    print "test2 __file__: ", __file__
    print "test2 __name__: ", __name__
    print "test2 __srcdir__: ", __srcdir__                          #@UndefinedVariable
    print "test2 __script_root__: ", __script_root__                #@UndefinedVariable

    __loads__(["apis/original/OriginalApi?clazz=TheApi?ns=Fred"])   #@UndefinedVariable
    Fred.press('15')                                                #@UndefinedVariable
    Fred.sleep(1)                                                   #@UndefinedVariable
    #   Importing a nested test module:
    from output.scripts.one.test1 import test as test1
    #    and executing it's test, returning the result:
    return "-".join(["test2::test", test1()])

if __name__ == '__main__':
    test()
