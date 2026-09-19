import unittest

class BitmanipulationHelper:
    """
    GROUP A:
        Complex user-defined use of object-orientated programming (OOP) model (Singleton)
        Complex user defined algorithms (optimisation?)

    Singleton datastructure for providing bitmanipulation functionality.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BitmanipulationHelper, cls).__new__(cls)
            cls._instance.__init_configs()
        return cls._instance

    def __init_configs(self):

        # Masks to cover select area's of integer
        self.__entity_mask = 0xFFFFFFFF # Base 32 bits 
        self.__generation_mask = 0xFFFF # 16 bits indicating a version

        # Shifts -> shift to the right to get to the encoded value
        self.__generation_shift = 32 
        self.__target_shift = 32

    # -- Base entity --

    def decode_entity(self, encoded_entity: int):
        """Returns entity masked to first 32 bits."""
        return encoded_entity & self.__entity_mask

    # -- Generation --

    def decode_generation(self, encoded_id):
        """Returns entity masked to 16 bits with a shift of 32"""
        return (encoded_id >> self.__generation_shift) & self.__generation_mask

    def clear_generation(self, encoded_entity: int):
        """Returns the encoded_entity without the generation"""
        return encoded_entity & ~(self.__generation_mask << self.__generation_shift)

    def set_generation(self, encoded_entity: int, generation: int):
        """Encodes a genereation value 16 bits into the encoded_entity"""
        return encoded_entity | generation << self.__generation_shift

    def increment_generation(self, encoded_entity):
        """Safely increments an encoded_entities generation"""
        generation = self.decode_generation(encoded_entity)
        incremented_generation = (generation + 1) & self.__generation_mask

        cleared_id = self.clear_generation(encoded_entity)
        encoded_id = self.set_generation(cleared_id, incremented_generation)
        return encoded_id

    def compare_generation(self, first_entity, second_entity) -> bool:
        """Return True if both entities shared the same generation"""
        return self.decode_generation(first_entity) == self.decode_generation(second_entity)

    # -- relationships --

    def encode_pair(self, relationship: int, target: int) -> int:
        """Returns a entity with the two base entities in the first and second 32 bits respectively."""

        decoded_relationship, decoded_target = self.decode_entity(relationship), self.decode_entity(target)

        return (decoded_target << self.__target_shift) | decoded_relationship

    def decode_pair(self, pair: int) -> int:
        """Returns a tuple of relationship -> target"""
        return self.decode_entity(pair), (pair >> self.__target_shift) & self.__entity_mask

class TestBitmanipulationHelper(unittest.TestCase):
    def test_singleton(self):
        # Check they're the same instance
        self.assertEqual(id(BitmanipulationHelper()), id(BitmanipulationHelper()))

    def test_decode_entity(self):
        # Returns integer with only 32 bits
        # 32 bit integer is less than 2^32 / 4_294_967_295

        test_integer = 4_294_967_296 # 1 above...
        result = BitmanipulationHelper().decode_entity(test_integer)

        # Value would have nothing within the first 32 bits
        self.assertIsNotNone(result)
        self.assertNotEqual(result, test_integer)
        self.assertEqual(result, 0)

        test_integer = 5_294_967_296 
        result = BitmanipulationHelper().decode_entity(test_integer)

        # Incremented by 1 billion so should be 1 billion
        self.assertEqual(result, 1_000_000_000)

    def test_generation(self):

        # Test setting the generation and decoding for same values
        test_integer = 100
        result = BitmanipulationHelper().set_generation(test_integer, 5)
        self.assertEqual(BitmanipulationHelper().decode_generation(result), 5)

        # Test the entity is still the same

        # Through decoding entity
        self.assertEqual(test_integer, BitmanipulationHelper().decode_entity(result))
        # Through clearing generation
        self.assertEqual(test_integer, BitmanipulationHelper().clear_generation(result))

        # compare generations
        entity_one = BitmanipulationHelper().set_generation(0, 100)
        entity_two = BitmanipulationHelper().set_generation(1, 100)
        entity_three = BitmanipulationHelper().set_generation(2, 101)

        self.assertTrue(BitmanipulationHelper().compare_generation(entity_one, entity_two))
        self.assertFalse(BitmanipulationHelper().compare_generation(entity_one, entity_three))

        # Check the incrementation
        entity = 1000
        for count in range(1, 5):
            entity = BitmanipulationHelper().increment_generation(entity)
            self.assertEqual(BitmanipulationHelper().decode_generation(entity), count)

        # The generation should not exceed 16 bits / 2^16 before resetting
        # that is 65,536 at which it should essentially return the modulus
        entity = BitmanipulationHelper().set_generation(1000, 65_536) # set to maxium
        entity = BitmanipulationHelper().increment_generation(entity) # increment to test reset
        self.assertEqual(BitmanipulationHelper().decode_generation(entity), 1)

    def test_pair(self):
        # pairs combine the first 32 bits of the relationship
        # and the last 32 bits of the target

        relationship = 10
        target = 100
        pair = BitmanipulationHelper().encode_pair(relationship, target)

        # Test that the decoding gives expected values
        self.assertEqual(BitmanipulationHelper().decode_pair(pair), (relationship, target))

        # Check with a generation set
        generation_relationship = BitmanipulationHelper().set_generation(relationship, 100)
        generation_target = BitmanipulationHelper().set_generation(target, 1000)
        generation_pair = BitmanipulationHelper().encode_pair(generation_relationship, generation_target)

        # Test that the decoding gives expected values
        self.assertEqual(BitmanipulationHelper().decode_pair(generation_pair), (relationship, target))

if __name__ == '__main__':
    unittest.main(verbosity=2)