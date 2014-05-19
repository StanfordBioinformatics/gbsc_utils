#!/usr/bin/env python

from argparse import ArgumentParser
import os
import re

import syapse_client

class Run:
    
    def __init__(self, runName, conn):
        self.conn = conn
        self.runName = runName
        
        self.run = None
        self.flowcell = None
        self.flowcellLayouts = None
        self.lanes = None
        self.libraries = None
        self.barcodes = None
        self.sequencingInstrument = None

    def getRun(self):
        if not self.run:
            runRecords = self.conn.kb.listAppIndividualRecords(name=self.runName, kb_class_id='scgpm:ScgpmIlluminaSequencingRun')
            assert len(runRecords)==1, 'Expected only one item with name %s but found %s. Run names should be unique.' % (self.runName, len(runRecords))
            runID = runRecords[0].app_ind_id
            self.run = self.conn.kb.retrieveAppIndividual(runID)
        return self.run

    def getFlowcell(self):
        if not self.flowcell:
            ID = self.getRun().hasScgpmIlluminaFlowcell.value()
            self.flowcell = self.conn.kb.retrieveAppIndividual(ID)
        return self.flowcell

    def getFlowcellLayouts(self):
        if not self.flowcellLayouts:
            self.flowcellLayouts = self.getFlowcell().hasScgpmFlowcellLayout.values()
        return self.flowcellLayouts

    def getLanes(self):
        if not self.lanes:
            self.lanes = {}
            for layout in self.getFlowcellLayouts():
                ID = layout.hasScgpmFlowcellLane.value()
                laneNumStr=layout.flowcellLane.value()
                if not re.match(r'^[0-9]+$', laneNumStr):
                    raise Exception('Expected lane number but found %s' % laneNumStr)
                self.lanes[int(laneNumStr)] = self.conn.kb.retrieveAppIndividual(ID)
        return self.lanes

    def getLibraries(self):
        if not self.libraries:
            self.libraries = {}
            for laneIndex in self.getLanes():
                libID = self.getLanes()[laneIndex].hasScgpmLibrary.value()
                self.libraries[laneIndex] = self.conn.kb.retrieveAppIndividual(libID)
        return self.libraries

    def getBarcodes(self):
        if not self.barcodes:
            self.barcodes = {}
            for laneIndex in self.getLibraries():
                lib = self.getLibraries()[laneIndex]
                barcodes = lib.hasBarcodedSample.values()
                codepoints = []
                for barcode in barcodes:
                    codepoints.append(barcode.codePoint)
                self.barcodes[laneIndex] = codepoints
        return self.barcodes

    def getSequencingInstrument(self):
        if not self.sequencingInstrument:
            ID = self.getRun().hasScgpmSequencingInstrument.value()
            self.sequencingInstrument = self.conn.kb.retrieveAppIndividual(ID)
        return self.sequencingInstrument

    def getSequencingRequest(self, laneNum):
        # Returns only first in list for multiple matching requests
        libraries = self.getLibraries()[laneNum]
        sequencing_requests = self.getMatchingSequencingRequests(libraries)
        if len(sequencing_requests) == 0:
            return None
        else:
            return sequencing_requests[0]

    def getMatchingSequencingRequests(self, library):
        results = self.conn.kb.executeSyQLQuery(
            """
            SELECT ?ScgpmCASequencingRequest_A.sys:uniqueId WHERE {
            REQUIRE PATTERN ?ScgpmCASequencingRequest_A scgpm:ScgpmCASequencingRequest {
            scgpm:hasScgpmLibrary %s }
            } """
            % library.id
        )
        col = results.headers.index(u'scgpm:ScgpmCASequencingRequest : sys:uniqueId')
        matchingSequencingRequests = []
        for row in results.rows:
            request = self.conn.kb.retrieveAppIndividualByUniqueId(row[col])
            if self.doesSequencingRequestMatch(request):
                matchingSequencingRequests.append(request)
        return matchingSequencingRequests

    def doesSequencingRequestMatch(self, request):
        flowcell = self.getFlowcell()
        return request.active.value() and \
            request.indexRead.value() == flowcell.isIndexRead.value() and \
            request.read1Cycles.value() == flowcell.read1Cycles.value() and \
            request.read2Cycles.value() == flowcell.read2Cycles.value()

    def getAnalysisParams(self):
        solexaRun = self.getRun()
        flowcell = self.getFlowcell()
        sequencingInstrument = self.getSequencingInstrument()

        return {
            'run_name': solexaRun.name.value(),
            'flow_cell': flowcell.scgpmFlowcellId.value(),
            'index_read': flowcell.isIndexRead.value(),
            'pared_end': flowcell.isPairedEnd.value(),
            'read1_cycles': solexaRun.read1Cycles.value(),
            'read2_cycles': solexaRun.read2Cycles.value(),
            'index1_cycles': solexaRun.index1Cycles.value(),
            'index2_cycles': solexaRun.index2Cycles.value(),
            'seq_software': solexaRun.scgpmIlluminaSequencerSoftware.value()
        }

    def getLaneParams(self):
        lanes = self.getLanes()
        params = {}
        for index in lanes:
            dnaLibrary = self.conn.kb.retrieveAppIndividual(lanes[index].hasScgpmLibrary.value())
            prefix='lane:%s:' % index
            params.update(
                {
                    prefix+'lane_number': index,
                    prefix+'sample_name': dnaLibrary.name.value(),
                    prefix+'owner': dnaLibrary.owner.value().full_name,
                    prefix+'multiplexed': dnaLibrary.multiplexedLibrary.value(),
                    prefix+'barcode_position': dnaLibrary.barcodePosition.value(),
                    prefix+'barcode_size': dnaLibrary.barcodeSize.value(),
                }                
            )
        return params

    def getBarcodeParams(self):
        barcodes = self.getBarcodes()
        params = {}
        for index in barcodes:
            prefix='lane:%s:' % index
            barcodeIndex = 0
            for barcode in barcodes[index]:
                barcodeIndex+=1
                prefix2 = "barcode:%s:" % barcodeIndex
                params.update({prefix+prefix2+'codepoint': barcode.value()})
        return params

    def getGeraldParams(self):
        params = {}
        prefix = 'gerald:0:'
        for index in self.getLanes():
            prefix2 = 'lane:%s:' % index
            request = self.getSequencingRequest(index)
            params[prefix+prefix2+'sample_name'] = self.getLibraries()[index].name.value()
            #submitter
            if (request == None) or (not self.hasMappingRequest(request)):
                params[prefix+prefix2+'analysis_type'] = 'sequence'
            else:
                params[prefix+prefix2+'analysis_type'] = 'map'
                params[prefix+prefix2+'mapping_program'] = request.sequenceMappingProgram.value()
                params[prefix+prefix2+'read1_num_skipped_bases'] = request.hasSkippedBases.value().read1.value()
                params[prefix+prefix2+'read2_num_skipped_bases'] = request.hasSkippedBases.value().read2.value()
                params[prefix+prefix2+'read1_num_mapped_bases'] = request.hasMappedBases.value().read1.value()
                params[prefix+prefix2+'read2_num_mapped_bases'] = request.hasMappedBases.value().read2.value()
                params[prefix+prefix2+'max_mismatches'] = request.maxNumMismatchingBases.value()
                params[prefix+prefix2+'max_mismatches'] = request.maxNumHitsPerRead.value()
                params[prefix+prefix2+'reference_sequence_name'] = request.referenceSequence.value()
                params[prefix+prefix2+'filter_poly_a'] = request.filterPolyA.value()
                params[prefix+prefix2+'generate_sgr'] = request.scgpmGenerateSgrSignalTrack.value()
                params[prefix+prefix2+'sgr_extension'] = request.scgpmSgrExtension.value()
        return params

    def getGeraldParamsForLane(self, index):
        params = {}
        request = self.getSequencingRequest(index)
        params['sample_name'] = self.getLibraries()[index].name.value()
            #submitter
        if (request == None) or (not self.hasMappingRequest(request)):
            params['analysis_type'] = 'sequence'
        else:
            params['analysis_type'] = 'map'
            params['mapping_program'] = request.sequenceMappingProgram.value()
            params['read1_num_skipped_bases'] = request.hasSkippedBases.value().read1.value()
            params['read2_num_skipped_bases'] = request.hasSkippedBases.value().read2.value()
            params['read1_num_mapped_bases'] = request.hasMappedBases.value().read1.value()
            params['read2_num_mapped_bases'] = request.hasMappedBases.value().read2.value()
            params['max_mismatches'] = request.maxNumMismatchingBases.value()
            params['max_mismatches'] = request.maxNumHitsPerRead.value()
            params['reference_sequence_name'] = request.referenceSequence.value()
            params['filter_poly_a'] = request.filterPolyA.value()
            params['generate_sgr'] = request.scgpmGenerateSgrSignalTrack.value()
            params['sgr_extension'] = request.scgpmSgrExtension.value()
        return params

    def hasMappingRequest(self, request):
        if request.sequenceMappingProgram.value():
            return True
        else:
            return False

    def printParams(self):
        self.printDict(self.getAnalysisParams())
        self.printDict(self.getLaneParams())
        self.printDict(self.getBarcodeParams())
        self.printDict(self.getGeraldParams())

    def printParamsForLane(self, index):
        self.printDict(self.getGeraldParamsForLane(index))

    def printDict(self, params):
        for param in params:
            print "%s %s" % (param, params[param])

def initialize_parser():
    parser=ArgumentParser('Query the Syapse LIMS to get information for a sequencing run')
    parser.add_argument('--run_name', required=True)
    parser.add_argument('--lane')
    parser.add_argument('--user')
    parser.add_argument('--password')
    parser.add_argument('--project', default = 29792)
    parser.add_argument('--url', default = 'scgpm.syapse.com')
    return parser

if __name__=='__main__':
    args = initialize_parser().parse_args()

    runName = args.run_name

    try:
        project = os.environ['SYAPSE_PROJECT']
    except KeyError:
        project = args.project

    try:
        url = os.environ['SYAPSE_URL']
    except KeyError:
        url = args.url

    if not args.user:
        try:
            user = os.environ['SYAPSE_USER']
        except KeyError:
            raise Exception('User not set. You must provide a --user argument or set the SYAPSE_USER environment variable')
    else:
        user = args.user

    if not args.password:
        try:
            password = os.environ['SYAPSE_PASSWORD']
        except KeyError:
            raise Exception('Password not set. You must provide a --password argument or set the SYAPSE_PASSWORD environment variable')
    else:
        password = args.password

    conn = syapse_client.SyapseConnection(url, user, password, use_http=False, timeout=600)
    conn.current_project = conn.retrieveProject('s:project/%s' % project)

    run = Run(runName, conn)
    if args.lane:
        run.printParamsForLane(int(args.lane))
    else:
        run.printParams()
