foo = 100

def hello():
  print("i am from my_module.py")

if __name__ == "__main__":
    print("Executando o programa main")
    print("O valor de __name__ é: ", __name__)
    hello()
