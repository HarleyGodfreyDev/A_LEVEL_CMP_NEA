
class Entity(int):
    """
    GROUP A:
        Complex user-defined use of object-orientated programming (OOP) model:
            inheritance, interface, builder
    

    Subclasses integer and interfaces the world api,
    is not used within the api but outside.
    """

    def __new__(cls, entity: int, world):
        instance = super().__new__(cls, entity)
        instance.__world = world
        return instance

    def add(self, *components):
        """add components from argument to the entity. """
        self.__world.ecs_add(self, *components)
        return self

    def remove(self, *components):
        """remove components from argument from the entity. """
        self.__world.ecs_remove(self, *components)
        return self

    def set(self, *components):
        """set component and component data from arguments in the entity"""
        self.__world.ecs_set(self, *components)
        return self
        
    def get(self, component):
        """get a component belonging to the entity"""
        return self.__world.get_component(self, component)
    
    # QUERIES
    def has(self, *components):
        """Test if entity has component / pair"""
        return all(self.__world.entity_has_component(self, component) for component in components)

    def parent(self):
        """Returns entities parent if it has a parent"""
        return self.__world.get_parent(self)

    def children(self):
        """Returns all children from a parent"""
        return self.__world.get_children(self)

    def wildcard_pair(self):
        """Returns wildcard pair of the entity"""
        return self.__world.get_wildcard_pair(self)

    # Each / Targets are iterable, might need to investigate.

    # SHORT CUTS

    def is_a(self, target: int):
        """adds is_a pair with target to the entity"""
        is_a_pair = self.__world.pair(self.__world.EcsIsA, target)        
        self.__world.ecs_add(self, is_a_pair)
        return self

    def child_of(self, parent: int):
        """adds child_of pair with parent as target to the entity"""

        child_of_pair = self.__world.pair(self.__world.EcsChildOf, parent)        
        self.__world.ecs_add(self, child_of_pair)
        return self
