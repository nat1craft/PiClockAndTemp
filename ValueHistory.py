import time
from datetime import datetime
from collections import deque

class DataPoint:
    def __init__(self, value, timeRecorded = None):        
        self.value = value
        if timeRecorded is None:
            self.recorded = datetime.now()
        else:
            self.recorded = timeRecorded


class ValueHistory:
    def __init__(self, name: str, units: str, datapoint: "DataPoint", float = 0.0, historyLength=12):        
        self.name = name
        self.units = units
        self.current = datapoint
        self.last = None
        self.historyLength = historyLength
        h = [self.current] * self.historyLength
        self.history = deque(h,self.historyLength)
        self.max = self.current.value
        self.min = self.current.value
        self.avg = self.current.value
        self.last_avg = self.current.value
        self.trend=" "

    def __str__(self):
        #tm = self.current.recorded.strftime("%Y-%m-%dT%H:%M:%S")
        tm = self.current.recorded.isoformat()
        return "{0}\t{1}={2:0.1f}{3}{4}\tMax:{5:0.1f}{3}\tMin:{6:0.1f}{3}\tAvg:{7:0.1f}{3}".format(tm, self.name, self.current.value, self.units, self.trend, self.max, self.min, self.avg)


    def push(self, datapoint: DataPoint):
        self.last = self.current
        self.last_avg = self.avg

        self.current = datapoint
        if self.max is None:
            self.max = self.current.value
        else:
            self.max = max(self.max,self.current.value)

        if self.min is None:
            self.min = self.current.value
        else:
            self.min = min(self.min,self.current.value)            

        if self.history is None:
            h = [self.current] * self.historyLength
            self.history = deque(h,self.historyLength)
        else:
            self.history.appendleft(self.current)

        sumV = 0
        for v in self.history:
            sumV += v.value

        self.avg = sumV/len(self.history)
        if self.last_avg is None:
            self.last_avg = self.avg
        
        if self.avg > self.last_avg:
            self.trend = "+"
        elif self.avg < self.last_avg:
            self.trend = "-"
        else:
            self.trend = " "
