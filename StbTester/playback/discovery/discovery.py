'''
Created on 26 Nov 2012

@author: francis
'''

import nose
import os
import pickle
import sys
from StbTester.playback.TVector import TVector
from StbTester.apis.ApiFactory import ApiFactory

def discover(args):
    result = []
    if args.nose==True:
        #    Now use nose to 'discover' tests:
        oldcwd = os.getcwd()
        try:
            testRoot = args.script_root
            sys.path.append(testRoot)
            tmpFile = os.path.realpath("test_cases.txt")
            cargs=["", "-v" , "--collect-only", "--exe", "--with-id", "--id-file=%(F)s"%{"F":tmpFile}]
            try:
                api = ApiFactory.emptyApi(args.api_type)
                __builtins__["api"] = api
                result = nose.run(defaultTest=testRoot, argv=cargs)
            except Exception, _e:
                pass
            else:
                if result is True:
                    args.script = []
                    #    Now query the selector:
                    s = pickle.loads(file(tmpFile).read())["ids"]
                    if os.path.exists(tmpFile):
                        os.remove(tmpFile)
                    for testCase in s.values():
                        filepath, relativeModuleSignature, test = testCase
                        testPath = filepath.strip()
                        if test is not None:
                            testName = test.strip()
                            #    Now we have: testPath, relativeModuleSignature, test
                            args.script.append(TVector(filename=testPath, moduleSig=relativeModuleSignature, methodName=testName, root=args.script_root, nose=True))
        finally:
            del __builtins__["api"]
            os.chdir(oldcwd)
    return result
