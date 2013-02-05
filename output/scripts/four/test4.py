
def test():
    print "test4::test called"
    print "test4 __file__: ", __file__
    print "test4 __name__: ", __name__
    print "test4 __srcdir__: ", __srcdir__
    print "test4 __script_root__: ", __script_root__
    api.press('15')
    return "test4::test"

if __name__ == '__main__':
    test()
