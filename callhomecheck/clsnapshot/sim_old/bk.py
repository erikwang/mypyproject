#from RASpy.DataCollect import Data_Collect
import sys,os
import pdb
''' parameter supported in [sim] in snapshot.conf
	Simcmd = <path> # simulator data collect command to use
			# default is bsim
'''
Mod_Path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(Mod_Path)
from configfile import SS_CONFIG_FILE

from D_Collect import Data_Collect
def save(path='/tmp'):
	My_Mod_Path = os.path.dirname(os.path.abspath(__file__))
	sys.path.append(My_Mod_Path)
	sim_cfg = dict()
	DsnapConf= SS_CONFIG_FILE(My_Mod_Path).ss_cfg('sim', sim_cfg)
	lsfsim=Data_Collect(path,caller_name())
	sim_cmd = DsnapConf.get('SIMCMD', 'bsim')

	lsfsim.saveit(sim_cmd + ' htrace')
	lsfsim.saveit(sim_cmd + ' htrace -a')
	lsfsim.saveit('bugroup -w')
	lsfsim.saveit('bmgroup -w')
	lsfsim.saveit('busers -w all')
	lsfsim.saveit('bhosts -s')
	lsfsim.saveit('lsload -l')
	lsfsim.saveit('bhosts -l')
	lsfsim.saveit("ypcat passwd | sed 's/:/ /g' | awk '{print $1}'")
	
def caller_name():
	return os.path.basename(__file__).split('.')[0]
