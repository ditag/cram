bin:
	mkdir bin

db:
	mkdir db

bin/velvetg: bin
	curl -O http://www.ebi.ac.uk/~zerbino/velvet/velvet_1.1.05.tgz
	tar -zxvf velvet_1.1.05.tgz
	make -C velvet_1.1.05 velveth velvetg MAXKMERLENGTH=71 OPENMP=1 LONGSEQUENCES=1
	mv velvet_1.1.05/velvet{g,h} bin/
	rm -rf velvet_1.1.05*

bin/prodigal: bin
	curl -O http://prodigal.googlecode.com/files/prodigal.v2_00.tar.gz
	tar -zxvf prodigal.v2_00.tar.gz
	make -C prodigal.v2_00
	mv prodigal.v2_00/prodigal bin/
	rm -rf prodigal.v2_00*

bin/phmmer: bin
	curl -O http://selab.janelia.org/software/hmmer3/3.0/hmmer-3.0.tar.gz
	tar -zxvf hmmer-3.0.tar.gz
	cd hmmer-3.0; ./configure; make; cd -
	mv hmmer-3.0/src/phmmer bin/
	rm -r hmmer-3.0*

# TODO: add support for other architectures
bin/smalt: bin
	curl -O ftp://ftp.sanger.ac.uk/pub4/resources/software/smalt/smalt-0.5.7.tgz
	tar -zxvf smalt-0.5.7.tgz
	mv smalt-0.5.7/smalt_MacOSX_i386 bin/smalt
	rm -rf smalt-0.5.7*

all: bin bin/velvetg bin/prodigal bin/phmmer bin/smalt
