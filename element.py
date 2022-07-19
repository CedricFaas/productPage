class Element:

    def __init__(self,aoiCode,x1,y1,x2,y2):
        self.aoiCode = aoiCode
        self.boundaries = [x1,y1,x2,y2]
        self.metrics = {}