from dataclasses import dataclass, field

@dataclass
class EntityRecord:
    """A record containing metadata about an entity, used as value in the EntityIndex"""
    entity: int         # Full entity_id for livelyness checking etc.
    name: str           # A string identifier for the entities name
    archetype: object   # The archetype the entity currently exists in
    row: int            # The row the entity currently exists in
    component_record: object = field(default=None) # ComponentRecord for component entities

    def __repr__(self):
        """Returns the entity """
        return f"EntityRecord(entity={self.entity}, name={self.name}, archetype={self.archetype.type if isinstance(self.archetype, object) else None}, row={self.row}, component_record={self.component_record})"