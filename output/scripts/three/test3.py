print "test3 imported"

def test():
    r"""
    test-id: 102
    """
    #    use builtins as normal (unless --disallow-builtins is provided).
    print "test3::test called"
    #    use import as per normal (unless --disallow-builtins is provided).
    import os
    print "cwd: ", os.getcwd()

    #    The variables available to a test script:
    print "test3 __file__: ", __file__
    print "test3 __name__: ", __name__
    print "test3 __srcdir__: ", __srcdir__
    print "test3 __script_root__: ", __script_root__

    #    the 'api' is always available:
    print "api: ", api
    api.press('15')

    #   Importing a different test module:
    from output.scripts.two.test2 import test as test2
    #    and executing it's test, returning the result:
    result = test2()
    print "nested test result: ", result

    #    Execute script actions as normal:
    api.press('15')
    api.wait_for_match('0000-15-complete.png')
    api.press('10')
    api.wait_for_match('0001-10-complete.png')
    api.press('1')
    api.wait_for_motion()

if __name__ == '__main__':
    test()
