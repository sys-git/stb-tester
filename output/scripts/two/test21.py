print "test2 imported"

def test():
    r"""
    @test-id: 101
    """
    i = 0
    while True:
        api.sleep(1)
        if i>3:
            raise Exception("hello.world!")
        i += 1

if __name__ == '__main__':
    test()