import sys

#this is a custom exception class what it does is it will give the error message in a better format
def error_message_detail(error,error_detail:sys):
    _,_,exc_tb=error_detail
    file_name=exc_tb.tb_frame.f_code.co_filename
    error_message = "Error occured in python script name [{0}] line number [{1}] error message [{2}]".format(
        file_name,exc_tb.tb_lineno,str(error),
    )
    return error_message

#this is a custom exception class it will inherit the exception class
class CustomException(Exception):
    def __init__(self,error_message,error_detail:sys):
        super().__init__(error_message) #this will call the constructor of the parent class
        self.error_message=error_message_detail(error_message,error_detail=error_detail)

    def __str__(self):
        return self.error_message
