import unittest
from ecs.datastructures.records.archetype_record import ArchetypeRecord

from ecs.datastructures.custom.archetype import Archetype


class ArchetypeIndex:
    """
    GROUP A:
        Complex user-defined use of object-orientated programming (OOP) model (interface?)
    """

    def __init__(self):
        self.__archetypes = {} # The archetype indexs data

    def register(self, archetype: Archetype):
        """Registers a archetype to the archetype_index with validation. """
        if not isinstance(archetype, Archetype):
            raise ValueError(f"Invalid archetype type of {type(archetype)} instead of archetype.")

        archetype_record = self.__archetypes[archetype.type] = ArchetypeRecord(archetype)
        return archetype_record

    def archetype_record(self, components: tuple[int]) -> Archetype:
        """Returns an archetype from the archetype index. """
        if not isinstance(components, tuple):
            # If a single entity then cat into components
            components = (components,)

        if len(components) < 1:
            # Ensure correct length of components
            raise ValueError(f"Invalid components passed into archetype lookup, components must have atleast 1 component: {components}")

        if not isinstance(components[0], int):
            # Check first component for extra validity
            if isinstance(components[0], tuple):
                # In cases where tuple might have been added as tuple of tuple
                self.archetype(components[0])
            else:
                raise ValueError(f"Invalid components passed into archetype lookup, components must be int: {components}")

        return self.__archetypes.get(components)

    def all_archetypes(self):
        """Returns all archetypes in the archetype_index"""
        return [archetype_record.archetype for archetype_record in self.__archetypes.values()]

    # -- archetype_record shortcuts --

    def archetype(self, components: tuple[int]) -> Archetype:
        """Returns the archetype for archetype_type"""
        archetype_record = self.archetype_record(components)
        return archetype_record.archetype if isinstance(archetype_record, ArchetypeRecord) else None

    def archetype_cache(self, archetype_type: tuple[int] | Archetype) -> Archetype:
        """Returns the archetype_cache for archetype_type / archetype"""

        if isinstance(archetype_type, Archetype):
            # Convert incase it's an archetype
            archetype_type = archetype_type.type

        archetype_record = self.archetype_record(archetype_type)
        return archetype_record.archetype_cache if isinstance(archetype_record, ArchetypeRecord) else None

    def __repr__(self):
        return str(self.__archetypes)

class TestArchetypeIndex(unittest.TestCase):
    def setUp(self):
        self.archetype_index = ArchetypeIndex()

    def test_register(self):
        with self.assertRaises(ValueError):
            self.archetype_index.register("InvalidArchetype")
        
        archetype_type = (1,2,3)
        archetype = Archetype(archetype_type, list(), list(), list())
        archetype_record = self.archetype_index.register(archetype)

        self.assertIsInstance(archetype_record, ArchetypeRecord)
        self.assertIn(archetype, self.archetype_index.all_archetypes())

    def test_archetype_record(self):
        archetype = Archetype((1,), list(), list(), list())
        archetype_record = self.archetype_index.register(archetype)

        archetype = Archetype((1,2,3), list(), list(), list())
        archetype_record = self.archetype_index.register(archetype)

        # Test that single component does / does not error
        self.assertIsInstance(self.archetype_index.archetype_record(1), ArchetypeRecord)

        # Test that multiple components does / does not error
        self.assertIsInstance(self.archetype_index.archetype_record((1,2,3)), ArchetypeRecord)

        # Test that nested tuples does / does not error
        self.assertIsInstance(self.archetype_index.archetype_record(((1,2,3))), ArchetypeRecord)
        
        # Test validation
        with self.assertRaises(ValueError):
            self.archetype_index.archetype_record(())

        with self.assertRaises(ValueError):
            self.archetype_index.archetype_record(("Pauleen"))

    def test_shortcuts(self):
        archetype = Archetype((1,), list(), list(), list())
        archetype_record = self.archetype_index.register(archetype)

        self.assertIsInstance(self.archetype_index.archetype(1), Archetype)
        self.assertIsInstance(self.archetype_index.archetype_cache(1), dict)

if __name__ == '__main__':
    unittest.main(verbosity=2)