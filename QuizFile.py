import os 
folder_path="C:/Users/Bhagya/OneDrive/Desktop/code/CPP_tasks_for_engineers/Python/QuizApp"

File_name="QuizQuestions.txt"
file_path = os.path.join(folder_path, File_name)
with open(file_path,'w')as f:
    f.write("What is the primary goal of Object-Oriented Programming (OOP)?\nCode reusability and modularity|Efficient memory utilization|Procedural abstraction|Dynamic typing\n3\n\nIn Python, what is a class?\nfunction|module|code block|blueprint for creating objects\n4")
with open(file_path,'a')as f:
    f.write("\n\nWhich keyword is used to achieve method overloading in Python?\noverload|method|override|Python does not support method overloading\n4\n\nWhat is a metaclass in Python?\nA class that inherits from multiple classes|A class for creating classes|A class that cannot be instantiated|A class that overrides all methods in a superclass\n2")
with open(file_path,'r')as f:
    print(f.read())

folder_path1="C:/Users/Bhagya/OneDrive/Desktop/code/CPP_tasks_for_engineers/Python/QuizApp"

File_name1="Result.txt"
file_path1 = os.path.join(folder_path1, File_name1)
with open(file_path1,'w')as f1:
    pass
with open(file_path1,'r')as f1:
    print(f1.read())
folder_path2="C:/Users/Bhagya/OneDrive/Desktop/code/CPP_tasks_for_engineers/Python/QuizApp"
File_name2="Result.xls"
file_path2 = os.path.join(folder_path2, File_name2)
with open(file_path2,'w')as f2:
    pass
with open(file_path2,'r')as f2:
    print(f2.read())
