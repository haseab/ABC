import pandas as pd
from datetime import datetime, timedelta
import glob
import os

class DataHandler:
    def __init__(self, file):
        self.file = file
        self.path = os.getcwd() + '\\*'

    def save_data(self, df):
        """
        Saves the dataframe to a csv in the same directory
        Parameters:
            df: dataframe
        Returns:
            str - file name
        """
        dt = datetime.now()
        file = f"Tasks {dt.year}_{dt.month}_{dt.day}_{dt.hour}.txt"
        df.to_csv(file, index=False)
        string = "Saved Data as: " + file
        print(string)
        return file

    def get_tasks_file(self, file=None):
        """
        Reads the to-do list (which is in csv format) and then sorts from Completed Tasks First
        Parameters:
            file - csv file that will be turned into a pandas DataFrame

        Returns:
            df - pd.DataFrame object
        """
        # Check if file has been passed as an argument
        if file is None:
            file = self.file

        # Reading of CSV
        df = pd.read_csv(self.file).fillna('')
        # Converting "Yes" and "No" Values into True and False Booleans instead
        df['Day'] = [str(i)[:10] for i in pd.to_datetime(df['Day']).fillna('')]
        # Placing all Completed Tasks at the top of the list and then followed by Not Completed Tasks
        df = pd.concat([df[df["Completed"] == True], df[df["Completed"] == False]]).reset_index(drop=True)
        return df

    def get_latest_tasks_file(self):
        """
        This method searches for the latest copy of the to-do list that was saved and returns it
        (Note it does not return the current version, but the last copied version)
        
        Instead of passing an argument of the file name, it uses the os module
        to determine the most recently modified txt file in the folder and returns that

        Returns:
            df - dataframe
        """
        # Calling function to get most recent file
        file = self._get_latest_file("Tasks")
        # Reading csv and filling Na values with blank strings
        df = pd.read_csv(file).fillna('')
        # Converting date list into datetime objects, and then back into strings (for standardization)
        df['Day'] = [str(i)[:10] for i in pd.to_datetime(df['Day']).fillna('')]
        return df

    def update_tasks(self, file=None):
        """
        There are two types of task files:
            1. CSV where changes are updated
            2. Cached Tasks list saved as a txt to be used as reference

        This function compares the two task lists and indicates what is different
        between the two lists and what specifically changed. The format is as follows

        >>> update_tasks()
        DATA CHANGED,
        Task:      Inspecting system
        Column:    Completed
        Old Value: False
        New Value: True
        Are you sure you want to continue with the above changes? y/n

        Returns:
            Original Dataset if nothing is changed
            tuple of dataset with a counter
        """
        # Checking for argument being passed
        if file is None:
            file = self.file

        # Getting cached task list, df (datframe)
        df = self.get_latest_tasks_file().fillna('')
        # Getting updating task list, ndf (new dataframe)
        ndf = self.get_tasks_file(file)

        # Creating a copy of both dataframes
        # Setting the index of both dataframes as the task for easier coding
        # It will be changed back once the comparison is done
        df2 = df.set_index("Task")
        ndf2 = ndf.set_index("Task")
        totalcount, counter2 = 0, 0

        # Dataframes without task as index, split into completed and not completed
        dftrue = df2[df2["Completed"] == True]
        ndftrue = ndf2[ndf2["Completed"] == True]
        dffalse = df2[df2["Completed"] == False]
        ndffalse = ndf2[ndf2["Completed"] == False]

        # Iterating through originally to-do tasks
        for i in dffalse.index:
            # Checking if tasks went from to-do to completed
            if i not in ndffalse.index and i in ndftrue.index:
                print(f"Task Completed: {i}")
                counter2 += 1
            # Checking if tasks went from to-do to being removed completely
            if i not in ndffalse.index and i not in ndftrue.index:
                print(f"Task Removed from To-Do: {i}")
                counter2 += 1

        for i in dftrue.index:
            # Checking if task went from completed to to-do
            if i not in ndftrue.index and i in ndffalse.index:
                print(f"Task Uncompleted: {i}")
                counter2 += 1
            # Checking if tasks went from completed to being removed completely
            if i not in ndffalse.index and i not in ndftrue.index:
                print(f"Task Removed from Completed: {i}")
                counter2 += 1

        # Iterating through the new to-do list
        for i in ndffalse.index:
            # Checking to see any new to-do's that weren't in the original to-do
            if i not in dffalse.index and i not in dftrue.index:
                print(f"Task added to to-do list: {i}")
                counter2 += 1

        # Iterating through the new completed list
        for i in ndftrue.index:
            # Checking to see if anything got added to "completed" without being a to-do first
            if i not in dffalse.index and i not in dftrue.index:
                print(f"Task added to completed without being on to-do list: {i}")
                counter2 += 1

        # Calling function that sees if any values were changed
        taskdf, counter = self._data_change_tracker(df, ndf)

        # If any changes were made, the counters should have integer values
        totalcount = counter + counter2
        if totalcount == 0:
            print("\nNothing happened")
            return df, 1
        else:
            # The changes are shown in a printout, and the following question is asked
            inputs = input("Are you sure you want to continue with the above changes? y/n")
            if inputs in ["Y", "y", "yes", "Yes", "YES", "YEs"]:
                print("Items added to new list!")


#                 # Merging completed and to-do list
#                 df3 = ndftrue.merge(ndffalse, how="outer").reset_index(drop=True).drop_duplicates(subset="Task")
                return ndf, 0

            else:
                print("Returning original dataset")
                return df, 1

    def update_tasks_to_csv(self, file=None):
        """
        Wrapper function of "update_tasks" function. This one saves changes as a csv
        """
        if file is None:
            file = self.file

        df, count = self.update_tasks(file)
        if count == 1:
            print("Nothing was saved")
            return None
        text = self.save_data(df)
        return df, count

    def _data_change_tracker(self, df, ndf):
        """Checks to see if any specific values of the table have been changed
           Parameters:
               df: old task list
               ndf: new task list

            Returns: Combined dataframe of both old and new dataframes
        """

        taskdf = df.merge(ndf, how="inner", on="Task").set_index("Task")
        col = taskdf.columns.values
        counter = 0
        #
        for i in range(int(len(col) / 2)):
            check = (taskdf[col[i]] == taskdf[col[i + int(len(col) / 2)]])
            if (check).all() == False:
                counter += 1
                for j in check.index:
                    if check[j] == False:
                        value = taskdf.loc[j][[col[i], col[i + int(len(col) / 2)]]].values
                        print(
                            f"\nDATA CHANGED,  \nTask:\t   {j} \nColumn:    {col[i][:-2]} \nOld Value: {value[0]} \nNew Value: {value[1]}")
        if counter == 0:
            print("\nData is identical. No Data changed")
        return taskdf, counter

    def _get_latest_file(self, first_word, path=None):
        """Gets the name of the most recently modified .txt file in the directory.
            Parameters
                first_word - the first word of the file. This is to minimize risk of picking a the wrong
                            .txt file that happened to be modified recently
                path - the file directory you want to explore

            Returns:
                the last element (most recent) of the list of file names
        """
        if path is None:
            path = self.path

        list_of_files = glob.iglob(path)  # * means all if need specific format then *.csv
        latest_file = sorted(list_of_files, key=os.path.getctime)
        latest_file = [i.split("\\")[-1] for i in latest_file]  # Slicing
        # Gathering list of files that are under the first name
        latest_file2 = [i for i in latest_file if first_word in i]
        #         inputs = input(f"File read was {latest_file[-1]}. Proceed? (y/n): ")
        #         if inputs in ["Y","y","yes","Yes","YES", "YEs"]:
        #             return latest_file[-1]
        #         else:
        #             return "Canceled operation"

        if len(latest_file2) == 0:
            return f"No files of word {first_word} in the path {path}"
        return latest_file2[-1]
