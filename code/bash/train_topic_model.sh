#!/bin/sh
# Bash script for training topic model
# Used for COVID earnings calls
# Arguments: input Mallet .seq file from importing TSV file
seqfile=$1

bname=`basename $seqfile .seq`
k=50    # num of topics

source ~/.bashrc

# outputprefix is output/seqfilename-numtopics-modelnum
outputprefix=output/$bname-$k-0
# Obtain initial model by training for 5000 iterations
if [ ! -f $outputprefix.gz ]; then
    iterations=500
    echo train $outputprefix $seqfile
    mallet train-topics --input $seqfile --num-topics $k --optimize-interval 10 --num-iterations $iterations --output-state $outputprefix.gz --output-topic-keys $outputprefix.keys.txt --num-top-words 20 --diagnostics-file $outputprefix.diag.xml --evaluator-filename $outputprefix.evaluator --word-topic-counts-file $outputprefix.wordcounts.txt --topic-word-weights-file $outputprefix.wordweights.txt --output-doc-topics $outputprefix.doctopics.txt &> $outputprefix.out
fi

# Obtain 9 more models, each trained by 100 more iterations than the last
for i in {1..9}; do
    prevoutputprefix=output/$bname-$k-$(($i-1)) # use previous model's output as input state to new model
    if [ -f $prevoutputprefix.gz ]; then
        outputprefix=output/$bname-$k-$i
        iterations=100
        echo train $outputprefix $seqfile
        mallet train-topics --input $seqfile --num-topics $k --optimize-interval 10 --num-iterations $iterations --input-state $prevoutputprefix.gz --output-state $outputprefix.gz --output-topic-keys $outputprefix.keys.txt --num-top-words 20 --diagnostics-file $outputprefix.diag.xml --evaluator-filename $outputprefix.evaluator --word-topic-counts-file $outputprefix.wordcounts.txt --topic-word-weights-file $outputprefix.wordweights.txt --output-doc-topics $outputprefix.doctopics.txt &> $outputprefix.out
    fi
done
