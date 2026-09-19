from dataclasses import dataclass, field


@dataclass
class Archetype:
    """
    GROUP A:
        Hashing
        multi-dimesonal arrays (columns)


    An archetype datastructure works similary to a table in a database. The archetype is composed of a unique unordered combination of components.
    Each non-tag component within an archetype has a column, this stores instances of the components dataclass. The dataclass is mapped to an entity
    within the archetype by the row in the column it is currently stored within. 
    """

    type: tuple[int]    # A tuple of integer sorted integer values unique to the archetype
    entities: list      # A list of entities, index in list is mapped the entities index in components column lists.
    column_map: list
    columns: list[list]

    hashed_id: int = field(init=False, default=-1) # Deterministic stored hash from type

    def __post_init__(self):
        self.hashed_id = hash(self.type)

    def __hash__(self):
        return self.hashed_id

    def __len__(self):
        return len(self.entities)

    def __eq__(self, other):
        return self.type == other
