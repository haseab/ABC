import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.pyplot import figure


class BurndownChart():
    def see_new_plan(self, df, start_date, max_hours=8):
        """Algorithm that takes all tasks and breaks them up into different 8 hour days
           The discrete size of these tasks are preserved and are not split into the next day

           The ETA column has a reverse cumulative sum setup so that hours are decreasing with
           every new line

           Parameters:
               max_hours: The maximum number of productive hours in a day
               start_date: The start date of the projects

            Returns:
                data: dataframe of the each task grouped by date
        """
        # Filtering only the incomplete tasks
        incompleteTasks = df[df["Completed"] == False].reset_index(drop=True)[["Day", "Task", "ETA", "Completed"]]
        # Calling algorithm to split the tasks into a day blocks (list of dataframes, one for each day)
        result = self._day_blocks(incompleteTasks, max_hours)
        # Converting date argument into a datetime object
        date = pd.to_datetime(start_date).to_pydatetime()
        # Creating new DataFrame with initial line to show total sum of hours
        data = pd.DataFrame([["", 0, True, date.strftime('%Y-%m-%d')]], columns=["Task", "ETA", "Completed", "Day"])
        # Iterating through the list of dataframes and adding consecutive days after the start date
        for i, j in zip(result, range(len(result))):
            i.loc[:, "Day"] = [(date + timedelta(days=j)).strftime('%Y-%m-%d')] * len(i)
            data = data.append(i)
        data = data.set_index(["Day", "Task"])
        # Creating Reverse cumulative series on ETA column
        data["Amount Left"] = list(data["ETA"].loc[::-1].cumsum().shift(1).fillna(0))[::-1]
        return data

    def save_new_plan(self, datahandler, plan):
        """
        function 'new_plan' must be run first in order to run this function. This is a wrapper to save it

        Paramaters:
            plan - multi-index dataframe. Obtained from the 'new_plan' output

        Returns:
            str - string explain the filename of saved csv
        """
        # Searching for any file that might have a duplicate name
        newpath = self._get_updated_path(datahandler, "Proposed", plan.index[0][0])
        # Asking if you want to save
        inputs = input(f"File is about to be written as '{newpath}'. OK? (y/n):  ")
        if inputs in ["Y", "y", "yes", "Yes", "YES", "YEs"]:
            export = plan.reset_index().to_csv(newpath, index=False)
            return plan.reset_index()
        else:
            return "Canceled operation"

    def get_latest_plan(self, instance):
        # Searches for most recently modified file with first word "Proposed"
        path = instance._get_latest_file("Proposed")
        # loading csv
        original = pd.read_csv(path).fillna('')
        # Returning it back in the original form 'see_new_plan' function had
        original = original.groupby(by=["Day", "Task"]).mean()
        # newpath = self._get_updated_path("CSV", start_date)
        #         original.to_csv(f"CSV of Plan on {start_date} v{path[-5]}.csv")
        return original

    def create_burndown_chart(self, data, max_hours=max_hours, start_date=datetime.now().strftime("%Y-%m-%d")):
        # Setting boundaries of matplotlib chart
        figure(num=None, figsize=(8, 6), dpi=80, facecolor='w', edgecolor='k')
        # x-values are the dates of the 'plan'
        xaxis = np.array(data.index.levels[0])
        # y-values are the cumulative sum of hours under the 'Amount Left' column
        yaxis = [data.loc[i].iloc[0]["Amount Left"] for i in xaxis]
        # labeling x-axis
        plt.xticks(rotation=90)
        # plotting bar graph
        plt.bar(xaxis, yaxis, color='lightgray')
        print(f"Below is the Proposed Plan from {xaxis[0]} to {xaxis[-1]}, Average Velocity: {max_hours} hours per day")
        print(f"Plan Proposed on {str(datetime.now())[:19]}")
        #         #Creating CSV Compatible Data
        #         lst =[[i,j] for i,j in zip(xaxis,yaxis)]
        #         export = pd.DataFrame(lst, columns = ["X-axis","Y-axis"]).to_csv(f"bdc data plan on {start_date} {str(time.time())[-3:-1]}.csv", index=False)
        return (xaxis, yaxis)

    def check_progress(self, datahandler, start_date):
        """
        This functions, determines what items got completed on the task list, and superimposes
        a line on top of the original burndown chart to show how current progress is going

        -------------------------------------------------------------------

        Parameters:
            datahandler - instance of DataHandler class
            start_date - start date of the project

        Returns:
            tuple - 4 arrays
                x values of bdc
                y values of bdc
                x values of progress line
                y values of progress line

        """
        ######### DETERMINING WHAT GOT COMPLETED #############

        # Pulling latest to-do list file
        df = datahandler.get_tasks_file(file=file)
        # Filtering only 'to-do' tasks to one variable, and organized columns
        dffalse = df[df["Completed"] == False][["Task", "ETA", "Completed", "Day"]]
        # Filtering only 'completed' tasks to one variable
        df2 = df[df["Completed"] == True][["Task", "ETA", "Completed", "Day"]]
        # Getting non-updated to-do list file
        df3 = datahandler.get_latest_tasks_file()[["Task", "ETA", "Completed", "Day"]]
        df3false = df3[df3['Completed'] == False]
        if '' in df3[df3['Completed'] == True]['Day'].values:
            raise Exception("Task marked as true but it does not have a completion date!")

        # Setting index of both dataframes by Task for easier searching
        df2 = df2.set_index("Task")
        df3 = df3.set_index("Task")
        df3false = df3false.set_index("Task")

        # Iterating over non-updated to-do list to see if the to-do is marked completed in the other dataframe
        # If a to do task is found to be complete on the newer list (df2), then the older task list will be updated (df3)
        # Note df3false is only being iterated because it has no completed tasks, which allows us to see what was completed
        for i in df3false.index:
            if i in df2.index:
                df3.loc[i, "Completed"] = True
                df3.loc[i, "Day"] = df2.loc[i, "Day"]
        df3 = df3.reset_index()  # Reverting back to original index

        ######### FILTERING DATA AFTER STARTING DATE #############

        # Splitting between completed and non-completed tasks
        tasks_left = df3[df3["Completed"] == False].reset_index().groupby(by=["Day", "Task"]).mean()
        tasks_comp = df3[df3["Completed"] == True]

        # Converting to datetime64 objects to prepare for comparison
        tasks_comp.loc[:, "Day"] = pd.to_datetime(tasks_comp["Day"])

        date = pd.to_datetime([start_date])

        # Comparison - filtering all dates that are after the start date
        tasks_comp = tasks_comp[tasks_comp["Day"].values >= date.values[0]]

        # Converting back to string objects instead of datetime64 objects
        tasks_comp["Day"] = [i.strftime("%Y-%m-%d") for i in tasks_comp["Day"]]

        # Checking if there's no new completed tasks
        if len(tasks_comp) == 0:
            raise Exception("Empty Dataset!")
        tasks_comp = tasks_comp.reset_index(drop=True).groupby(by=["Day", "Task"]).mean()

        ######### PREPARING TO GRAPH #############

        # Adding column 'Amount Left' to show reverse cumulative sum of the tasks.
        tasks_comp["Amount Left"] = np.array(list(tasks_comp["ETA"].loc[::-1].cumsum().shift(1).fillna(0))[::-1])
        # Getting Proposed plan to see how the original burndown chart looked like
        export = pd.read_csv(datahandler._get_latest_file("Proposed")).fillna('').set_index(["Day", "Task"])
        # Adjusting all reverse cumulative sum values of 'tasks_comp' so it matches that of the proposed plan
        tasks_comp["Amount Left"] += export["ETA"].sum() - tasks_comp.iloc[0]["Amount Left"]

        ########### GRAPHING DATA ####################

        # Grabbing the dates of the plan on the burndown chart
        xaxis = [i.strftime("%Y-%m-%d") for i in pd.date_range(export.index.levels[0][0], export.index.levels[0][-1])]

        # Setting burndown chart y-axis values: Placeholder used to keep the bar graph at the same level if theres a day that has no assigned work
        yaxis = []
        placeholder = 0
        for i in xaxis:
            if i not in export.index.levels[0]:
                yaxis.append(placeholder)
            else:
                placeholder = export.loc[i].iloc[0]["Amount Left"]
                yaxis.append(placeholder)

        # Setting x values of the completion line
        newXaxis = tasks_comp.index.levels[0].values

        # Getting corresponding y-values of line from x values
        newYaxis = tasks_comp.loc[:, "Amount Left"].values

        # Fitting the line according to the day the first task was completed
        ##Setting Datetimes of the line x values and of the start date
        xdatetime = [datetime.strptime(i, "%Y-%m-%d") for i in list(newXaxis)]
        startdatetime = datetime.strptime(start_date, "%Y-%m-%d")
        ##Getting how many days after starting date tasks got completed
        shift = (min(xdatetime) - startdatetime).days
        ##Getting total time since the start date
        ranged = (max(xdatetime) - min(xdatetime)).days

        # Converting x values (which were dates (str)) into numerical values
        numx = np.array(xdatetime) - xdatetime[0] + timedelta(days=shift)
        numx = [i.days for i in numx]

        # Start plotting

        ##Creating Burndown velocity: the line of best fit of all data points so far
        c = np.polyfit(numx, newYaxis, 1)
        x1 = np.array(range(ranged + shift, len(xaxis)))
        line = c[0] * x1 + c[1]

        # Plotting
        ##Determing window size of matplotlib
        fig = plt.figure(num=None, figsize=(10, 6), dpi=80, facecolor='w', edgecolor='k')
        plt.ylim(0, max(yaxis) + 10)
        plt.xticks(rotation=90, figure=fig)
        plt.bar(xaxis, yaxis, color='lightgray', figure=fig)
        plt.plot(newXaxis, newYaxis, linewidth=5, color="red", figure=fig)
        plt.plot(x1, line, color='black', linewidth=3, linestyle=':', figure=fig)
        # plt.plot(numx,newYaxis,'o', color='red', markersize =10)

        # Feedback on progess
        print(f"Below is the Current Progress for the dates {xaxis[0]} to {xaxis[-1]}")
        if newYaxis[len(newYaxis) - 1] < yaxis[len(newYaxis) - 1]:
            print(f"Good job!! You're ahead of schedule!")
        elif len(newYaxis) == 0:
            print("No data recorded yet!")
        elif newYaxis[len(newYaxis) - 1] == yaxis[len(newYaxis) - 1]:
            print("Right on time! Keep it up")
        else:
            print("We're behind! We have to work faster!")
        return newXaxis, newYaxis, x1, line

    def _day_blocks(self, df, max_hours=max_hours):
        lst2 = []
        freeze = 0
        a = df["ETA"]
        for i in range(len(a) + 1):
            df2 = df["ETA"].iloc
            if df2[freeze:i].sum() > max_hours:
                increment = 0
                if df2[freeze:i + increment + 1].drop(i - 1).sum() < max_hours:
                    while df2[freeze:i + increment + 1].drop(i - 1).sum() < max_hours:
                        check = df2[freeze:i + increment + 1].drop(i - 1)
                        increment += 1
                        if check.equals(df2[freeze:i + increment + 1].drop(i - 1)):
                            break
                    temp = df.iloc[i - 1]
                    df.iloc[i - 1:i + increment + 1] = df.iloc[i - 1:i + increment + 1].shift(-1).fillna(temp)
                    # print(df.iloc[i-1:i+increment+1])
                    lst2.append(df.iloc[freeze:i + increment - 1])
                    freeze = i + increment - 1
                else:
                    lst2.append(df.iloc[freeze:i - 1])
                    freeze = i - 1
        lst2.append(df.iloc[freeze:])
        return lst2

    def _get_updated_path(self, instance, first_word, start_date,
                          path='/Users/owner/Desktop/Datasets/TaskIntegrator/*'):
        """When making new copies of """
        # Get proper naming
        paths = instance._get_latest_file("Proposed", path)

        if paths[-7:-5] != " v":
            return "There is an issue with naming the file. There is no version label (vx)"
        if paths[-4:] == ".txt":
            extension = ".txt"
        if paths[-4:] == ".csv":
            extension = ".csv"

        assert len(
            pd.Series([i if str(datetime.now().year) in i else "Invalid" for i in paths.split(' ')]).drop_duplicates(
                keep=False)) != 0, "Invalid Date Time on file"
        file_date = pd.Series(
            [i if str(datetime.now().year) in i else "Invalid" for i in paths.split(' ')]).drop_duplicates(keep=False)

        position, file_date = file_date.index[0], file_date.values[0]

        file_datetime = datetime.strptime(file_date, "%Y-%m-%d")
        start_datetime = datetime.strptime(start_date, "%Y-%m-%d")

        if start_datetime == file_datetime:
            newpaths = paths[:-5] + str(int(paths[-5]) + 1) + extension
            return newpaths
        elif start_datetime > file_datetime:
            pathslst = paths.split(' ')
            pathslst[position] = start_date
            pathslst[-1] = "v1" + extension
            newpaths = ' '.join(pathslst)
            return newpaths
        elif start_datetime < file_datetime:
            return "There is apparently a more recent proposed plan"