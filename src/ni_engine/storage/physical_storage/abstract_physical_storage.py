import ni_engine.config as config 
from abc import ABCMeta, abstractmethod , abstractproperty
import threading
import copy
import atexit
import glob
class AbstractPhysicalStorage(object):
    """
    Abstract physical storage class that must be implemented by all 
    physical storage mediums. 
    """
    __metaclass__ = ABCMeta


    CODE = "ABSTRACTSTORAGE"

    def __init__(self):
        atexit.register(self._close,self)
    
    
    def store_data(self,type_measurement,measurement):
        """
        Takes a DataContainer and stores to file

        Parameters 
        ----------
        type_measurement : str 
            What type of information to store. Ie. controller, hardware or sensor
        measurement : AbstractMeasurement or list[AbstractMeasurement]

        """
        
        c = copy.deepcopy(measurement)        
        self.write_queue.add((type_measurement,c))        
        if len(self.write_queue)>=self.buffer_size:
            self.write_data(self.write_queue)
        

    @abstractmethod
    def write_data(self,queue):
        """
        Is called when the number of measurements in measurement queue
        is greater than the buffer_size parameter

        Parameters
        ----------
        queue : ItemStore
        """
        raise NotImplementedError('Abstract method has not been implemented')


    def store_compound(self,type_measurement,measurement):
        """
        Takes a DataContainer and stores to file

        Parameters 
        ----------
        type_measurement : str 
            What type of information to store. Ie. controller, hardware or sensor
        measurement : AbstractMeasurement or list[AbstractMeasurement]

        """
        
        self.write_compound_queue.add((type_measurement,copy.deepcopy(measurement)))        
        if len(self.write_compound_queue)>=self.buffer_size:
            self.write_compound(self.write_compound_queue)

    @abstractmethod
    def write_compound(self,queue):
        """
        Is called when the number of measurements in measurement queue
        is greater than the buffer_size parameter. Writes compound measurement

        Parameters
        ----------
        queue : ItemStore
        """
        raise NotImplementedError('Abstract method has not been implemented')

    
    def store_controller(self,controller_measurements,compound=False):
        """
        Stores controller information

        Parameters
        ----------
        controller_measurements : DataContainer
        """
        if not compound:
            self.store_data("controllers",controller_measurements)
        else:
            self.store_compound("controllers",controller_measurements)

    
    def store_sensor(self,sensor_measurements,compound=False):
        """
        Stores sensor information

        Parameters
        ----------
        sensor_measurements : DataContainer
        """
        if not compound:
            self.store_data("sensors",sensor_measurements)
        else:
            self.store_compound("sensors",sensor_measurements)

    
    def store_hardware(self,hardware_measurements,compound=False):
        """
        Stores hardware information

        Parameters
        ----------
        hardware_measurements : DataContainer
        """
        if not compound:
            self.store_data("hardware",hardware_measurements)
        else:
            self.store_compound("hardware",hardware_measurements)

    def store_mixed(self,mixed_data,compound=False):
        """
        Stores mixed information

        Parameters
        ----------
        mixed_data : DataContainer
        """
        if not compound:
            self.store_data("hardware",mixed_data)
        else:
            self.store_compound("hardware",mixed_data)





    @classmethod 
    @abstractmethod    
    def create(cls,configuration):
        """
        Takes configuration, generates object of storage engine and returns it.

        Parameters
        ----------
        configuration : dictionary
            Configuration dictionary

        Returns 
        -------
        AbstractPhysicalStorage
            Object of class with correct configuration information
        """
        raise NotImplementedError('Abstract method has not been implemented')

    def _close(self):
        """
        Make sure to make final writes
        """
        self.write_data(self.write_queue)
        self.write_compound(self.write_compound_queue)

    @abstractmethod
    def close(self):
        """
        Method registered with atexit to be called to close connection. On 
        exit of ni-engine
        """
        raise NotImplementedError('Abstract method has not been implemented')

    @classmethod
    @abstractmethod
    def build_data_from_file(cls,file_path,number_elems=None):
        """
        Abstract method to build stored data into Dictionary of Data containers
        """
        raise NotImplementedError('Abstract method has not been implemented')    

    @property
    def buffer_size(self):
        """
        property for how many measurements should be waited for until written to file

        Parameters
        ----------
        value : int
            When the number of values to stored in write buffer equals or exceeds this, a
            write is triggered.
        """
        if not hasattr(self, '_buffer_size'):
            self._buffer_size = 0
            return int(self._buffer_size)
        else: return int(self._buffer_size)
    @buffer_size.setter    
    def buffer_size(self,value):
        self._buffer_size = value
    

    @property
    def write_queue(self):
        """
        Queue that holds all of the AbstractDataContainers to be written. The data 
        inside the queue is a tuple of (measurement_type(str),DataContainer )
        """
        if not hasattr(self, '_write_queue'):
            self._write_queue = ItemStore()
            return self._write_queue
        else:
            return self._write_queue
    @write_queue.setter
    def write_queue(self,write_queue):
        assert isinstance(write_queue,ItemStore)
        self._write_queue = write_queue

    @property
    def write_compound_queue(self):
        """
        Queue that holds all of the AbstractDataContainers to be written. The data 
        inside the queue is a tuple of (measurement_type(str),DataContainer )
        """
        if not hasattr(self, '_write_compound_queue'):
            self._write_compound_queue = ItemStore()
            return self._write_compound_queue
        else:
            return self._write_compound_queue
    @write_compound_queue.setter
    def write_compound_queue(self,write_compound_queue):
        assert isinstance(write_compound_queue,ItemStore)
        self._write_queue = write__compoundqueue

    @abstractproperty
    def code(self):
        """
        Should return the storage engine code
        
        Returns
        -------
        str
        """
        raise NotImplementedError('Abstract method has not been implemented')
    def _get_newest_file_index(self,file_path,file_extension):
        path_no_ext = file_path.replace('.'+file_extension,'')
        glob_string = path_no_ext+'_[0-9]*.'+file_extension
        nums = []
        try:

            file_list = glob.glob(glob_string)               
            if file_list:   
                nums = map(lambda x: int(x.replace('.'+file_extension,'').replace(path_no_ext+'_','')),file_list)
                self.has_old_data = True
            else: 
                #if there are currently no files, set to 0 as this will indicate no previous file
                nums.append(-1)
                self.has_old_data = False
        except:
            print "There are improperly named files in the storage directory."
            raise 
        
        nums.sort()        
        return nums[-1]
    def get_sequential_file_name(self,file_path,file_extension):
        """
        Find the actual path name that should be written too if we 
        want to number our files path_to_file_1.ext,path_to_file_2.ext
        ...

        Parameters
        ----------
        file_path : str
            The path to the file_name template
            ie. /home/experiment/data/test_data.h5
        file_extension: str
            The extension of the file type to be 
            stored. ie. 'h5','txt'... 

        Returns 
        -------
        str
        """
        path_no_ext = file_path.replace('.'+file_extension,'')
        index = self._get_newest_file_index(file_path,file_extension)
        
        return '{0}_{1}.{2}'.format(path_no_ext,index+1,file_extension)
    
    def get_last_file_path(self,file_path,file_extension):
        """
        Get path to last experiment data 

        Parameters
        ----------
        file_path : str
            The path to the file_name template
            ie. /home/experiment/data/test_data.h5
        file_extension: str
            The extension of the file type to be 
            stored. ie. 'h5','txt'... 

        Returns
        -------
        str or False
            returns `False` if there is no previous file
        """
        path_no_ext = file_path.replace('.'+file_extension,'')
        index = self._get_newest_file_index(file_path,file_extension)
        if index>=0:
            return '{0}_{1}.{2}'.format(path_no_ext,index,file_extension)
        else:
            return False

    @property
    def has_old_data(self):
        return self._has_old_data
    @has_old_data.setter
    def has_old_data(self, value):
        self._has_old_data = value
    
class ItemStore(object):
    """
    Threadsafe itemstore
    """

    def __init__(self):
        self.lock = threading.Lock()
        self.items = []
        
    def add(self, item):
        """
        Add an item or list to store safely with mutex

        Parameters
        ----------
        item : list or object
        """
        
        with self.lock:
            if isinstance(item, list):
                self.items.join(item)
            else:
                self.items.append(item)


    def get_all(self,empty=True):
        """
        Get all items from store with thread safety
        and empties the store. 

        Parameters
        ----------
        empty : bool

        Returns
        -------
        list
        """
        with self.lock:
            items = self.items
            if empty: self.items = []
        return items

    def __len__(self):        
        length = 0
        with self.lock:   
            

            length = reduce(lambda x,y : x+len(y[1]),self.items,0) 
                
        return length
