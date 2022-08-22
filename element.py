class Element:

    def __init__(self,aoiCode,x1,y1,x2,y2):
        self.aoiCode = aoiCode
        self.boundaries = [int(x1),int(y1),int(x2),int(y2)]
        self.metrics = {}