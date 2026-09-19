import unittest
from ecs.datastructures.base.doubly_linked_list import DoublyLinkedList

class Queue:
    """
    GROUP A: Stack/Queue operations

    A queue is a datastructure that servers as a collection of elements.
    It utilises a FIFO datastructure (First in, First Out)
    
    """

    def __init__(self):
        self.__data = DoublyLinkedList()

    def enqueue(self, *values):
        """enqueues all arguments onto the end of the queue. """
        for value in values:
            self.__data.add_last(value)

    def dequeue(self):
        """removes and returns the first item in the queue. """
        return self.__data.remove_first()

    def peek(self):
        """returns the item at the top of the queue without removing the item. """
        return self.__data.peek_first()

    def is_empty(self):
        """returns True if the stack is empty else False"""
        return len(self) == 0

    def __len__(self):
        return len(self.__data)

    def __str__(self):
        return f"{repr(self)}: {self.__data.to_array()}"

    def __repr__(self):
        return f"<Queue(size={len(self)}, top={self.peek()})>"

class TestStack(unittest.TestCase):
    def setUp(self):
        self.queue = Queue()

    def test_enqueue(self):
        self.queue.enqueue(10, 9, 8, 7, 6, 5, 4, 3, 2, 1)

        # Check stack values are as expected
        self.assertEqual(len(self.queue), 10)
        self.assertEqual(self.queue.peek(), 10)

    def test_dequeue(self):
        # Test dequeue returns None and does not errror
        self.assertIsNone(self.queue.dequeue())

        # Populate queue
        self.queue.enqueue(10, 9, 8, 7, 6, 5, 4, 3, 2, 1)
    
        # dequeue value for each value checking if it is the correct value
        for count in range(len(self.queue)):
            self.assertEqual(self.queue.dequeue(), 10 - count)

    def test_is_empty(self):
        # Test if basic empty works
        self.assertTrue(self.queue.is_empty())
        
        # populate
        self.queue.enqueue(10)

        # test if empty logic correct
        self.assertFalse(self.queue.is_empty())

        # check if popping correctly influnences size
        self.queue.dequeue()
        self.queue.dequeue()
        self.queue.dequeue()
        self.assertTrue(self.queue.is_empty())

if __name__ == '__main__':
    unittest.main(verbosity=2)