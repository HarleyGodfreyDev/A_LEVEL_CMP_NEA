from loguru import logger
import unittest
from dataclasses import dataclass, field

logger.add(
    sink="logs/entity_component_system.log",
    mode="w",
    level="DEBUG",
    format="{elapsed} | {level} | {function} | {line} | {message}",
    colorize=True,
    rotation="1 MB",  # Rotate log file after it reaches 1 MB
    retention="10 days",  # Retain logs for 10 days
    compression="zip",  # Compress rotated logs
)

class DoublyLinkedList:
    """
    GROUP A: 
        Linked List maintenance
        List Opeations
        Complex user-defined use of object-orientated programming (OOP) model
        Mult-dimesonal arrays (Not sure if using Nodes counts towards this.)

    Time complexity:

                  Average      Worst
        Access:     O(n)        O(n)
        Search:     O(n)        O(n)
        Insertion:  O(1)        O(1) 
        Deletion:   O(1)        O(1)

    A doubly linked list is effective of insertion and deletion operations having a
    constant time complexity compared to a typical arrays linear time complexity.
    """

    @dataclass
    class Node:
        value: int
        next: object | None = field(default=None)
        previous: object | None = field(default=None)

        def is_head(self):
            return self.previous is None

        def is_tail(self):
            return self.next is None

        def __repr__(self):
            """String representation of node used for logging / debugging"""
            identifer = "Head" if self.is_head() else "Tail" if self.is_tail() else "Node"
            return f"<{identifer}(value={self.value})>"

    def __init__(self):
        self.head = None
        self.tail = None
        self.__size = 0 # keep track of the size of the lis

    def add_first(self, value):
        """Add an item to the front of the linked list"""

        if not self.head:
            # No head / tail, set both equal to the node value
            self.head = self.tail = DoublyLinkedList.Node(value)
            self.__size += 1
        else:
            previous_head = self.head
            self.head = DoublyLinkedList.Node(value, next=previous_head)
            previous_head.previous = self.head
            self.__size += 1

    def add_last(self, value):
        """Add an item to the end of the linked list"""
        if not self.head:
            # No head / tail, set both equal to the node value
            self.head = DoublyLinkedList.Node(value)
            self.tail = self.head
            self.__size += 1
        else:
            previous_tail = self.tail
            self.tail = DoublyLinkedList.Node(value, previous=previous_tail)
            previous_tail.next = self.tail
            self.__size += 1

    def insert_before(self, index, value):
        """Insert a value into the linked list before the node at a given index"""

        if index == 0: return self.add_first(value) # if index is 0 then add to start

        current_node = self.__get(index) # get the current node at the index we are inserting
        
        # The next is the current_node and it takes the previous from the current_node
        insertion_node = DoublyLinkedList.Node(value, next=current_node, previous=current_node.previous)

        # The new nodes previouses next needs to be the insertion node
        insertion_node.previous.next = insertion_node

        # The current nodes previous should be updated to the insertion node
        current_node.previous = insertion_node

    def insert_after(self, index, value):
        """Insert a value into the linked list after the node at a given index"""
        if index == len(self): return self.add_last(value)
        
        current_node = self.__get(index)

        # The next is the next of the current_node and the previous is the current_node
        insertion_node = DoublyLinkedList.Node(value, next=current_node.next, previous=current_node)

        # The current_nodes nexts previous is now you
        insertion_node.next.previous = insertion_node

        # The current nodes next should be updated to the insertion node
        current_node.next = insertion_node

    def remove_first(self):
        """Remove the first item in the linked list"""

        if self.head is None:
            # Nothing to remove
            return None
        elif self.head == self.tail:
            # Only item within the list
            return_value = self.head.value
            self.head = self.tail = None
            self.__size -= 1
            return return_value
        else:
            return_value = self.head.value
            self.head = self.head.next 
            self.head.previous = None
            self.__size -= 1
            return return_value

    def remove_last(self):
        """Remove the last item in the linked_list"""

        if not self.tail:
            # Nothing to remove
            return None
        elif self.head == self.tail:
            # Only item within the list
            return_value = self.head.value
            self.head = self.tail = None
            self.__size -= 1
            return return_value
        else:
            return_value = self.tail.value
            self.tail = self.tail.previous
            self.tail.next = None
            self.__size -= 1
            return return_value

    def peek_first(self):
        """Returns the first value in the linked list"""
        return None if not hasattr(self.head, "value") else self.head.value

    def peek_last(self):
        """Returns the last value in the linked list"""
        return None if not hasattr(self.tail, "value") else self.tail.value

    def to_array(self):
        """Returns the linked list as an array"""
        return [value for value in self]

    def __get(self, index):
        """
        Returns the node at a given index.
        
        Reduced time complexity of search to O(log n) by searching through the half the index is closest to.
        """

        # Index out of range
        if index < 0 or index > self.__size:
            raise IndexError

        # If index is 0 then it's the head
        elif index == 0: return self.head
        # If index is len(self) it's the tail
        elif index == len(self): return self.tail

        if index < len(self) // 2:
            # Index is closer to head
            current_node = self.head
            current_index = 0

            while current_index != index:
                current_node = current_node.next
                current_index += 1
        else:
            # Index is closer to tail
            current_node = self.tail
            current_index = 0

            while current_index != index:
                current_node = current_node.previous
                current_index += 1
        
        return current_node

    def __getitem__(self, index):
        """Returns the value of a node at a given index"""
        return self.__get(index).value

    def __iter__(self):
        """Called when iteration begins, sets current iterating node to the head"""
        self.__iter_node = self.head  
        return self

    def __next__(self):
        """Returns the value of the node being iterated over and sets iter node to next"""
        if not self.__iter_node: raise StopIteration
        return_value = self.__iter_node.value
        self.__iter_node = self.__iter_node.next
        return return_value

    def __len__(self):
        return self.__size

    def __bool__(self):
        return self.__size != 0

    def __str__(self):
        """Detailed representation of the linked list for debugging and logging"""
        if not self.head:
            return repr(self)

        current_node = self.head
        display_string = f"{repr(self)}: {current_node}"
        while current_node.next:
            current_node = current_node.next
            display_string += f" --> {current_node}"
        return display_string

    def __repr__(self):
        return f"<DoublyLinkedList(size={len(self)})>"

class TestDoublyLinkedList(unittest.TestCase):
    def setUp(self):
        """Setup for tests"""
        self.linked_list = DoublyLinkedList()

    def test_add_first(self):
        # Test adding first from nothing
        self.linked_list.add_first(10)

        # Check they're equal
        self.assertEqual(self.linked_list.to_array(), [10])

        # Check bulk add_first
        for count in range(9, 0, -1):
            self.linked_list.add_first(count)

        # Check against expected result
        self.assertEqual(self.linked_list.to_array(), [1,2,3,4,5,6,7,8,9,10])

    def test_add_last(self):
        # Test adding last from nothing
        self.linked_list.add_first(10)

        # Check they're equal
        self.assertEqual(self.linked_list.to_array(), [10])

        # Check bulk add_last
        for count in range(9, 0, -1):
            self.linked_list.add_last(count)

        # Check against expected result
        self.assertEqual(self.linked_list.to_array(), [10,9,8,7,6,5,4,3,2,1])

    def test_insert_before(self):
        # Populate the linked list for testing [1,2,3,4,5]
        for count in range(5, 0, -1):
            self.linked_list.add_first(count)

        # before index 2 (value of 3) insert 2.5
        self.linked_list.insert_before(index=2, value=2.5)

        # Check against expected result
        self.assertEqual(self.linked_list.to_array(), [1,2,2.5,3,4,5])

        # boundary test (insert before first index)
        self.linked_list.insert_before(index=0, value=0)
        self.assertEqual(self.linked_list.to_array(), [0,1,2,2.5,3,4,5])

    def test_insert_after(self):
        # Populate the linked list for testing [1,2,3,4,5]
        for count in range(5, 0, -1):
            self.linked_list.add_first(count)

        # after index 1 (value of 2) insert 2.5
        self.linked_list.insert_after(index=1, value=2.5)
        self.assertEqual(self.linked_list.to_array(), [1,2,2.5,3,4,5])

        # boundary test (insert after last index)
        self.linked_list.insert_after(index=5, value=6)
        self.assertEqual(self.linked_list.to_array(), [1,2,2.5,3,4,5,6])

    def test_remove_first(self):
        # Remove from empty list
        self.assertIsNone(self.linked_list.remove_first())
    
        # Populate the linked list for testing [1,2,3,4,5]
        for count in range(5, 0, -1):
            self.linked_list.add_first(count)

        # remove_first for each item in the linked list and check if it is the expected value
        for count in range(4):
            self.assertEqual(self.linked_list.remove_first(), count + 1)

    def test_remove_last(self):
        # Remove from empty list
        self.assertIsNone(self.linked_list.remove_last())
    
        # Populate the linked list for testing [1,2,3,4,5]
        for count in range(5, 0, -1):
            self.linked_list.add_first(count)

        # remove_first for each item in linked list and check if it is the expected value
        for count in range(4):
            self.assertEqual(self.linked_list.remove_last(), 5 - count)

    def test_peek(self):
        # Should both return None as nothing on the list
        self.assertIsNone(self.linked_list.peek_first())
        self.assertIsNone(self.linked_list.peek_last())

        # populate list
        self.linked_list.add_first(100)

        # both should be 100
        self.assertEqual(self.linked_list.peek_first(), 100)
        self.assertEqual(self.linked_list.peek_last(), 100)

        self.linked_list.add_first(0)

        # Check both work with multiple values
        self.assertEqual(self.linked_list.peek_first(), 0)
        self.assertEqual(self.linked_list.peek_last(), 100)

    def test_len(self):

        # Populate with 10 values
        for count in range(10):
            self.linked_list.add_first(count)

        # Test len is correct
        self.assertEqual(len(self.linked_list), 10)

        # remove 5 values
        for count in range(5):
            self.linked_list.remove_first()
        
        # test len is correct
        self.assertEqual(len(self.linked_list), 5)

    # Obselete to test to_array() as used in tests
    # Obselete to test iterable as used in tests

if __name__ == '__main__':
    unittest.main(verbosity=2)

