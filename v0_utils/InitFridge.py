from v0_utils.qcodes_tools import \
    instrument_factory, init_or_create_database, load_or_create_experiment, \
    add_parameter_to_instrument, \
    DelegateParameter, VirtualInstrument

from importlib import reload
from pytopo.qctools import instruments as instools; reload(instools)
from pytopo.qctools.instruments import create_inst, add2station
import qcodes as qc

def QT4_init(**kwargs):
    station = qc.Station()
    inst_list = []
    
    if 'DMM1' in kwargs and kwargs['DMM1'] is True:
        from qcodes.instrument_drivers.Keysight.Keysight_34465A import Keysight_34465A
        DMM1 = instools.create_inst(Keysight_34465A, 'DMM1', address="TCPIP::169.254.26.27")
        inst_list.append(DMM1)
    
    if 'DMM2' in kwargs and kwargs['DMM2'] is True:
        from qcodes.instrument_drivers.Keysight.Keysight_34465A import Keysight_34465A
        DMM2 = instools.create_inst(Keysight_34465A, 'DMM2', address="TCPIP::169.254.88.178")
        inst_list.append(DMM2)
            
    if 'DMM3' in kwargs and kwargs['DMM3'] is True:
        from qcodes.instrument_drivers.Keysight.Keysight_34465A import Keysight_34465A
        DMM3 = instools.create_inst(Keysight_34465A, 'DMM3', address="TCPIP::169.254.4.61")
        inst_list.append(DMM1)
    
    if 'lockin1' in kwargs and kwargs['lockin1'] is True:
        from qcodes.instrument_drivers.stanford_research.SR860 import SR860
        lockin1 = instools.create_inst(SR860, "lockin1", "TCPIP::169.254.88.181")
        inst_list.append(lockin1)
            
    if 'lockin2' in kwargs and kwargs['lockin2'] is True:
        from qcodes.instrument_drivers.stanford_research.SR860 import SR860
        lockin2 = instools.create_inst(SR860, "lockin2", "TCPIP::169.254.88.179")
        inst_list.append(lockin2)
            
    if 'yokogawa' in kwargs and kwargs['yokogawa'] is True:
        from qcodes.instrument_drivers.yokogawa.GS200 import GS200
        yokogawa = instools.create_inst(GS200, "yokogawa", "USB0::0x0B21::0x0039::91U100329::INSTR")
        inst_list.append(yokogawa)
            
    if 'mdac' in kwargs and kwargs['mdac'] is True:
        from MDAC.Driver.MDAC import MDAC
        mdac = instools.create_inst(MDAC, "mdac", address='ASRL4::INSTR', force_new_instance=True)
        inst_list.append(mdac)
    
    if 'SGS1' in kwargs and kwargs['SGS1'] is True:
        from qcodes.instrument_drivers.rohde_schwarz.SGS100A import RohdeSchwarz_SGS100A
        SGS1 = instools.create_inst(RohdeSchwarz_SGS100A, "SGS1", "TCPIP::169.254.90.38")
        inst_list.append(SGS1)
            
    if 'SGS2' in kwargs and kwargs['SGS2'] is True:
        from qcodes.instrument_drivers.rohde_schwarz.SGS100A import RohdeSchwarz_SGS100A
        SGS2 = instools.create_inst(RohdeSchwarz_SGS100A, "SGS2", "TCPIP::169.254.2.20")
        inst_list.append(SGS2)
    
    if 'scope' in kwargs and kwargs['scope'] is True:
        from qcodes.instrument_drivers.Keysight.Infiniium import Infiniium
        #import qcodes.instrument_drivers.Keysight.Infiniium as MSO
        scope = instools.create_inst(Infiniium, 'scope', 'TCPIP::169.254.159.151')
        inst_list.append(scope)
        
    if 'rigol' in kwargs and kwargs['rigol'] is True:
        from qcodes.instrument_drivers.rigol.DG1062 import DG1062
        rigol = instools.create_inst(DG1062, 'rigol', 'TCPIP::169.254.32.101')
        inst_list.append(rigol)
    
    if 'awg_5208' in kwargs and kwargs['awg_5208'] is True:
        from qcodes.instrument_drivers.tektronix.AWG5208 import AWG5208
        awg = instools.create_inst(AWG5208, "awg", address='TCPIP0::169.254.121.32::inst0::INSTR')
        inst_list.append(awg_5208)
    
    if 'magnet' in kwargs and kwargs['magnet'] is True:
        from qcodes.instrument_drivers.american_magnetics.AMI430 import AMI430,AMI430_3D
        ami_x = instools.create_inst(AMI430, "AMI430_x", "169.254.237.94", port = 7180, has_current_rating=True)
        ami_y = instools.create_inst(AMI430, "AMI430_y", "169.254.250.157", port = 7180, has_current_rating=True)
        ami_z = instools.create_inst(AMI430, "AMI430_z", "169.254.70.33", port = 7180, has_current_rating=True)
        magnet = instools.create_inst(AMI430_3D, "AMI430", ami_x, ami_y, ami_z, 1)
        inst_list.append(magnet)
        
    if 'alazar' in kwargs and kwargs['alazar'] is True:
        from qcodes.instrument_drivers.AlazarTech import utils; reload(utils)
        from qcodes.instrument_drivers.AlazarTech import ATS9360; reload(ATS9360)
        from qcodes.instrument_drivers.AlazarTech.ATS9360 import AlazarTech_ATS9360
        alazar = instools.create_inst(AlazarTech_ATS9360, 'alazar', force_new_instance=True)
        inst_list.append(alazar)
    
    station = qc.Station(*inst_list)
    return station

def QT5_init(**kwargs):
    station = qc.Station()
    inst_list = []
    
    if 'DMM1' in kwargs and kwargs['DMM1'] is True:
        from qcodes.instrument_drivers.Keysight.Keysight_34465A import Keysight_34465A
        DMM1 = instools.create_inst(Keysight_34465A, 'DMM1', address="TCPIP::169.254.26.27")
        inst_list.append(DMM1)
    
    if 'DMM2' in kwargs and kwargs['DMM2'] is True:
        from qcodes.instrument_drivers.Keysight.Keysight_34465A import Keysight_34465A
        DMM2 = instools.create_inst(Keysight_34465A, 'DMM2', address="TCPIP::169.254.88.178")
        inst_list.append(DMM2)
            
    if 'DMM3' in kwargs and kwargs['DMM3'] is True:
        from qcodes.instrument_drivers.Keysight.Keysight_34465A import Keysight_34465A
        DMM3 = instools.create_inst(Keysight_34465A, 'DMM3', address="TCPIP::169.254.4.61")
        inst_list.append(DMM3)
    
    if 'lockin1' in kwargs and kwargs['lockin1'] is True:
        from qcodes.instrument_drivers.stanford_research.SR860 import SR860
        lockin1 = instools.create_inst(SR860, "lockin1", "TCPIP::169.254.88.181")
        inst_list.append(lockin1)
            
    if 'lockin2' in kwargs and kwargs['lockin2'] is True:
        from qcodes.instrument_drivers.stanford_research.SR860 import SR860
        lockin2 = instools.create_inst(SR860, "lockin2", "TCPIP::169.254.88.179")
        inst_list.append(lockin2)
            
    if 'yokogawa' in kwargs and kwargs['yokogawa'] is True:
        from qcodes.instrument_drivers.yokogawa.GS200 import GS200
        yokogawa = instools.create_inst(GS200, "yokogawa", "USB0::0x0B21::0x0039::91U100329::INSTR")
        inst_list.append(yokogawa)
            
    if 'mdac' in kwargs and kwargs['mdac'] is True:
        from MDAC.Driver.MDAC import MDAC
        mdac = instools.create_inst(MDAC, "mdac", address='ASRL4::INSTR', force_new_instance=True)
        inst_list.append(mdac)
    
    if 'SGS1' in kwargs and kwargs['SGS1'] is True:
        from qcodes.instrument_drivers.rohde_schwarz.SGS100A import RohdeSchwarz_SGS100A
        SGS1 = instools.create_inst(RohdeSchwarz_SGS100A, "SGS1", "TCPIP::169.254.90.38")
        inst_list.append(SGS1)
            
    if 'SGS2' in kwargs and kwargs['SGS2'] is True:
        from qcodes.instrument_drivers.rohde_schwarz.SGS100A import RohdeSchwarz_SGS100A
        SGS2 = instools.create_inst(RohdeSchwarz_SGS100A, "SGS2", "TCPIP::169.254.2.20")
        inst_list.append(SGS2)
    
    if 'scope' in kwargs and kwargs['scope'] is True:
        from qcodes.instrument_drivers.Keysight.Infiniium import Infiniium
        #import qcodes.instrument_drivers.Keysight.Infiniium as MSO
        scope = instools.create_inst(Infiniium, 'scope', 'TCPIP::169.254.159.151')
        inst_list.append(scope)
        
    if 'rigol' in kwargs and kwargs['rigol'] is True:
        from qcodes.instrument_drivers.rigol.DG1062 import DG1062
        rigol = instools.create_inst(DG1062, 'rigol', 'TCPIP::169.254.32.101')
        inst_list.append(rigol)
    
    if 'awg_5208' in kwargs and kwargs['awg_5208'] is True:
        from qcodes.instrument_drivers.tektronix.AWG5208 import AWG5208
        awg = instools.create_inst(AWG5208, "awg", address='TCPIP0::169.254.121.32::inst0::INSTR')
        inst_list.append(awg_5208)
    
    if 'magnet' in kwargs and kwargs['magnet'] is True:
        from qcodes.instrument_drivers.american_magnetics.AMI430 import AMI430,AMI430_3D
        ami_x = instools.create_inst(AMI430, "AMI430_x", "169.254.237.94", port = 7180, has_current_rating=True)
        ami_y = instools.create_inst(AMI430, "AMI430_y", "169.254.250.157", port = 7180, has_current_rating=True)
        ami_z = instools.create_inst(AMI430, "AMI430_z", "169.254.70.33", port = 7180, has_current_rating=True)
        magnet = instools.create_inst(AMI430_3D, "AMI430", ami_x, ami_y, ami_z, 1)
        inst_list.append(magnet)
        
    if 'alazar' in kwargs and kwargs['alazar'] is True:
        from qcodes.instrument_drivers.AlazarTech import utils; reload(utils)
        from qcodes.instrument_drivers.AlazarTech import ATS9360; reload(ATS9360)
        from qcodes.instrument_drivers.AlazarTech.ATS9360 import AlazarTech_ATS9360
        alazar = instools.create_inst(AlazarTech_ATS9360, 'alazar', force_new_instance=True)
        inst_list.append(alazar)
    
    station = qc.Station(*inst_list)
    return station

