#Note:The template file will be copied to a new file. When you change the code of the template file you can create new file with this base code. 
#entendendo um decorator
# fonte udemy

import sys
import os
import functools #cria um decorator atraves do functools 

# um decorator é uma funcao que chama outra funcao

#2- o decorator @my_decorator ira chamar
# a funcao def my_decorator passando
#a funcao def my_function como argumento
# ou seja my_function = func logo em seguida
# ira chamar a funcao que roda func

def my_decorator(func):
    @functools.wraps(func)
    def function_that_runs_func():
        print("antes da funcao")#primeiro
        func()
        print("depois da funcao")#terceiro
        return function_that_runs_func


#1- ao criar uma funcao com um
#decorator ela irar executar primeiro
#a funcao my_decorator

@my_decorator
def my_function():
    print("my function")# segundo
   
my_function()
