import numpy as np
import matplotlib.pyplot as plt
import pandas

def heatmap(path,pId):
    file = pandas.read_csv(path)
    file = file[file.ProductId == pId]
    file = file[file.LeftGazePointValidity == 1]
    file = file[file.RightGazePointValidity == 1]
    file["X"] = round(((file["LeftGazePointX"] + file["RightGazePointX"]) / 2)*100)
    file["Y"] = round(((file["LeftGazePointY"] + file["RightGazePointY"]) / 2)*100)
    file = file[file.X <= 100]
    file = file[file.Y <= 100]
    file = file.drop(file.columns[[0,1,2,3,4,5,6,7,8]], axis=1) 
    myArray = np.zeros((101,101))
    grid = pandas.DataFrame(myArray)
    
    file = file.reset_index()
    
    for index, row in file.iterrows():
        grid.at[int(row["X"]),int(row["Y"])] = grid[int(row["X"])][int(row["Y"])] + 1
        
    plt.imshow(grid,cmap='hot',interpolation='nearest', 
               origin = 'lower')
    plt.show()

heatmap('./log/p201/gazeData/gaze_2_0.csv',2)