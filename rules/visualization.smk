rule genomeSize:
    input:
        rules.genomeSamToolsIndex.output
    output:
        "genomes/sizes.genome"
    conda:
        "../envs/samtools.yaml"
    threads: 1
    log: "logs/genomeSamToolsIndex.log"
    shell:
        "mkdir -p genomes; cut -f1,2 {input[0]} > genomes/sizes.genome"

rule bamindex:
    input:
        rules.map.output,
        rules.genomeSize.output
    output:
        "bam/{method}-{condition}-{sampleid}.bam.bai"
    conda:
        "../envs/samtools.yaml"
    threads: 20
    params:
        prefix=lambda wildcards, output: (os.path.splitext(os.path.basename(output[0]))[0])
    shell:
        "samtools index -@ {threads} bam/{params.prefix}"

rule wig:
    input:
        rules.map.output,
        rules.genomeSize.output,
        rules.bamindex.output
    output:
        "tracks/{method}-{condition}-{sampleid}.wig"
    conda:
        "../envs/wig.yaml"
    threads: 1
    params:
        prefix=lambda wildcards, output: (os.path.splitext(os.path.basename(output[0]))[0])
    shell:
        "mkdir -p tracks; bam2wig.py -i bam/{params.prefix}.bam -s {input[1]} -o tracks/{params.prefix}"

rule annotationBed:
    input:
        rules.retrieveAnnotation.output
    output:
        "tracks/annotation.bed"
    conda:
        "../envs/bed.yaml"
    threads: 1
    shell:
        "mkdir -p tracks; cat {input[0]} | grep -v '\tgene\t' > tracks/annotation-woGenes.gtf; gtf2bed < tracks/annotation-woGenes.gtf > tracks/annotation.bed"

rule annotationBigBed:
    input:
        rules.annotationBed.output,
        rules.genomeSize.output
    output:
        "tracks/annotation.bb"
    conda:
        "../envs/bed.yaml"
    threads: 1
    shell:
        "mkdir -p tracks; cut -f1-6 {input[0]} > tracks/annotationNScore.bed6;  awk '{{$5=1 ; print ;}}' tracks/annotation.bed6 > tracks/annotation.bed6; bedToBigBed -type=bed6 -tab tracks/annotation.bed6 {input[1]} tracks/annotation.bb"
