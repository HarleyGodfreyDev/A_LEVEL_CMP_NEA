import unittest
from ecs.datastructures.custom.counter import Counter
from ecs.datastructures.base.stack import Stack
from ecs.datastructures.helpers.bitmanipulation import BitmanipulationHelper

class Graveyard:
    """
    GROUP A:
        stack/queue operations
    
    A custom datastructure for generating unique entity identifers with recycling.
    Custom version system in the form of generations.
    """

    def __init__(self):
        self.__counter = Counter()
        self.__bin = Stack()

    def kill(self, entity: int):
        """Adds a entity to the graveyard."""
        if isinstance(entity, int):
            self.__bin.push(entity)
        else:
            raise ValueError(f"Invalid entity type of {type(entity)} instead of int.")

    def __call__(self, revive: bool) -> int:
        """Returns a unique entity identifer"""
        if revive and not self.__bin.is_empty():
            # Return item from top of the stack with an incremented generation
            return BitmanipulationHelper().increment_generation(self.__bin.pop())
        return self.__counter()

class TestGraveyard(unittest.TestCase):
    def setUp(self):
        self.graveyard = Graveyard()

    def test_autoincremented(self):
        for count in range(1, 100):
            entity = self.graveyard(revive=False)
            self.assertIsInstance(entity, int)
            self.assertEqual(entity, count )

    def test_revive(self):
        self.graveyard.kill(500)
        
        # Test counter works as expected with revive False
        self.assertEqual(self.graveyard(revive=False), 1)

        # Revive the entity
        entity = self.graveyard(revive=True)
        self.assertNotEqual(entity, 2) # Check value was not incremented
        self.assertNotEqual(entity, 500) # Check that the value has some form of encoding
        self.assertEqual(BitmanipulationHelper().decode_entity(entity), 500) # Check correct value was recycled
        self.assertEqual(BitmanipulationHelper().decode_generation(entity), 1) # Ensure generation was incremented correctly

        # Recycle entity to check incrementing is working correctly
        self.graveyard.kill(entity)
        entity = self.graveyard(revive=True)
        self.assertEqual(BitmanipulationHelper().decode_entity(entity), 500) # Check correct value was recycled
        self.assertEqual(BitmanipulationHelper().decode_generation(entity), 2) # Ensure generation was incremented correctly

if __name__ == '__main__':
    unittest.main(verbosity=2)