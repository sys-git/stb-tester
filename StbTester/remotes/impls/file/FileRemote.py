'''
Created on 31 Oct 2012

@author: YouView
'''

from StbTester.remotes.impls.BaseRemote import BaseRemote

class FileRemote(BaseRemote):
    @staticmethod
    def listen(filename, debugger):
        """
        @summary: A generator that returns lines from the file given by filename.
        
        Unfortunately treating a file as a iterator doesn't work in the case of
        interactive input, even when we provide bufsize=1 (line buffered) to the
        call to open() so we have to have this function to work around it.
        """
        f = open(filename, 'r')
        if filename == '/dev/stdin':
            debugger.debug('Waiting for keypresses from standard input...\n')
        while True:
            line = f.readline()
            if line == '':
                f.close()
                raise StopIteration
            yield line.rstrip()
