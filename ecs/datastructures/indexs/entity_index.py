import unittest
from loguru import logger

from ecs.datastructures.helpers.bitmanipulation import BitmanipulationHelper

from ecs.datastructures.records.entity_record import EntityRecord
from ecs.datastructures.records.component_record import ComponentRecord

from ecs.datastructures.custom.archetype import Archetype

class EntityIndex:
    """
    GROUP A:
        Complex user-defined use of object-orientated programming (OOP) model: (interface?)
        multi-dimesonal hash-table
    

    The entity_index is a container datastructure for all entities and their entity data.
    The container provides validation and consistent checking aswell as dynamic lookups.
    The entity_record can be lookedup through their entity_id. The entity_id can be lookedup through a name.
    """

    def __init__(self):
        self.__entities = {}    # Maps the entity_id to the entity_record
        self.__name_index = {}  # Maps the name of the entity to the entity_id

    # -- construction / destruction --
    # temp for lazy testing
    @property
    def entities(self):
        return self.__entities

    def register(self, entity: int, name: str, archetype: object, row: int, component_record: object, is_pair: bool):
        """
        Registers the decoded entity to the entity_index.
        Decodes the entity so only first 32 bit's can be observed

        - Consider adding further validation for custom instances
        """

        if not isinstance(entity, int):
            raise TypeError(f"Invalid entity type of {type(entity)} instead of int.")

        if not isinstance(name, str):
            raise TypeError(f"Invalid entity name type of {type(name)} instead of string.")

        if not isinstance(row, int):
            raise TypeError(f"Invalid entity row type of {type(row)} instead of int.")

        # Pairs do not get decoded
        # registry_entity = entity if is_pair else BitmanipulationHelper().decode_entity(entity)
        registry_entity = entity if is_pair else BitmanipulationHelper().decode_entity(entity)

        self.__entities[registry_entity] = EntityRecord(entity, name, archetype, row, component_record) # Assign record to entity
        self.__name_index[name] = entity # Assign name to entity

    # -- lookups --

    def entity_record(self, entity: int | str, is_pair: bool = False) -> EntityRecord:
        """Returns the entity_record for a given entity."""

        if isinstance(entity, str):
            # If it is a string then lookup by name to get the entity
            entity = self.lookup_name(entity)

        if not isinstance(entity, int):
            # Check it is an int for type validation and preventing unhashable types
            raise TypeError(f"Invalid entity type of {type(entity)} instead of int.")


        # I try with the full_id first
        if not isinstance(entity_record := self.__entities.get(entity), EntityRecord):
            # If it's is_pair and it was not found then return None, avoid matching relationship.
            if is_pair: return None

            decoded_entity = BitmanipulationHelper().decode_entity(entity)
            entity_record = self.__entities.get(decoded_entity)

        return entity_record

    def lookup_name(self, name: str) -> int:
        """Returns entity from name"""
        if not isinstance(name, str):
            raise TypeError(f"Invalid entity name type of {type(name)} instead of string.")

        return self.__name_index.get(name)

    # -- entity_record shortcuts --

    def get_encoded_entity(self, entity: int | str) -> int:
        """Returns the full encoded_entity for an entity"""
        entity_record = self.entity_record(entity)
        return entity_record.entity if isinstance(entity_record, EntityRecord) else None

    def get_name(self, entity: int | str) -> str:
        """Returns the name for an entity"""
        entity_record = self.entity_record(entity)
        return entity_record.name if isinstance(entity_record, EntityRecord) else None

    def get_archetype(self, entity: int | str) -> object:
        """Returns the archetype for an entity"""
        entity_record = self.entity_record(entity)
        return entity_record.archetype if isinstance(entity_record, EntityRecord) else None

    def get_row(self, entity: int | str) -> int:
        """Returns the row for an entity"""
        entity_record = self.entity_record(entity)
        return entity_record.row if isinstance(entity_record, EntityRecord) else None

    # -- Components --

    def get_component_record(self, entity: int | str) -> ComponentRecord:
        """Returns the component_record for a component entity"""
        entity_record = self.entity_record(entity)

        if not isinstance(entity_record, EntityRecord):
            return None

        return entity_record.component_record if isinstance(entity_record, EntityRecord) else None
        
    def get_component_type(self, entity: int | str) -> object:
        """Returns the component_type for a component entity"""
        component_record = self.get_component_record(entity)
        return component_record.type if isinstance(component_record, ComponentRecord) else None

    def get_archetype_map(self, entity: int | str) -> dict:
        """Returns the archetype_map for a component entity"""
        component_record = self.get_component_record(entity)
        return component_record.archetype_map if isinstance(component_record, ComponentRecord) else None

    def get_component_index(self, entity: int | str, archetype: Archetype) -> int:
        """Returns the index of the component within the archetype type"""
        archetype_map = self.get_archetype_map(entity)
        return archetype_map.get(archetype) if isinstance(archetype_map, dict) else None

    def get_component_column(self, entity: int | str, archetype: Archetype) -> int:
        """Returns the column for a component entity in a given archetype"""
        component_index = self.get_component_index(entity, archetype)
        return archetype.column_map[component_index] if isinstance(component_index, int) else None

    def __repr__(self):
        """
        I want to update this in the future to shorten the archetypes to just their type.
        """

        return str(self.__entities)

class TestEntityIndex(unittest.TestCase):
    def setUp(self):
        self.entity_index = EntityIndex()

        # Register a dummy entity
        self.entity_index.register(
            entity=500, 
            name="DummyEntity", 
            archetype=Archetype(tuple(), list(), list(), list()), # Dummy archetype
            row=0,
            component_record=None,
            is_pair=False
        )

        # Register a dummy tag
        self.entity_index.register(
            entity=1000, 
            name="DummyTag", 
            archetype=Archetype(tuple(), list(), list(), list()), # Dummy archetype
            row=0,
            component_record=ComponentRecord(type=None),
            is_pair=False,
        )

        # Register a dummy relationship
        self.entity_index.register(
            entity=100, 
            name="DummyRelationship", 
            archetype=Archetype(tuple(), list(), list(), list()), # Dummy archetype
            row=0,
            component_record=ComponentRecord(type=None),
            is_pair=False,
        )

        # Register dummy pair
        self.entity_index.register(
            entity=BitmanipulationHelper().encode_pair(100, 1000), 
            name="DummyPair", 
            archetype=Archetype(tuple(), list(), list(), list()), # Dummy archetype
            row=0,
            component_record=ComponentRecord(type=None),
            is_pair=True,
        )
    
    def test_register(self):
        # Ensure errors raised correctly
        with self.assertRaises(TypeError):
            # invalid entity
            self.entity_index.register("InvalidEntity", "InvalidEntity", Archetype(tuple(), list(), list(), list()), row=0, component_record=None, is_pair=False),

        with self.assertRaises(TypeError):
            # invalid name
            self.entity_index.register(100, 1000, Archetype(tuple(), list(), list(), list()), row=0, component_record=None, is_pair=False),

        with self.assertRaises(TypeError):
            # invalid row
            self.entity_index.register(100, "InvalidEntity", Archetype(tuple(), list(), list(), list()), row="row", component_record=None, is_pair=False),

        # IsPair is False so 150 should be registered but not the encoded result of 150 & 250
        self.entity_index.register(BitmanipulationHelper().encode_pair(150, 250), "TestEntity", Archetype(tuple(), list(), list(), list()), row=0, component_record=None, is_pair=False),
        self.assertIn(150, self.entity_index.entities) # Should be in as it is not a pair therefore first 32 bits are used as key
        self.assertNotIn(BitmanipulationHelper().encode_pair(150, 250), self.entity_index.entities) # The pair should not be in as is_pair was not flagged on registy

        self.entity_index.register(BitmanipulationHelper().encode_pair(550, 750), "TestPairEntity", Archetype(tuple(), list(), list(), list()), row=0, component_record=None, is_pair=True),
        self.assertNotIn(550, self.entity_index.entities) # Should not be in as only the full pair should be used as the key
        self.assertIn(BitmanipulationHelper().encode_pair(550, 750), self.entity_index.entities) # Should be in as the whole pair should be used as the key

    def test_entity_record(self):
        # Test that using non-existent key safely returns None
        self.assertIsNone(self.entity_index.entity_record(42069))


        # Test base entity_record
        self.assertIsInstance(self.entity_index.entity_record(500), EntityRecord) # DummyEntity
        self.assertIsInstance(self.entity_index.entity_record(1000), EntityRecord) # DummyTag
        self.assertIsInstance(self.entity_index.entity_record(100), EntityRecord) # DummyRelationship
        self.assertIsInstance(self.entity_index.entity_record(BitmanipulationHelper().encode_pair(100, 1000), is_pair=True), EntityRecord) # DummyPair

        # Test with names
        self.assertIsInstance(self.entity_index.entity_record("DummyEntity"), EntityRecord) # DummyEntity
        self.assertIsInstance(self.entity_index.entity_record("DummyTag"), EntityRecord) # DummyTag
        self.assertIsInstance(self.entity_index.entity_record("DummyRelationship"), EntityRecord) # DummyRelationship
        self.assertIsInstance(self.entity_index.entity_record("DummyPair", is_pair=True), EntityRecord) # DummyPair

        # Test exception
        with self.assertRaises(TypeError):
            self.entity_index.entity_record("NonexistentEntity")

    def test_lookup_name(self):
        self.assertIsInstance(self.entity_index.lookup_name("DummyEntity"), int)
        self.assertIsNone(self.entity_index.lookup_name("InvalidEntity"))

    def test_shortcuts(self):
        """Tests a range of shortcuts ensuring they're all safe"""
        
        entity_record = self.entity_index.entity_record("DummyTag") # DummyTag to test ComponentRecord
        self.assertIsInstance(self.entity_index.get_encoded_entity("DummyTag"), int)
        self.assertIsInstance(self.entity_index.get_name("DummyTag"), str)
        self.assertIsInstance(self.entity_index.get_archetype("DummyTag"), Archetype)
        self.assertIsInstance(self.entity_index.get_row("DummyTag"), int)
        self.assertIsInstance(self.entity_index.get_component_record("DummyTag"), ComponentRecord)
        self.assertIsNone(self.entity_index.get_component_type("DummyTag"))
        self.assertIsInstance(self.entity_index.get_archetype_map("DummyTag"), dict)

        entity_record = self.entity_index.entity_record("DummyEntity") # DummyEntity to test ComponentRecord when invalid
        self.assertIsNone(self.entity_index.get_component_record("DummyEntity"))
        self.assertIsNone(self.entity_index.get_component_type("DummyEntity"))
        self.assertIsNone(self.entity_index.get_archetype_map("DummyEntity"))

if __name__ == '__main__':
    unittest.main(verbosity=2)