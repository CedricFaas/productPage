# productPage
To start performing the study, you have to first start app.py and then open localhost:5000/ in your browser.

To continue after each calibration you have to press the enter button.

The gaze data is stored in the log folders for each participant.

All data recorded by the eye tracker is stored in the files named gaze_PRODUCTSET_HIGHLIGHTING_FULL.csv.
The highlighting techniques are: no highlighting (0), larger font(1), red text (1), blinking text (3).
The first two columns of the files refer to the product currently looked at and how often the participant visited it.
ProductId 0 refers to a sanity check, in which a dot is shown in the middle of the screen.

The images folder contains a screenshot for every product, the files are named: PRODUCTSET_PRODUCTID.jpg.
The highlighting techniques used in the screenshots varies randomly.

analyze.py was used to analyze the gaze metrics.
evaluation.py was used to evaluate the questionnaires, the decisions made and the decision time.
