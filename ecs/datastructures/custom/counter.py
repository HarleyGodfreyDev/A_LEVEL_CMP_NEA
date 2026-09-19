class Counter:
    """
    Creates a instance that when called increments a private count attribute by one then returns the attribute.

    Abstracts simple functionality into a clean utility datastructure.
    """

    def __init__(self):
        self.__count = 0

    def __call__(self):
        self.__count += 1
        return self.__count

    def __repr__(self):
        return f"<Counter({self.__count})>"