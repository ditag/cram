# encoding: utf-8

import os
import sys

def get_outdir(out):
    ''' append config to d '''
    def s(s):
        return out + '/' + s.lstrip('/')
    return s

def ohai(s):
    ''' simple status message '''
    c = '\033[96m'
    e = '\033[0m'
    print ' %s✪ %s%s' % (c, s, e)

def okay(s):
    ''' successfully did something '''
    c = '\033[92m'
    e = '\033[0m'
    print ' %s✓%s %s' % (c, e, s)

def ohno(s):
    ''' did something and AAH! failure! '''
    c = '\033[91m'
    e = '\033[0m'
    print ' %s✖%s %s' % (c, e, s)
    quit()

def run(cmd):
    ''' runs a system command '''
    res = os.system(cmd)
    if res == 0:
        okay(cmd)
    else:
        ohno(cmd)

def velvet(**ops):
    ''' run velvet assembly '''
    
    velveth = ' '.join([
        'bin/velveth',
        '%(outdir)s',
        '%(kmer)s',
        '-fasta',
        '-short',
        ' %(reads)s',
        '> /dev/null']) % ops
    
    velvetg = 'bin/velvetg %(outdir)s > /dev/null' % ops
    
    ohai('running velvet: %(reads)s, k = %(kmer)s' % ops)
    
    run(velveth) # run hash algorithm
    run(velvetg) # run assembly algorithm

def reference_assemble(**ops):
    ''' reference assemble using clc_ref_assemble_long '''
    
    # drm :(
    assert os.path.exists('clc.license')

    clc = ' '.join([
      'bin/clc_ref_assemble_long',
      '-q %(query)s',
      '-d %(reference)s',
      '-o %(out)s.clc',
      '-a local', # todo, make an option?
      '--cpus 16', # todo, autodetect.
      ]) % ops

    ohai('running reference assembly %(query)s vs. %(reference)s')
    
    run(clc)

    # generate assembly table
    assembly_table = 'bin/assembly_table -n -s %(out)s.clc > %(out)s' % ops
    run(assembly_table)


def prodigal(**ops):
    ''' run prodigal '''
    
    prodigal = ' '.join([
        'bin/prodigal',
        '-q',
        '-f gff',
        '-i %(input)s',
        '-o %(out)s.gff',
        '-a %(out)s.faa',
        '-d %(out)s.fna',
        '-p meta'
    ]) % ops
    
    ohai('running prodigal: %(input)s' % ops)
    
    run(prodigal)

def phmmer(**ops):
    ''' run phmmer '''
    
    # phmmer doesn't like to use as many cpus as you specify
    # so it would be a good idea to put some kind of simple
    # map reduce in here,  ala: from concurrent.futures import *
    
    # phmmer is slow when it comes to threading. I don't think has
    # anything to do with Disk IO as it's still slow even with a
    # ram disk. I may have to use some kind of map-reduce to speed
    # this up.
    
    phmmer = ' '.join([
        'bin/phmmer',
        '--notextw',
        '--domE 0.001',
        '--incE 0.00001',
        '--cpu 24',
        '--incdomE 0.00001',
        '--noali',
        '-o /dev/null',
        '--tblout %(out)s.table',
        '-E 0.00001',
        #'/dev/stdin',
        '%(query)s',
        '%(db)s'
    ]) % ops
    
    # gnu parallel method
    parallel = "parallel --pipe --recstart '>' --progress -N1000"
    
    
    ohai('running phmmer: %(query)s vs. %(db)s' % ops)

    run(phmmer)
    quit()

def make_coverage_table(**ops):
    ''' create table of reference sequence, no. hits '''
    
    reference = ops['reference']
    table     = ops['table']
    out       = ops['out']
    
    from itertools import count
    from collections import defaultdict
    
    # get sequence # -> header from reference db
    # * fix this for paired output!?
    # * clc has a bug in table output, might not even need to do this.
    n_to_counts = defaultdict(int) # { reference: reads that mapped to it }
    with open(table) as handle:
        for line in handle:
            line = line.strip().split()
            ref_n = int(line[5])
            
            n_to_counts[ref_n] += 1
            
    # convert back into regs dictionary
    n_to_counts = dict(n_to_counts)
    
    # which names to keep?
    keep = set(n_to_counts.keys())
    
    # get names of references that we care about
    # XXX start counting at 1 or 0?
    
    c, n_to_name = count(), {}
    n_to_name[-1] = 'unmatched'
    
    with open(reference) as handle:
        for line in handle:
            if line.startswith('>'):
                n = c.next()
                if n in keep:
                    n_to_name[n] = line.lstrip('>').rstrip()
                
    # print coverage table
    with open(out, 'w') as handle:
        print >> handle, 'function\t%s' % table
        for n in n_to_counts:
            name = n_to_name[n]
            count = n_to_counts[n]
            print >> handle, '%s\t%s' % (name, count)
    

def generate_ss_table(**ops):
    ''' generate a table containing subsystems and their coverage
    with merged counts at higher levels'''
    pass

def prepare_seed(**ops):
    ''' create table of seed_id -> subsystems '''
    
    ohai('generating subsystem table %(out)s from %(seed)s' % ops)
    
    # TODO work out better fig id parsing?
    
    # load subsystems from figids using subsystems2peg
    figs_to_name = {}
    with open(ops['peg']) as handle:
        for line in handle:
            line = line.strip()
            line = line.split('\t')
            
            assert(len(line) == 3)
            
            _, name, fig = line
            
            assert type(fig) == str
            
            figs_to_name[fig] = name
    
    # load full subsystem names using subsystems2role
    name_to_ss = {}
    with open(ops['role']) as handle:
        for line in handle:
            line = line.strip()
            line = line.split('\t')
            
            assert(len(line) == 4)
            
            a, b, c, d = line
            
            name_to_ss[d] = [b, a, c]
    
    # Print table, using SEED headers
    with open(ops['seed']) as handle, open(ops['out'], 'w') as out:
        for line in handle:
            if line.startswith('>'):
                
                fig = line.split()[0][1:]
                
                name = figs_to_name.get(fig, fig)
                
                ss = name_to_ss.get(name, [None]*4)
                
                print >> out, "%s\t%s;%s;%s;%s" % (fig, ss[0], ss[1], ss[2], name)
  
