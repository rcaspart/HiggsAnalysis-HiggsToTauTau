import ConfigParser
import os
import sys

class configuration:
    def __init__(self, mode, config, mtsoft=False):
        self.config=ConfigParser.SafeConfigParser(allow_no_value=True)
        config_read=self.config.read(["{CMSSW}/src/HiggsAnalysis/HiggsToTauTau/limits-{MODE}.config".format(CMSSW=os.getenv('CMSSW_BASE'), MODE=mode), config])
        if len(config_read) == 1 and config:
            sys.stderr.write("ERROR in LimitsConfig: Specified configuration file does not exist or is not readable.\n")
            exit(1) 
        #read values from config
        self.periods=self.config.get('main', 'periods').split()
        self.channels=self.config.get('main', 'channels').split()
        self.categories={}
        self.inputs={}
        self.unblind=self.config.has_option('main','unblind')
        if self.config.has_option('main', 'blind'):
            self.unblind = False
        self.comb_periods=self.config.get('combination', 'periods').split()
        self.comb_channels=self.config.get('combination', 'channels').split()
        self.comb_categories=self.config.get('combination', 'categories').split()
        for channel in self.channels:
            self.categories[channel]={}
            for period in self.periods:
                self.categories[channel][period]=self.get_categories(channel, period)
            self.inputs[channel]=self.config.get('inputs', channel)
        if mtsoft and 'mt' in self.channels and mode == 'sm':
            for period in self.periods:
                self.categories['mt'][period] = self.categories['mt'][period]+self.get_categories('mt_soft', period, 'sm')
            self.inputs['mt_soft']=self.config.get('inputs', 'mt_soft')
        self.bbbcat={}
        self.bbbproc={}
        self.bbbthreshold={}
        for channel in self.channels:
            self.bbbthreshold[channel]=self.config.get('bbb',channel+'_threshold')
            self.bbbcat[channel]={}
            for period in self.periods:
                self.bbbcat[channel][period]=self.get_bbb_categories(channel, period)
            self.bbbproc[channel]=self.get_bbb_processes(channel)
        if mtsoft and 'mt' in self.channels and mode == 'sm':
            self.bbbproc['mt'] = self.bbbproc['mt']+self.get_bbb_processes('mt_soft')
            for period in self.periods:
                self.bbbcat['mt'][period] = self.bbbcat['mt'][period]+self.get_bbb_categories('mt_soft', period)


    def get_categories(self, channel, period):
        categories=self.config.get('main', channel+'_categories_'+period)
        return categories.split()
    def get_bbb_categories(self, channel, period):
        categories=self.config.get('bbb', channel+'_categories_'+period)
        return categories.split()
    def get_bbb_processes(self, channel):
        process=self.config.get('bbb', channel+'_processes')
        return process.split()
