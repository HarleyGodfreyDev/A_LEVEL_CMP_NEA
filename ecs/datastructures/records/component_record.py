from dataclasses import dataclass, field

@dataclass
class ComponentRecord:
    """A record containing metadata about an component, used as value in EntityRecord/EntityIndex"""
    type: object # The dataclass of the component
    archetype_map: dict = field(default_factory=dict) # Contains all archetypes with component in the type, maps archetypes to index in archetype_type

    def __repr__(self):
        type_repr = type.__name__
        archetype_map_repr = f"ArchetypeMap({len(self.archetype_map)} archetypes)"
        return f"ComponentRecord(type={type_repr}, archetype_map={archetype_map_repr})"
