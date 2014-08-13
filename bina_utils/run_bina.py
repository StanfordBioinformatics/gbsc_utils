#!/usr/bin/env python

# Usage:
#
# binajob = RunBina(outputDir='Bina://my/output/dir', description='my project')
#
# binajob.addAlignerJob('readgroup1', sample1', inputBAM='Bina://myinput/file1.bam')
# binajob.addAlignerJob('readgroup2', sample1', inputBAM='Bina://myinput/file2.bam')
# binajob.addAlignerJob('readgroup3', sample1', inputBAM='Bina://myinput/file3.bam')
#
# binajob.addAlignerJob('readgroup4', sample2', inputBAM='Bina://myinput/file4.bam')
# binajob.addAlignerJob('readgroup4', sample3', inputBAM='Bina://myinput/file5.bam')
# binajob.addAlignerJob('readgroup4', sample4', inputBAM='Bina://myinput/file6.bam')
#
# binaJob.submit()

import bina

class RunBina(object):

   api_key = "gocardinal"

   nodes = [
      "scg-bb-01-genstorage.sunet:8080",
      "scg-bb-02-genstorage.sunet:8080",
      "scg-bb-03-genstorage.sunet:8080",
      "scg-bb-04-genstorage.sunet:8080",
      "scg-bb-05-genstorage.sunet:8080"
      ]

   def __init__(self, outputDir, description, genotypeWithGATK=False, mapWithBWA=False):
      alignmentData = []

      self.BWA = mapWithBWA
      self.GATK = genotypeWithGATK

      self.job = bina.Job()
      self.job.set_output_dir(outputDir)
      self.job.set_description(description)

      # Select Broad GATK or the Bina genotyper
      self.job.set_use_broad_gatk(self.GATK)
      if self.GATK:
         self.job.genotyping.unified_genotyper.set_option("--genotype_likelihoods_model","BOTH")

      # Send emails on job success or failure
      self.job.set_notification("scg-auto-notify@lists.stanford.edu", "binabox")

      self._applyStandardJobSettings()
      self._applyStandardVQSRSettings()

   def addAlignerJob(self, readGroup, sampleID, inputFastq1=None, inputFastq2=None, inputBAM=None):
      aligner_job = bina.BinaAlignerJob(
         first_end = inputFastq1,
         second_end = inputFastq2,
         readgroup = readGroup,
         library = "Library",
         sample = sampleID,
         platform = "Illumina",
         bam_input = inputBAM)

      aligner_job.set_trimming(30)

      # Set aligner template size calculation to automatic
      aligner_job.set_option("--template_len_comp_method", 2)

      # Use batched template size calculation to emulate BWA
      aligner_job.set_argument("--enable_batch_pairing", True)

      self.job.alignment.add_aligner_job(aligner_job)

   def submit(self):
      binabox = bina.BinaBox()
      binabox.connect(self.api_key, self.nodes)
      job_id = binabox.run_job(self.job)
      print "Job submitted with ID " + job_id + "."

   def _applyStandardJobSettings(self):
      # Reference
      self.job.reference.set_species("human")
      self.job.reference.set_genome_build("hg19")
      self.job.reference.set_dbsnp_build("135")

      if self.BWA:
         self.job.alignment.set_disable_concurrent_sorting(True)
      else:
         self.job.alignment.set_disable_concurrent_sorting(False)

      # What to keep
      self.job.alignment.set_keep_merged_sorted_bams(False)
      self.job.realignment.set_keep_merged_realigned_bams(True)
      if self.GATK:
         self.job.genotyping.unified_genotyper.set_option("--output_mode", "EMIT_ALL_CONFIDENT_SITES")
      else:
         self.job.genotyping.fast_genotyper.set_option("--output_mode", "EMIT_ALL_CONFIDENT_SITES")


      # Enable all structural variation tools
      self.job.structural_variation.set_disable_bina_sv(True)
      self.job.structural_variation.set_run_breakdancer(True)
      self.job.structural_variation.set_run_breakseq(True)
      self.job.structural_variation.set_run_cnvnator(True)
      self.job.structural_variation.set_run_pindel(True)
      self.job.structural_variation.pindel.set_use_breakdancer(True)

   def _applyStandardVQSRSettings(self):

      vqsr_resource_snp_0 = bina.VariantRecalibrationResource("hapmap", "bina://VA/data/referencefiles/hapmap/hapmap_3.3.hg19.sites.vcf")
      vqsr_resource_snp_0.set_file_type("VCF")
      vqsr_resource_snp_0.set_training(True)
      vqsr_resource_snp_0.set_known(False)
      vqsr_resource_snp_0.set_truth(True)
      vqsr_resource_snp_0.set_prior(15.0)

      vqsr_resource_snp_1 = bina.VariantRecalibrationResource("omni", "bina://VA/data/referencefiles/omni/1000G_omni2.5.hg19.sites.vcf")
      vqsr_resource_snp_1.set_file_type("VCF")
      vqsr_resource_snp_1.set_training(True)
      vqsr_resource_snp_1.set_known(False)
      vqsr_resource_snp_1.set_truth(False)
      vqsr_resource_snp_1.set_prior(12.0)

      vqsr_resource_snp_2 = bina.VariantRecalibrationResource("dbsnp", "bina://VA/data/referencefiles/dbsnp/dbsnp_135.hg19.vcf")
      vqsr_resource_snp_2.set_file_type("VCF")
      vqsr_resource_snp_2.set_training(False)
      vqsr_resource_snp_2.set_known(True)
      vqsr_resource_snp_2.set_truth(False)
      vqsr_resource_snp_2.set_prior(6.0)

      vqsr_snp = bina.VariantRecalOperation()
      vqsr_snp.set_name("snp")
      vqsr_snp.set_variant_type("SNP")
      vqsr_snp.add_resource(vqsr_resource_snp_0)
      vqsr_snp.add_resource(vqsr_resource_snp_1)
      vqsr_snp.add_resource(vqsr_resource_snp_2)
      vqsr_snp.add_annotations(["QD", "HaplotypeScore", "MQRankSum", "ReadPosRankSum", "FS", "MQ", "DP"])

      vqsr_resource_indel_0 = bina.VariantRecalibrationResource("mills", "bina://VA/Mills_and_1000G_gold_standard.indels.hg19.sites.rightHeader.vcf")
      vqsr_resource_indel_0.set_file_type("VCF")
      vqsr_resource_indel_0.set_training(True)
      vqsr_resource_indel_0.set_known(True)
      vqsr_resource_indel_0.set_truth(True)
      vqsr_resource_indel_0.set_prior(12.0)

      vqsr_indel = bina.VariantRecalOperation()
      vqsr_indel.set_name("indel")
      vqsr_indel.set_variant_type("INDEL")
      vqsr_indel.add_resource(vqsr_resource_indel_0)
      vqsr_indel.add_annotations(["QD", "FS", "HaplotypeScore", "ReadPosRankSum"])

      self.job.genotyping.add_recal_operation(vqsr_snp)
      self.job.genotyping.add_recal_operation(vqsr_indel)
      self.job.genotyping.set_keep_recal_files(True)
      self.job.genotyping.set_perform_vqsr(True)
