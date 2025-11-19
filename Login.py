from Interface import LoginInterface

class Loginpage(LoginInterface):
    def __init__(self):
        self.__username=""
        self.__password=""
    
    def check_username(self,username):
        if not username:            #if username is empty
            return False
        if len(username)<5:
            return False
        if username[0].isupper():
            return True
        return False
    
    def check_password(self, password):
        if len(password) < 8:
             return False

        Alpha = any(ch.isalpha() for ch in password)     #any is inbuilt function to checks iterable and return T or F
        Digit = any(ch.isdigit() for ch in password)
        Special = any(not ch.isalnum() for ch in password)

        return Alpha and Digit and Special
    
    def Login(self):
        try:
            self.__username = input("Enter your Username: ")

            if not self.check_username(self.__username):
                print("Invalid Username.")
                return None

            self.__password = input("Enter your Password: ")
            if not self.check_password(self.__password):
                print("Invalid Password.")
                return None

            print("Login successfully.......")
            return self.__username

        except ValueError:
            print("Invalid login credentials...")
            return None
