class QuizQuestions:
    def __init__(self, question, options, correct_ans):
        self.question = question
        self.options = options
        self.correct_ans = correct_ans
        self.user_answer = None
        self.user_comment = ""
    
    def display(self):
        print(f"\n{self.question}")
        i = 1
        for option in self.options:
            print(f"{i}. {option}")
            i += 1

    def QuizAnswer(self,index):
        choice = input(f"Enter your answer for Q{index+1} :")
        if choice.strip() != "" :
            value= int(choice)
            if 1 <= value <= 4:
                self.user_answer = value
                
            else:
                print(" Invalid choice.")
        self.user_comment = input("Write your explaination here:  ")

    def is_correct(self):
        return self.user_answer == self.correct_ans
    