from typing import List


class AnalogData():

    @staticmethod
    def decodeByteData(raw, scale=4, magnitude=1000, getRaw=False, diff_mv=0):

        def to16bit(rawPair):
            rawVal = rawPair[0] | (rawPair[1] << 8)
            if diff_mv:
                rawVal = (rawVal - diff_mv) * 2
            return rawVal

        def toFloat(rawInt):
            if getRaw:
                return rawInt
            return float(rawInt * scale) / float(magnitude)

        return [toFloat(to16bit(raw[i:i + 2])) for i in range(0, len(raw), 2)]

    @staticmethod
    def clasifyAnalogData(data, breakOn: List[float]):
        classes = [0 for i in range(len(breakOn) + 1)]

        for val in data:
            for i, bkVal in enumerate(breakOn):
                if val < bkVal:
                    classes[i] += 1
                    break
                elif i == len(breakOn) - 1:
                    classes[i + 1] += 1

        return classes
