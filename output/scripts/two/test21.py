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
    r"""
    @summary: The actual test-case
    @attention: Method name should contain 'test' for Nose to find it, or use a testClass(unittest.TestCase).
    @test-id: 101
    """
    i = 0
    #    Dynamically load an api from a path from the file-system (either relative or absolute):
    __loads__(["apis/new/NewerApi?ns=scooby"])      #@UndefinedVariable
    #    No exception was thrown so the api is now loaded.
    availableApis = __requires__({"name":"newer-stbtester-api", "min":1, "max":1.0, "exact":1.0, "ns":"scooby"})        #@UndefinedVariable
    #    This should include the newly added api:
    print dumpApis(availableApis)
    #    Use the newly imported api with ns: 'scooby':
    scooby.scrappy()                                #@UndefinedVariable

    #   Importing a different test module:
    from output.scripts.two.test3 import test23
    #    Call the imported test function:
    print test23()

    #    Attempt duplicate api loading, api's are duplicates based only on their NS.
    __loads__(["apis/new/NewApi2?ns=shaggy"])  #@UndefinedVariable

    while True:
        #    Use existing api with name 'original-stbtester-api' and ns: 'Velma':
        Velma.sleep(1)                              #@UndefinedVariable
        if i>2:
            #    Attempt duplicate api loading, api's are duplicates based only on their NS.
            __loads__(["apis/new/NewerApi?ns=shaggy"], -2)  #@UndefinedVariable
        if i>3:
            raise Exception("hello.world!")
        i += 1
        #    Use existing api with name 'new-stbtester-api' and ns: 'Daphne':
        Daphne.stuff("hello.world!")                 #@UndefinedVariable
        #    Use newly imported api with ns: 'scooby':
        scooby.sleep(1)                             #@UndefinedVariable
        scooby.scrappy()                            #@UndefinedVariable
        print dumpApis(__requires__())              #@UndefinedVariable
        #    Use newly imported api with ns: 'shaggy':
        shaggy.sleep(1)                             #@UndefinedVariable

if __name__ == '__main__':
    #    Run the test, or use unittest.main() if defined a testClass(unittest.TestCase).
    test()
    #    NB: For Nose to run, --disallow_builtins (I think) must be: 'FALSE'.
#    unittest.main()
