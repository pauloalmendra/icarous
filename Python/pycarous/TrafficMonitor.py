from ctypes import *

from Interfaces import Bands

class TrafficMonitor():

    def __init__(self,callsign,cfgFile,log,monitor="DAIDALUS"):
        self.lib = CDLL('libTrafficMonitor.so')
        self.lib.newDaidalusTrafficMonitor.restype = c_void_p
        self.lib.newDaidalusTrafficMonitor.argtypes = [c_char_p,c_char_p,c_bool]
        self.lib.TrafficMonitor_UpdateParameters.argtypes = [c_void_p,c_char_p,c_bool]
        self.lib.TrafficMonitor_InputIntruderData.argtypes = [c_void_p,c_int,c_char_p,c_double*3,c_double*3,c_double,c_double*6,c_double*6]
        self.lib.TrafficMonitor_InputOwnshipData.argtypes  = [c_void_p,c_double*3,c_double*3,c_double,c_double*6,c_double*6]
        self.lib.TrafficMonitor_MonitorTraffic.argtypes = [c_void_p,c_double*2]
        self.lib.TrafficMonitor_CheckPointFeasibility.argtypes = [c_void_p,c_double*3,c_double]
        self.lib.TrafficMonitor_CheckPointFeasibility.restype = c_bool
        self.lib.TrafficMonitor_GetTrackBands.argtypes = [c_void_p,POINTER(Bands)]
        self.lib.TrafficMonitor_GetSpeedBands.argtypes = [c_void_p,POINTER(Bands)]
        self.lib.TrafficMonitor_GetAltBands.argtypes = [c_void_p,POINTER(Bands)]
        self.lib.TrafficMonitor_GetVerticalSpeedBands.argtypes = [c_void_p,POINTER(Bands)]
        self.lib.TrafficMonitor_GetTrafficAlerts.argtypes = [c_void_p,c_int,c_char_p,POINTER(c_int)]
        self.lib.TrafficMonitor_GetTrafficAlerts.restype = c_int
        self.obj = self._get_monitor_module_loader(monitor)(callsign,cfgFile,log)

    def _get_monitor_module_loader(self,monitorType):
        if monitorType == 'ACAS':
            return self._get_ACAS_module
        elif monitorType == 'DAIDALUS':
            return self._get_DAIDALUS_module
        else:
            raise ValueError("monitorType {} not supported".format(monitorType))

    def _get_ACAS_module(self,callsign,cfgFile,log):
        self.lib.newACASTrafficMonitor.restype = c_void_p
        self.lib.newACASTrafficMonitor.argtypes = [c_bool,c_char_p]
        return self.lib.newACASTrafficMonitor(c_bool(log),c_char_p(cfgFile.encode('utf-8')))

    def _get_DAIDALUS_module(self,callsign,cfgFile,log):
        return self.lib.newDaidalusTrafficMonitor(c_char_p(callsign.encode('utf-8')),c_char_p(cfgFile.encode('utf-8')),c_bool(log))

    def SetParameters(self,params,log):
        self.lib.TrafficMonitor_UpdateParameters(self.obj,c_char_p(params.encode('utf-8')),c_bool(log))

    def input_traffic(self,callsign,position,velocity,time,sumPos=[0,0,0,0,0,0],sumVel=[0,0,0,0,0,0]):
        cpos = c_double*3
        cvel = c_double*3
        _pos = cpos(position[0],position[1],position[2])
        _vel = cvel(velocity[0],velocity[1],velocity[2])
        _time = c_double(time)
        _index = c_int(0)
        ret = c_int(0)
        ret.value = self.lib.TrafficMonitor_InputIntruderData(self.obj,_index,c_char_p(callsign.encode('utf-8')),_pos,_vel,_time,(c_double*6)(*sumPos),(c_double*6)(*sumVel))
        
    def monitor_traffic(self,position,velocity,windFrom,windSpeed,time,sumPos=[0,0,0,0,0,0],sumVel=[0,0,0,0,0,0]):
        cpos = c_double*3
        _pos = cpos(position[0],position[1],position[2])
        _vel = cpos(velocity[0],velocity[1],velocity[2])
        _wind = (c_double*2)(windFrom,windSpeed)
        self.lib.TrafficMonitor_InputOwnshipData(self.obj,_pos,_vel,c_double(time),(c_double*6)(*sumPos),(c_double*6)(*sumVel))
        self.lib.TrafficMonitor_MonitorTraffic(self.obj,_wind)

    def monitor_wp_feasibility(self,wp,speed):
        cpos = c_double*3
        _wp = cpos(wp[0],wp[1],wp[2])
        val = c_bool(0)
        val.value = self.lib.TrafficMonitor_CheckPointFeasibility(self.obj,_wp,c_double(speed))
        return val.value

    def GetTrackBands(self):
        bands = Bands()
        self.lib.TrafficMonitor_GetTrackBands(self.obj,byref(bands))
        return bands

    def GetGSBands(self):
        bands = Bands()
        self.lib.TrafficMonitor_GetSpeedBands(self.obj,byref(bands))
        return bands

    def GetAltBands(self):
        bands = Bands()
        self.lib.TrafficMonitor_GetAltBands(self.obj,byref(bands))
        return bands

    def GetVSBands(self):
        bands = Bands()
        self.lib.TrafficMonitor_GetVerticalSpeedBands(self.obj,byref(bands))
        return bands

    def GetAlerts(self):
        trafficid = c_char_p()
        trafficid.value=b' '*20
        alert = c_int()
        size = self.lib.TrafficMonitor_GetTrafficAlerts(self.obj,0,trafficid,byref(alert))
        alerts = []
        if size >= 0:
            alerts.append((trafficid.value.decode('utf-8'),alert.value))
            for i in range(1,size):
                trafficid = c_char_p()
                trafficid.value=b' '*20
                self.lib.TrafficMonitor_GetTrafficAlerts(self.obj,i,trafficid,byref(alert))
                alerts.append((trafficid.value.decode('utf-8'),alert.value))

        return alerts
                


