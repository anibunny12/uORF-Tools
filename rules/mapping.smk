rule genomeIndex:
    input:
        rules.retrieveGenome.output,
        rules.retrieveAnnotation.output
    output:
        "index/genomeStar/chrLength.txt",
        "index/genomeStar/chrName.txt",
        "index/genomeStar/genomeParameters.txt"
    conda:
        "../envs/star.yaml"
    threads: 20
    shell:
        "mkdir -p index/genomeStar; STAR --runThreadN {threads} --runMode genomeGenerate --genomeDir index/genomeStar --genomeFastaFiles {input[0]}" #--sjdbGTFfile {input[1]} --sjdbOverhang 100"

#ruleorder: map > maplink

rule map:
    input:
        fastq="norRNA/{method, [a-zA-Z]+}-{condition, [a-zA-Z]+}-{replicate, d+}.fastq",
        index=rules.genomeIndex.output
    output:
        "bam/{method}-{condition}-{replicate}/Aligned.sortedByCoord.out.bam"
    conda:
        "../envs/star.yaml"
    threads: 20
    params:
        prefix=lambda wildcards, output: (os.path.dirname(output[0]))
    shell:
        "mkdir -p bam; STAR --genomeDir index/genomeStar --readFilesIn {input.fastq} --outFileNamePrefix {params.prefix}/ --outSAMtype BAM SortedByCoordinate --outSAMattributes All --outFilterMultimapNmax 1 --alignEndsType EndToEnd --runThreadN {threads}"

rule maplink:
    input:
        "bam/{method, [a-zA-Z]+}-{condition, [a-zA-Z]+}-{replicate, d+}/Aligned.sortedByCoord.out.bam"
    output:
        "maplink/{method}-{condition}-{replicate}.bam"
    params:
        inlink=lambda wildcards, input:(os.getcwd() + "/" + str(input)),
        outlink=lambda wildcards, output:(os.getcwd() + "/" + str(output))
    threads: 1
    shell:
        "mkdir -p maplink; ln -s {params.inlink} {params.outlink}"
