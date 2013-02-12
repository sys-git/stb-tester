'''
Created on 26 Nov 2012

@author: francis
'''

from StbTester.apis.ApiComparitor import ApiComparitor
from StbTester.apis.ApiFactory import ApiFactory
from StbTester.playback.TVector import TVector
import nose
import os
import pickle
import sys

def discover(args):
    result = []
    if args.nose==True:
        #    Now use nose to 'discover' tests:
        oldcwd = os.getcwd()
        NSs = ["__requires__"]
        try:
            testRoot = args.script_root
            sys.path.append(testRoot)
            tmpFile = os.path.realpath("test_cases.txt")
            cargs=["", "-v" , "--collect-only", "--exe", "--with-id", "--id-file=%(F)s"%{"F":tmpFile}]
            try:
                apids = []
                for apiType in args.api_types:
                    apid = ApiFactory.emptyApi(apiType)
                    apids.append(apid)
                    api = apid.api()
                    NS = api.NAMESPACE
                    NSs.append(NS)
                    __builtins__[NS] = api
                __builtins__["__requires__"] = ApiComparitor(apids)
                result = nose.run(defaultTest=testRoot, argv=cargs)
            except Exception, _e:
                raise
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
            os.chdir(oldcwd)
            for NS in NSs:
                try:
                    del __builtins__[NS]
                except Exception, _e:
                    pass
    return result
