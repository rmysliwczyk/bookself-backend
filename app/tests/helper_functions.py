import random

def get_random_string(n=10):
    return "".join([chr(random.randrange(65, 91)) for _ in range(n)])
