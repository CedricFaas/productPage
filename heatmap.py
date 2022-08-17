import numpy as np
import matplotlib.pyplot as plt
import pandas

def heatmap(path,pId):
    file = pandas.read_csv(path)
    file = file[file.ProductId == pId]
    file = file[file.LeftGazePointValidity == 1]
    file = file[file.RightGazePointValidity == 1]
    file["X"] = round(((file["LeftGazePointX"] + file["RightGazePointX"]) / 2)*1920)
    file["Y"] = round(((file["LeftGazePointY"] + file["RightGazePointY"]) / 2)*1080)
    file = file[file.X <= 1920]
    file = file[file.Y <= 1080]
    file = file[file.X >= 0]
    file = file[file.Y >= 0]
    file = file.drop(file.columns[[0,1,2,3,4,5,6,7,8]], axis=1) 
    myArray = np.zeros((1081,1921))
    grid = pandas.DataFrame(myArray)
    
    file = file.reset_index()
    
    for index, row in file.iterrows():
        x = int(row["X"])
        y = int(row["Y"])
        grid.at[y,x] = grid.at[y,x] + 1.0
        
    
    plt.imshow(grid,cmap='hot',interpolation=None, vmin=0.0, vmax=0.1)
    plt.show()

heatmap('./log/p501/gazeData/gaze_14_0.csv',1)