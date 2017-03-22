#!/usr/bin/env python

import corr,time

r=corr.katcp_wrapper.FpgaClient('10.1.0.23')
time.sleep(0.1)
r.progdev('test_snap_i2c_2017-03-17_1509.bof')
print '\n'.join(r.listdev())
