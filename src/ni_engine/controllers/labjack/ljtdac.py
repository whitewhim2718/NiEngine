import ni_engine.config as config
from ..abstract_controllers import AbstractDAC
import struct
from ni_engine.storage import DataContainer,data

class LJTDAC(AbstractDAC):
    """
    LJTDAC controller class. Interacts and sets LJTDACS
    
    **Required Parameters:**
    
    * 'pin'     

    **Optional Parameters:**
    
    * 'default_voltage'(float)
    * 'max_voltage'(float)
    """
    code = 'LJTDAC'
    name = 'LJTDAC Extension'
    description = 'A dac extension that can output from -10V to +10V'
    default_voltage = 0.0
    max_volt = 10.0
    DAC_PIN_DEFAULT = 0
    U3_DAC_PIN_OFFSET = 0
    EEPROM_ADDRESS = 0x50
    DAC_ADDRESS = 0x12
    CALIBRATION_OFFSET = 0.03
    MAX_DATA = 100
    def __init__(self,ID,device,dac_pin,default_voltage=0,max_voltage=10,max_stored_data=100,name=name,description=description):
        self._id = ID 
        self._device = device
        self._dac_pin = dac_pin    
        self._default_voltage = default_voltage        
        self.max_voltage = max_voltage        
        self._name = name
        self._description = description
        self._max_stored_data = max_stored_data
        
        if self._dac_pin %2 == 0 :
            self._is_A = True
        else : 
            self._is_A = False
            self._dac_pin -= 1

        if self._device.code == "U3LV":
            self.sclPin = self._dac_pin + LJTDAC.U3_DAC_PIN_OFFSET
            self.sdaPin = self.sclPin + 1
        else:
            self.sclPin = self._dac_pin
            self.sdaPin = self.sclPin + 1


        

    def connect(self):
        self.initialize_default()

    def initialize_default(self):
        """
        setup and initialize to default values
        """
        self.get_cal_constants()
        self.voltage = self._default_voltage

    def disconnect(self):
        raise NotImplementedError('Abstract method has not been implemented')

    def _set_voltage(self,voltage):
        """
        Implements :class:`.AbstractDAC`s method.   
        Sets the voltage for the corresponding output of 
        the LJTDAC 
        """
        
        
        #apply calibration function
        v= self.calibration_function(self.voltage)        
        voltage = v.magnitude

        if self._is_A:
            self._device.i2c(LJTDAC.DAC_ADDRESS, [48, int(self.calibration_function(((voltage*self.aSlope)+self.aOffset))/256), 
                int(self.calibration_function(((voltage*self.aSlope)+self.aOffset))%256)],
             SDAPinNum = self.sdaPin, SCLPinNum = self.sclPin)
        else:
            self._device.i2c(LJTDAC.DAC_ADDRESS, [49, int(self.calibration_function(((voltage*self.bSlope)+self.bOffset))/256), 
                int(self.calibration_function(((voltage*self.bSlope)+self.bOffset))%256)],
             SDAPinNum = self.sdaPin, SCLPinNum = self.sclPin)
        
        
    def get_cal_constants(self):
        """
        Get Calibration constances
        """             
        # Make request
        data = self._device.i2c(LJTDAC.EEPROM_ADDRESS, [64], NumI2CBytesToReceive=36, SDAPinNum = self.sdaPin, SCLPinNum = self.sclPin)
        response = data['I2CBytes']
        self.aSlope = self.to_double(response[0:8])
        self.aOffset = self.to_double(response[8:16])
        self.bSlope = self.to_double(response[16:24])
        self.bOffset = self.to_double(response[24:32])

        if 255 in response: raise IOError("The calibration constants for controller: {0} seem a little off. Please go into settings and make sure the pin numbers are correct and that the LJTickDAC is properly attached.".format(self._id))
    
    #calibrates function to be more accurate
    #testing has shown than an adjusted voltage follows equation
    #As far as I can tell builtin calibration function for dac is optimal
    #just return the required voltage than until a better calibration function is found
    def calibration_function(self,voltage):
        """
        Not needed right now. If we need to adjust
        the set voltage based on additional calibration data 
        do it here. 

        Parameters
        ----------
        voltage : quantities.Quantity

        Returns 
        -------
        quantities.Quantity
        """
        return voltage
        
    def to_double(self,buffer):
        """
        Name: to_double(buffer)
        Args: buffer, an array with 8 bytes
        Desc: Converts the 8 byte array into a floating point number.
        """
        if type(buffer) == type(''):
            bufferStr = buffer[:8]
        else:
            bufferStr = ''.join(chr(x) for x in buffer[:8])
        dec, wh = struct.unpack('<Ii', bufferStr)
        return float(wh) + float(dec)/2**32

    def get_status(self):
        """
        Get's current voltage and max_voltage of LJTDAC 

        Returns
        -------
        DataContainer : Contains 'voltage' and 'max_voltage'
        """ 
        con = DataContainer(self.id,self._max_stored_data)
        con['voltage'] = data(self.id,self.code,self.name,self.voltage)
        con['max_voltage'] = data(self.id,self.code,self.name,self.max_voltage)
        return con

    @classmethod 
    def create(cls,configuration,data_handler,hardware,sensors):
        """
        Creation function for class
        """
        ID = configuration[config.ID]        
        n = configuration.get(config.NAME,cls.name)
        d = configuration.get(config.DESCRIPTION,cls.description)
        dac_pin = configuration['pins']['dac']  
        max_voltage = configuration.get('max_voltage',cls.max_volt)
        default_voltage = configuration.get('default_voltage',cls.default_voltage)
        max_stored_data = configuration.get(config.MAX_DATA,cls.MAX_DATA)
             
        
        return LJTDAC(ID,hardware,dac_pin,default_voltage=default_voltage,max_stored_data=max_stored_data,max_voltage = max_voltage, name=n,description=d) 
