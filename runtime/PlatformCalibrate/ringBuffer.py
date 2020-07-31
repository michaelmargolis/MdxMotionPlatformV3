import numpy as np
from numpy.lib.stride_tricks import as_strided
 

"""
http://code.activestate.com/recipes/68429-ring-buffer/
http://stackoverflow.com/questions/4151320/efficient-circular-buffer
"""


class RingBuffer(object):
    def __init__(self, size_max, dtype=np.int16, default_value=0):
        """
        initialization
        """
        self.size_max = size_max
        self.default_value = default_value

        self._data = np.empty(size_max, dtype=dtype)
        self.reset()

    def reset(self):
        self._data.fill(self.default_value)
        self.size = 0   
    
    """     
    def _rolling_window(self, a, start, window_len):
        shape = a.shape[:-1] + (a.shape[-1] - window_len + 1, window_len)
        strides = a.strides + (a.strides[-1],)
        return np.lib.stride_tricks.as_strided(a, shape=shape, strides=strides)[start]
    """
    def insert(self, index, value):
        #todo add size check
        self._data[index] = value
        
    def append(self, value):
        """
        append an element
        :param value:
        """
        #self._data = np.roll(self._data, 1)
        #self._data[0] = value
        if self.size < self.size_max:
            self._data[self.size] = value
            self.size += 1
        else:
            self.__class__ = RingBufferFull
     
    def read(self,index):
        return self._data[index]

    def get_all(self, window_size):
        """
        return a list of elements from the oldest to the newest
        """
        if self.size <= window_size:
            return self._data[:window_size]
        else:
            return self._data[:self.size]

    def get_partial(self, window_size):
        if self.size <= window_size:
            #print "<, size=", self.size, "len=", len(self._data[0:window_size])
            return self._data[0:window_size]
            #return self._rolling_window(self._data, 0, window_size)
        else:
           # delta = self.size-window_size
           # print ">=, self_size=",self.size, "delta=", delta , "size=", size,  "len=", len(self._data[delta:self.size]), self._data[delta:self.size]
           #return self._rolling_window(self._data, delta, window_size)
           return self._data[self.size-window_size:self.size]

    def __getitem__(self, key):
        """
        get element
        """
        return self._data[key]

    def __repr__(self):
        """
        return string representation
        """
        s = self._data.__repr__()
        s = s + '\t' + str(self.size)
        s = s + '\t' + self.get_all()[::-1].__repr__()
        s = s + '\t' + self.get_partial()[::-1].__repr__()
        return s


class RingBufferFull(RingBuffer):
    def append(self, value):
        """
        append an element when buffer is full
        :param value:
        """
        self._data = np.roll(self._data, 1)
        self._data[0] = value
