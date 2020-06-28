""" streaming moving average
"""

class StreamingMovingAverage:
    def __init__(self, window_size):
        self.window_size = window_size
        self.values = []
        self.sum = 0

    def next(self, value):
        self.values.append(value)
        self.sum += value
        if len(self.values) > self.window_size:
            self.sum -= self.values.pop(0)
        return float(self.sum) / len(self.values)


if __name__ == '__main__':
    values = [1,1,2,2.1]
    ma = StreamingMovingAverage(8)
    for val in values:
        avg = ma.next(val)
        print val, avg, int(round(avg))
