from loguru import logger
from ecs.datastructures.helpers.bitmanipulation import BitmanipulationHelper

class QueryBuilder:
    """
    GROUP A:
        Complex user-defined use of object-orientated programming (OOP) mode: builder, interface
        Complex user-defined algorithms (predication, backtracking and execution. )

    Queries provide the capability to match a list of conditions.
    This is the core behind systems that operate based on queries.

    the user can select the base archetypes, if they do not select a base
    then it will default to all archetypes.
    """

    def __init__(self, world, archetype_index, entity_index):

        self.__world = world
        self.__archetype_index = archetype_index
        self.__entity_index = entity_index

        # Base archetypes from select_
        # utilised set to prevent duplication and access other operations.

        self.__archetypes = set() 

        self.__predicates = [] # a list of functions that should be called on build

    def select_(self, *components):
        """
        Selects the base archetypes that will be used in the query.
        defaults to all archetypes.

        I need to make it do it as if a lambda before the archetypes so when it's 
        rebuilt is accounts for the new archetype and starts again from. 
        """

        if len(components) == 0:
            self.__archetypes.update(self.__archetype_index.all_archetypes())
            return self

        for component in components:
            if not isinstance(component_archetypes := self.__entity_index.get_archetype_map(component), dict):
                continue
            
            for archetype in component_archetypes.keys():
                self.__archetypes.add(archetype)
        return self

    # ******* WITH ********

    # with_ and -> returns true if all components are in the archetype
    def with_(self, *components):
        self.__predicates.append(lambda archetype: all(self.__world.entity_has_component(archetype, component) for component in components))
        return self
    
    # with_ or -> returns true if any components are in the archetype
    def with_any_(self, *components):
        self.__predicates.append(lambda archetype: any(self.__world.entity_has_component(archetype, component) for component in components))
        return self

    # with_ xor -> returns true if only one of these conmponents are in the archetype
    def with_ethier_(self, *components):
        self.__predicates.append(lambda archetype: self.__exclusive_or_predicate(archetype, components))
        return self

    # with_ethier predicate, custom implementation to exit early and avoid unneccesary checks.
    def __exclusive_or_predicate(self, archetype, components):
        flag = False # boolean flag indicating if a component that is valid has already been found. I couldn't think of a name
        for component in components:
            if self.__world.entity_has_component(archetype, component):
                if flag: 
                    # multiple true conditions, return False
                    return False
                else: flag = True
        return flag

    # with_ nand -> returns false if all the components are in the archetype
    def without_(self, *components):
        self.__predicates.append(lambda archetype: not all(self.__world.entity_has_component(archetype, component) for component in components))
        return self

    # with_ nor -> returns false if any of the components are in the archetype
    def without_any_(self, *components):
        self.__predicates.append(lambda archetype: not any(self.__world.entity_has_component(archetype, component) for component in components))
        return self

    # checks if the archetype contains is_a relationships
    def is_a_(self, target: int):
        pair = BitmanipulationHelper().encode_pair(self.__world.EcsIsA, target)
        self.__predicates.append(lambda archetype: self.__world.entity_has_component(archetype, pair))
        return self

    # checks if the archetype contains a child_of relationship
    def child_of_(self, parent: int):
        pair = BitmanipulationHelper().encode_pair(self.__world.EcsChildOf, parent)
        self.__predicates.append(lambda archetype: self.__world.entity_has_component(archetype, pair))
        return self

    def execute(self):
        """
        Returns the result of the query.
        
        Optimises performance by using backtracking and predicates,.
        if any of the predicates return False it will backtrack immediately.
        """

        matching = []
        base_archetypes = self.__archetypes
        predicates = self.__predicates

        for archetype in base_archetypes:
            valid = True
            for predicate in predicates:
                if not predicate(archetype):
                    logger.debug(f"archetype failed predicate.")
                    valid = False
                    break

            if valid:
                logger.debug(f"archetype succeded predicate.")
                matching.append(archetype)
        
        return matching
