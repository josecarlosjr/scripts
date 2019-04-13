#este codigo mostra o uso de decorators avancados
# decorators avancados podem passar argumentos

import sys
import functools

def decorator_with_arguments(number):
    def my_decorator(func):
        @functools.wraps(func)
        def function_that_runs_func():
            print("in the decorator")
            if number == 56:
                print("o argumento é 56")
            else:
                func()
            print("afte the decorator")
            return function_that_runs_func
        return my_decorator


@decorator_with_arguments(56)
def my_function():
    print("hello")
    
my_function()
