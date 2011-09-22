from dnaio import *
from helps import *

def trim_pairs(**ops):
    ''' trim paired reads, output interleaved fastq and singletons files '''
    
    ohai('trimming pairs')
    for f in [ops['out_left'], ops['out_right'], ops['out']]:
        if os.path.exists(f):
            okay('skipping!')
            return
    
    input_format = ops.get('input_format', 'qseq')
    
    left_mates  = Dna(ops['left_mates'], type=input_format)
    right_mates = Dna(ops['right_mates'], type=input_format)
    out_left    = open(ops['out_left'], 'w')
    out_right   = open(ops['out_right'], 'w')
    out_trimmed = open(ops['out'], 'w')
    cutoff      = int(ops['cutoff'])
    
    from itertools import izip
    
    counts = {
        'pairs': 0,
        'left':  0,
        'right': 0,
    }
    
    for left, right in izip(left_mates, right_mates):
        left_trimmed, right_trimmed = Trim.trim(left), Trim.trim(right)
        
        if len(right_trimmed) < cutoff and len(left_trimmed) < cutoff:
            # both reads suck
            continue
        elif len(right_trimmed) < cutoff:
            # keep left pair
            print >> out_left, left_trimmed.fastq
            counts['left'] += 1
        elif len(left_trimmed) < cutoff:
            # keep right pair
            print >> out_right, right_trimmed.fastq
            counts['right'] += 1
        else:
            # both are good, keep both!
            print >> out_trimmed, left_trimmed.fastq
            print >> out_trimmed, right_trimmed.fastq
            counts['pairs'] += 1
    
    # way too many file handles :[
    out_left.close()
    out_right.close()
    out_trimmed.close()
    left_mates.close()
    right_mates.close()
    
    # return read counts
    return counts


class Trim():
    ''' The Famous Trim algorithm '''

    @classmethod
    def _get_coords(self, quality, **kwargs):
        ''' the trim2 algorithm '''
        
        quality_cutoff = 20
        
        _sum, _max, first, last, start, end = 0, 0, 0, 0, 0, 0
        for a, q in enumerate(quality):
            _sum += (q - quality_cutoff)
            if _sum > _max:
                _max = _sum
                end = a
                start = first
            if _sum < 0:
                _sum = 0
                first = a
        
        return (start, end - start)
    
    @classmethod
    def trim(self, record):
        ''' an atomic method for sequence trimming '''
        
        # trimming algorithm
        coords = self._get_coords(record.quality)
        
        # truncate sequence and quality accordingly
        sequence = record.sequence[coords[0]:coords[1]]
        quality = record.quality[coords[0]:coords[1]]
        
        # quick test
        assert len(sequence) == len(quality)
        
        # make and return a new record
        new_record = Record(record.header, sequence, quality)
        
        return new_record
    
    @classmethod
    def _check_seq(self, record, **kwargs):
        ''' make sure sequence survives trimming '''
        
        ops = { # defaults
            'min_length': 0,
            'skip_if_quality_has': [],
            'skip_if_read_has': [],
        }
        
        ops.update(kwargs)
        
        for n in ops['skip_if_quality_has']:
            if n in record.quality:
                return False
        for n in ops['skip_if_read_has']:
            if n in record.sequence:
                return False
        
        if len(record.sequence) < ops['min_length']:
            return False
        return True



def test():
    
    # this is temporarily broken because Trim() doesn't have support for
    # defining ascii offset of quality scores and these are for offset
    # 64 (Illumina). I temporarily need 33.
    raw = \
'''HWUSI-EAS163FR:13:2:1:4515:5372:0:1:A
GCCGCGGTAACACGTAGGGCGCGAGCGTTGTCCGGAATTATTGGGCGTAAAGAGCTCGTAGGCGGCCTGTTGCGTGCGCTGTGAAAGCCG
HWUSI-EAS163FR:13:2:1:4515:5372:0:1:A
ffffffffffaffffcfffafffafcfffffddfdPRdd]^bbbf_febaacafY^Wa^]b`XbcZJ_c\^XM^BBBBBBBBBBBBBBBB
'''.split('\n')
    
    trimmed = \
'''HWUSI-EAS163FR:13:2:1:4515:5372:0:1:A
GCCGCGGTAACACGTAGGGCGCGAGCGTTGTCCGGAATTATTGGGCGTAAAGAGCTCGTAGGCGGCCTGTTGC
HWUSI-EAS163FR:13:2:1:4515:5372:0:1:A
ffffffffffaffffcfffafffafcfffffddfdPRdd]^bbbf_febaacafY^Wa^]b`XbcZJ_c\^XM
'''.split('\n')
    
    record = Record(raw[0], raw[1], [ (ord(i) - 64) for i in raw[3] ])
    trimmed = Record(trimmed[0], trimmed[1], [ ord(i) - 64 for i in trimmed[3] ])
    record = Trim.trim(record)
    
    assert record.sequence == trimmed.sequence
    assert record.quality == trimmed.quality
