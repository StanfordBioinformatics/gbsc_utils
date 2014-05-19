#!/usr/bin/env python

from optparse import OptionParser
import os
import re
import shutil
import xml.dom.minidom

class RemoveMissingTiles(object):

    DEFAULT_RUN_ROOT='/srv/gsfs0/projects/gbsc/SeqCenter/Illumina/RunsInProgress'

    def __init__(self, options):
        self.run = None

        self.setRun(options['run'])

    def showMissingTiles(self):
        missing = self._getMissingTiles()
        print missing

    def removeMissingTiles(self):
        configFile = os.path.join(
            self.run, 'Data', 'Intensities', 'BaseCalls', 'config.xml')

        self._backup(configFile)

        # Place tile objects from the XML file in a hash
        # with the format tiles[laneID][tileID]
        # for ease of look-up
        tiles = {}
        configXML = xml.dom.minidom.parse(configFile)
        lanesXML = configXML.getElementsByTagName('Lane')
        for laneXML in lanesXML:
            laneIndex = laneXML.getAttribute('Index')
            tiles[laneIndex] = {}
            for tileXML in laneXML.getElementsByTagName('Tile'):
                tileIndex = tileXML.childNodes[0].wholeText
                tiles[laneIndex][tileIndex] = tileXML

        # Remove missing tiles from configXML
        missing = self._getMissingTiles()
        for tile in missing:
            laneIndex = tile[0][-1]
            tileIndex = tile[1]
            thisTile = tiles[laneIndex][tileIndex]
            thisTile.parentNode.removeChild(thisTile)

        with open(configFile, 'w') as f:
            f.write(configXML.toxml())
        
    def _backup(self, configFile):
        configFileBak = configFile+'.bak'
        if not os.path.isfile(configFileBak):
            print "Backing up config.xml as %s" % configFileBak
            shutil.copy(configFile, configFileBak)
        else:
            print "Skipping config.xml backup. Backup already exists at %s" % configFileBak

    def _getMissingTiles(self):
        filterDirs = self.getFilterDirs()
        allMissingTiles = []
        for lane in filterDirs:
            allFiles = os.listdir(lane)
            filterRE = re.compile('.filter')
            controlRE = re.compile('.control')
            filterFiles = filter(filterRE.search, allFiles)
            controlFiles = filter(controlRE.search, allFiles)
            # Remove file extensions and keep last 4 chars (tile number)
            filterTiles = set([ f.split('.')[0][-4:] for f in filterFiles])
            controlTiles = set([ f.split('.')[0][-4:] for f in controlFiles])
            missingTiles = controlTiles.difference(filterTiles)
            for f in missingTiles:
                allMissingTiles.append((lane.split('/')[-1], f))
        return allMissingTiles

    def setRun(self, runInput):
        if len(runInput.split('/')) > 1:
            # Assume path is given
            self.run = runInput
        else:
            # Append run root
            self.run = os.path.join(self.DEFAULT_RUN_ROOT, runInput)

    def getFilterDirs(self):
        if not self.run:
            raise Exception(
                'Run directory must be set before getting *.filter dir')
        basecalls = os.path.join(self.run, 'Data', 'Intensities', 'BaseCalls')
        # Identify subfolders of the basecalls dir that are named as lanes L###
        laneRE = re.compile('L[0-9]{3}')
        lanes = filter(laneRE.search, os.listdir(basecalls))
        filterDirs = []
        for lane in lanes:
            filterDirs.append(os.path.join(basecalls, lane))
        return filterDirs

    @classmethod
    def parse_commandline_input(cls):
        parser = OptionParser()
        parser.add_option(
            "-r", 
            "--run", 
            dest="run",
            help="sequencing run name")
        (options, args) = parser.parse_args()
        cls.clean_args(args)
        return cls.clean_options(options)

    @classmethod
    def clean_args(cls, args):
        if args:
            raise Exception('Unused argument(s): "%s"' % args)

    @classmethod
    def clean_options(cls, options_raw):
        options = {}
        options['run'] = cls.clean_run_option(options_raw.run)
        return options

    @classmethod
    def clean_run_option(cls, run):
        if not run:
            raise Exception('--run argument is required')
        return run

if __name__=='__main__':
    options = RemoveMissingTiles.parse_commandline_input()
    rmc = RemoveMissingTiles(options)
#    rmc.showMissingTiles()
    rmc.removeMissingTiles()
