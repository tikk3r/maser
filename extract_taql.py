from __future__ import division
from itertools import islice, imap
from operator import itemgetter

import casacore.tables as ct
import numpy as np
import math
import subprocess
import os

def form_baselines(antennas):
    ''' Calculate all possible baselines.
    Args:
        antennas (list) : a list containing all antennas as an integer.
    '''
    baselines = []
    for i in antennas:
        for j in antennas:
            if j <= i:
                # It's either the same antenna or the baseline is already covered.
                continue
            else:
                baselines.append((i,j))
    return baselines

'''
Read in MS file and extract the required columns into numpy arrays.
'''
print '[CVE] Reading in file...'
#msfile = ct.table('target_K_30s_03.ms', readonly=False)
msfile = ct.table('TESTVIS.ms', readonly=False)

print '[CVE] Forming baselines...'
ANTENNA1 = msfile.getcol('ANTENNA1')
ANTENNA2 = msfile.getcol('ANTENNA2')

ANTENNAS = set(ANTENNA1).union(set(ANTENNA2))
baselines = form_baselines(ANTENNAS)
# Extract the data for each baseline.
print '[CVE] Extracting visibilities per baseline...'
progress = 0; end = len(baselines); printed = False
f = open('visibilities.txt', 'wb'); f.close()
for i,j in baselines:
    p = int(progress / end * 100)
    if ((progress % 10) == 0):
        print 'Progress: %d%%' % (p)
    bl = ct.taql('SELECT DATA FROM $msfile WHERE ANTENNA1=$i AND ANTENNA2=$j')
    data = bl.getcol('DATA')
    # Average polarizations together.
    data_avg_pol = np.average(data, axis=2)
    data_avg_pol_flat = data_avg_pol.flatten()
    data_real = data_avg_pol_flat.real
    data_imag = data_avg_pol_flat.imag

    n = len(data_avg_pol_flat)
    antenna1 = np.zeros(n); antenna1.fill(i)
    antenna2 = np.zeros(n); antenna2.fill(j)
    # Save data to file.
    with open('visibilities.txt', 'ab') as f:
        np.savetxt(f, zip(antenna1, antenna2, data_real, data_imag))
    progress += 1

print '[CVE] Loading visibilties...'
print os.path.abspath('./visibilities.txt')
print os.path.exists(os.path.abspath('./visibilities.txt'))
ch = subprocess.check_output('wc -l ./visibilities.txt', shell=True)
ch = int(ch.split(' ')[0])
chunksize = 1000000
chunks = int(math.ceil(ch / chunksize))

print '[CVE] Calculating statistics...'
print 'Using chuncksize: ', chunksize
print 'Using %d chuncks.' % chunks

ravg = []; rvar = []
iavg = []; ivar = []
for i in xrange(chunks):
    print 'Processing chunck %d/%d...' % (i+1, chunks)
    with open('visibilities.txt') as f:
        line = np.genfromtxt(islice(f, i*chunksize, (i+1)*chunksize))
        real, imag = line[:,2], line[:,3]
        ravg.append(real.mean()); rvar.append(real.var())
        iavg.append(imag.mean()); ivar.append(imag.var())

ravg = np.asarray(ravg)
iavg = np.asarray(iavg)
rvar = np.asarray(rvar)
ivar = np.asarray(ivar)
mean_re = ravg.mean(); mean_im = iavg.mean()
std_re = np.sqrt(rvar.mean()); std_im = np.sqrt(ivar.mean())

sig = [std_re, std_im]

print 'Re mean: ', mean_re
print 'Re std: ', std_re
print 'Im mean: ', mean_im
print 'Im std: ', std_im

print '[CVE] Writing back to MS file...'
#ct.taql('UPDATE $msfile SET SIGMA=$sig')

print '[CVE] Finished.'
