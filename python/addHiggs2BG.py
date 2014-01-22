"""
Backend python implemenation of a addition of a SM higgsboson processes as background contribution
to existing datacards configurations.

2013-12-19 Rene Caspart
"""

import os
import re
import ROOT
from optparse import OptionParser
from glob import glob
from HiggsAnalysis.HiggsToTauTau.UncertAdaptor import UncertAdaptor
from HiggsAnalysis.HiggsToTauTau.utils import get_shape_systematics

ROOT.PyConfig.IgnoreCommandLineOptions = True
ROOT.gROOT.SetBatch()  

def signal_processes(filename):
    '''
    This function extracts the signal processes and category names from a configuration file.
    '''
    file = open(filename, 'r')
    signal_proc = []
    signal_group = "GROUP signal"
    category = None
    for line in file:
        if signal_group in line:
            signal_proc.extend(line[line.rfind(signal_group)+len(signal_group)+1:].rstrip('\n').split(','))
        if 'categories' in line:
            category = line.strip().split()[1]
    return category,signal_proc

def copy_histos(file, category, processes, uncerts, mass):
    '''
    This function takes as inputs a opened ROOTfile, a categoryname, a list of processes, uncertainties and a massindex.
    It copys the histograms, which are given bei process+mass(+uncertainty+Up/Down) and copyies them to process+_SM(+uncertainty+Up/Down)
    '''
    for proc in processes:
        hist = file.Get(category+"/"+proc+mass)
        if hist:
            new_hist = hist.Clone(hist.GetName().replace(mass,"_SM"))
            file.cd(category)
            new_hist.Write(hist.GetName().replace(mass,"_SM"), ROOT.TObject.kOverwrite)
            for uncert in uncerts:
                for suffix in ['Up','Down']:
                    hist = file.Get(category+"/"+proc+mass+uncert+suffix)
                    if hist:
                        new_hist = hist.Clone(hist.GetName().replace(mass,"_SM"))
                        file.cd(category)
                        new_hist.Write(category+"/"+hist.GetName().replace(mass,"_SM"), ROOT.TObject.kOverwrite)
                    
def addHiggs2BG(setup, channels, mass, signal=None):
    '''
    This function takes a setup path and set of channels.
    It loops over all present sm configurations and adds an additional higgs with suffix '_SM'
    to the backgrounds for the found configurations.
    '''
    uncertadaptor = UncertAdaptor()
    for channel in channels:
        print "processing ", channel
        categories = {}
        uncerts = {}
        for file in sorted(glob("{SETUP}/{CHN}/cgs-sm*.conf".format(SETUP=setup,CHN=channel))):
            if os.path.exists(file.replace('cgs','unc').replace('conf','vals')):
                print "processing ", file
                matcher = re.compile('cgs-sm-(?P<PER>\d\w+)-(?P<CAT>\w+).\w*')
                catnumber = matcher.search(file).group('CAT')
                per = matcher.search(file).group('PER')
                cat,sig_proc = signal_processes(file)
                if signal:
                    sig_proc = signal
                if per in categories:
                    categories[per].extend(cat.split(','))
                else:
                    categories[per]=[]
                    categories[per].extend(cat.split(','))
                uncertadaptor.cgs_processes(file, None, [process+'_SM' for process in sig_proc], None, None)
                ## loop over all category names and processes and get the corresponding shape uncertainties
                for catname in cat.split(','):
                    if not per in uncerts:
                        uncerts[per]={}
                    uncerts[per][catname]=[]
                    for proc in sig_proc:
                        uncerts[per][catname].extend(get_shape_systematics(setup, per, channel, catnumber, proc, catname))
                    ## ensure the list contains only unique entries
                    uncerts[per][catname]=list(set(uncerts[per][catname]))
    
                unc_file = file.replace('cgs','unc').replace('conf','vals')
                unc_val = open(unc_file, 'r')
                outfile = open(unc_file+'_tmp','w')
                for line in unc_val:
                    if line.strip() and line[0] != '#':
                        for proc in sig_proc:
                            if proc in line.strip().split()[1]:
                                line = line.replace(proc, proc+','+proc+'_SM')
                        if 'signal' in line.strip().split()[1]:
                            line = line.replace('signal','signal,'+','.join([process+'_SM' for process in sig_proc]))
                    outfile.write(line)
                unc_val.close()
                outfile.close()
                os.system("mv "+unc_file+'_tmp '+unc_file)
        for filename in glob("{SETUP}/{CHN}/*.root".format(SETUP=setup,CHN=channel)):
            print "processing ", filename
            matcher = re.compile('(v?)htt(_?\w*).inputs-sm-(?P<PER>\d\w+).root')
            per = matcher.search(filename).group('PER')
            file = ROOT.TFile(filename, "UPDATE")
            for cat in categories[per]:
                copy_histos(file, cat, sig_proc, uncerts[per][cat], str(mass))
