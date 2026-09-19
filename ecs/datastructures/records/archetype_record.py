from dataclasses import dataclass, field

@dataclass
class ArchetypeRecord:
    """A record containing metadata for an archetype, used as a value for the ArchetypeIndex. """
    archetype: object # The archetype instance itself
    archetype_cache: dict = field(default_factory=dict) # the archetype cache