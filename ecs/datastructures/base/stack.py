import unittest
from ecs.datastructures.base.doubly_linked_list import DoublyLinkedList

class Stack:
    """
    GROUP A: Stack/Queue operations

    A stack is a datastructure that servers as a collection of elements.
    It utilises a LIFO datastructure (Last in, First Out)
    
    No need for pointers as the linked list has O(1) insertion for first and last element.
    """

    def __init__(self):
        self.__data = DoublyLinkedList()

    def push(self, *values):
        """pushes all arguments onto the stack."""
        for value in values:
            self.__data.add_first(value)

    def pop(self):
        """removes and returns the item at the top of the stack."""
        # remove_first method will return None if the list is empty so no need for empty check
        return self.__data.remove_first()

    def peek(self):
        """returns the item at the top of the stack without removing the item"""
        return self.__data.peek_first()

    def is_empty(self):
        """returns True if the stack is empty else False"""
        return len(self) == 0

    def __len__(self):
        return len(self.__data)

    def __str__(self):
        return f"{repr(self)}: {self.__data.to_array()}"

    def __repr__(self):
        return f"<Stack(size={len(self)}, top={self.peek()})>"

class TestStack(unittest.TestCase):
    def setUp(self):
        self.stack = Stack()
    
    def test_push(self):
        self.stack.push(10, 9, 8, 7, 6, 5, 4, 3, 2, 1)

        # Check stack values are as expected
        self.assertEqual(len(self.stack), 10)
        self.assertEqual(self.stack.peek(), 1)

    def test_pop(self):
        # Test that popping returns None
        self.assertIsNone(self.stack.pop())

        # Populate stack
        self.stack.push(10, 9, 8, 7, 6, 5, 4, 3, 2, 1)

        # pop value for each value checking it is the correct value
        for count in range(len(self.stack)):
            self.assertEqual(self.stack.pop(), count + 1)

    def test_is_empty(self):
        # Test if basic empty works
        self.assertTrue(self.stack.is_empty())
        
        # populate
        self.stack.push(10)

        # test if empty logic correct
        self.assertFalse(self.stack.is_empty())

        # check if popping correctly influnences size
        self.stack.pop()
        self.stack.pop()
        self.stack.pop()
        self.assertTrue(self.stack.is_empty())

if __name__ == '__main__':
    unittest.main(verbosity=2)