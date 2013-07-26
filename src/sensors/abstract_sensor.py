from tools import Item
from abc import ABCMeta, abstractmethod , abstractproperty

class AbstractSensor(Item):

    __metaclass__ = ABCMeta
    
    
    

    @abstractmethod
    def connect(self):
        """
        Connects sensor
        """
        pass

    @abstractmethod
    def disconnect(self):
        """
        Disconnects sensor
        """
        pass

    @abstractmethod
    def delete(self):
        """
        Deletes sensor
        """
        pass

    @abstractmethod
    def measure(self):
        """
        Called to measure sensor
        Returns
        -------
        DataContainer
        """
        pass

    # abstract method to handle sensor creation based on configuration
    @classmethod
    @abstractmethod
    def create(cls,config,data_handler,hardware):
        """
        Abstract method that when implemented is the intializer method for the sensor.
        
        Parameters
        ----------
        config : configuration
        data_handler : data_handler
        hardware : HardwareManager

        Returns
        -------
        AbstractSensor
        """
        pass


    