from StbTester.core.errors.DuplicateApiNamespaceError import \
    DuplicateApiNamespaceError

print "test2 imported"

def dumpApis(apis):
    s = ["Available apis:"]
    for value in apis.values():
        s.append("API: '%(ns)s', originalNS: '%(original_ns)s', name: '%(name)s', version: '%(version)s', module: '%(module)s', clazz: %(clazz)s, path: '%(path)s'."%value)
    return "\n".join(s)

#    Test requires that the following apis are available already, only: one of["ns", "name"] is mandatory.
#    The apis were previously defined on the cmdline OR in the default '*.conf' file.
#    NB: This will also stop Nose from being able to run discover test successfully if the apis are not available
availableApis = __requires__([{"name":"original-stbtester-api", "min":1, "max":1.0, "exact":1.0, "ns":"Velma"},           #@UndefinedVariable
                              {"name":"new-stbtester-api", "min":1, "max":1.0, "exact":1.0, "ns":"Daphne"}
                              ])
#    Print out the available apis to this test script.
print dumpApis(availableApis)

def test():
    #    __loads__
    assert Daphne.getStore()==None                                                      #@UndefinedVariable
    __loads__(["apis/new/NewApi1?ns=Daphne"], mode=2)                                   #@UndefinedVariable
    Daphne.store(123)                                                                   #@UndefinedVariable
    assert Daphne.getStore()==123                                                       #@UndefinedVariable
    try:
        Daphne.aDifferentMethod()                                                       #@UndefinedVariable
    except AttributeError, _e:
        assert True
    else:
        assert False
    __loads__(["apis/new/NewApi1?ns=Daphne"], mode=1)                                   #@UndefinedVariable
    assert Daphne.getStore()==123                                                       #@UndefinedVariable
    assert Daphne.aDifferentMethod()==1                                                 #@UndefinedVariable
    __loads__(["apis/new/NewApi2?ns=Daphne"], mode=0)                                   #@UndefinedVariable
    assert Daphne.aDifferentMethod()==2                                                 #@UndefinedVariable
    __loads__(["apis/new/NewApi3?ns=Daphne"], mode=-1)                                  #@UndefinedVariable
    assert Daphne.nor2()==3                                                             #@UndefinedVariable
    try:
        Daphne.aDifferentMethod()                                                       #@UndefinedVariable
    except AttributeError, _e:
        assert True
    else:
        assert False
    try:
        __loads__(["apis/new/NewApi1?ns=Daphne"], mode=-2)                                  #@UndefinedVariable
    except DuplicateApiNamespaceError:
        assert True
    else:
        assert False
    #    __injects__
    __injects__(["apis/new/NewApi4?ns=Daphne"], mode=0)                                   #@UndefinedVariable
    assert Daphne.nor2()==4                                                             #@UndefinedVariable
    try:
        Daphne.nor3()                                                                   #@UndefinedVariable
    except AttributeError, _e:
        assert True
    else:
        assert False
    __injects__(["apis/new/NewApi5?ns=Daphne"], mode=1)                                   #@UndefinedVariable
    assert Daphne.nor2()==4                                                             #@UndefinedVariable
    assert Daphne.nor3()==7                                                             #@UndefinedVariable

if __name__ == '__main__':
    #    Run the test, or use unittest.main() if defined a testClass(unittest.TestCase).
    test()
    #    NB: For Nose to run, --disallow_builtins (I think) must be: 'FALSE'.
#    unittest.main()
