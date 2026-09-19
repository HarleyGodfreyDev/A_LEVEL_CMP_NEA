import unittest
import time
from loguru import logger
from dataclasses import dataclass, field, fields, make_dataclass

from ecs.datastructures.indexs.entity_index import EntityIndex
from ecs.datastructures.indexs.archetype_index import ArchetypeIndex

from ecs.datastructures.records.entity_record import EntityRecord
from ecs.datastructures.records.archetype_record import ArchetypeRecord
from ecs.datastructures.records.component_record import ComponentRecord

from ecs.datastructures.helpers.bitmanipulation import BitmanipulationHelper

from ecs.datastructures.custom.graveyard import Graveyard
from ecs.datastructures.custom.archetype import Archetype

from ecs.datastructures.builders.entity import Entity
from ecs.datastructures.builders.query import QueryBuilder

from ecs.datastructures.base.stack import Stack
from ecs.datastructures.base.queue import Queue

logger.remove()

# Setup logging to my preferences
logger.add(
    sink="logs/entity_component_system.log",
    mode="w",
    level="DEBUG",
    format="{elapsed} | {level} | {function} | {line} | {message}",
    colorize=True,
    rotation="1 MB",  # Rotate log file after it reaches 1 MB
    retention="10 days",  # Retain logs for 10 days
    compression="zip",  # Compress rotated logs
)

class World:
    """
    The primary class / API for the entity component system. I have added where I believe group a methods have been used throughout.
    However, a significant amount of the critera specifies object orientated when I am utilsing the entity component system.
    """

    def __init__(self):
        logger.info(f"""

        ****************************
        * Initialsing EcsWorld API *
        ****************************

        """)

        # Initialise entity_index
        self.__entity_index = EntityIndex()
        self.__archetype_index = ArchetypeIndex()
        logger.info(f"\n\n**** entity & archetype indexs initialised ****\n")

        self.__graveyard = Graveyard() # Returns revived / autoincremented entity_ids
        logger.info(f"\n\n**** graveyard initialised ****\n")

        # -- built-in --
        logger.info(f"\n\n**** built-in ecs type identifers initialising ****\n")

        self.EcsComponent = self.__bootstrap_ecs_component() # Components for components, holds component_record metadata.
        self.EcsTag = self.__bootstrap_ecs_tag() # Tag identifer for tags.
        self.EcsEntity = self.__bootstrap_ecs_entity() # Unique identifer for base entities.

        self.EcsRelationship = self.tag(name="EcsRelationship") # Identifer for relationships
        self.EcsPair = self.tag(name="EcsPair") # Identifer for pairs

        logger.info(f"\n\n**** built-in ecs type identifers initialised ****\n")

        # -- built-in traits --
        logger.info(f"\n\n**** built-in ecs traits initialising ****\n")

        self.EcsPairIsTag = self.tag(name="EcsPairIsTag") # Enforces that the pair will never contain data (even if the target is a component)
        self.EcsFinal = self.tag(name="EcsFinal") # Enforces that no more IsA pairs can be added to the entity

        # Instantiation occurs when an IsAs is added to the entity.
        # works with EcsOverride, EcsInherit, EcsDontInherit
        self.EcsOnInstantiate = self.relationship(name="EcsOnInstantiate") 
        self.EcsDontInherit = self.tag(name="EcsDontInherit") # Does not copy, prevent get / has / set operations from over-riding 

        self.EcsExclusive = self.tag(name="EcsExclusive") # Only one of said relationship can exist within the archetype at a time.

        self.EcsSymmetric = self.tag(name="EcsSymmetric") # The relationship is also added / removed from the target relationship but with the pairs target being the orignal entity.

        self.EcsCanToggle = self.component(make_dataclass(cls_name="EcsCanToggle", fields=[('toggle', bool, True)])) # Trait added to component to toggle if it is or is not found in queries.

        logger.info(f"\n\n**** built-in ecs traits initialised ****\n")

        # -- built-in relationships ---
        logger.info(f"\n\n**** built-in ecs relationships initialising ****\n")

        # A unique tag that is used in queries to select all
        # for example (Likes, Apple) is a pair in which you could query
        # (Likes, *), (*, Apple), (*, *)
        # Where there is a * it implies all, therefore (Likes, *) will have all archetypes with a likes pair
        self.EcsWildcard = self.relationship(name="EcsWildcard") 

        # A built-in relationship used for inheritance within the entity component system
        # inheritance works through an IsA pair such as IsADragon means the entity inherits from the Dragon entity.
        # to save memory instead of copying the components from IsADragon instead the entity will utilise the Dragon entities component_instance.
        # over-riding can occur within the entities set method, if an inherited component is set to different attributes it will have the component
        # added to itself. It will use the component_instance of the parent as the default and then apply any set changes.
        self.EcsIsA = self.relationship(name="EcsIsA") # Inheritance

        self.EcsChildOf = self.relationship(name="EcsChildOf") # Hierarichal relationship but no inheritance.
        self.ecs_add(self.EcsChildOf, self.EcsExclusive)

        # Added to a component to indicate that it must always come together with another component.
        # When With is added to a relationship the additonal id added will be a relationship pair aswell
        # with the same target as the first relationship.
        self.EcsWith = self.relationship(name="EcsWith")


        logger.info(f"\n\n**** built-in ecs relationships initialised ****\n")

        logger.success(f"""

        ****************************
        * Initialised EcsWorld API *
        ****************************

        """)

    def __bootstrap_ecs_component(self) -> int:
        """
        EcsComponent manual registration and setup on initialistion. 

        Bootstraps EcsComponent without requiring utilisation of EcsComponent, preventing circular issues resutling from entities being components.
        Utilises dependency injection where possible to minimise manual injection, although required.
        """

        logger.info(f"\n\n**** bootstrapping EcsComponent ****\n")

        component = self.__graveyard(revive=False)
        component_record = ComponentRecord(type=ComponentRecord)


        logger.info(f"Archetype type and entity will show as None, ignore for now.")
        archetype_record = self.archetype(
            component, 
            entities=[component],
            column_map=[0],
            columns=[
                [component_record,]
            ]
        )

        component_record.archetype_map[archetype_record.archetype] = 0  # Assign column in archetype_map

        self.__entity_index.register(
            entity=component,
            name="EcsComponent",
            archetype=archetype_record.archetype,
            row=0,
            component_record=component_record,
            is_pair=True,
        )

        logger.info(f"\n\n**** bootstrapped EcsComponent ****\n")

        return Entity(component, self)

    def __bootstrap_ecs_tag(self) -> int:
        """
        EcsTag manual registration and setup on initialistion. 

        Bootstraps EcsTag without requiring utilisation of EcsTag, preventing circular issues resutling from entities being components.
        Utilises dependency injection where possible to minimise manual injection, although required.

        Required due to Tag being used in checking for components for column_mapping.
        """

        logger.info(f"\n\n**** bootstrapping EcsTag ****\n")

        tag = self.__graveyard(revive=False)
        component_record = ComponentRecord(type=None)

        archetype_record = self.archetype(
            self.EcsComponent, tag, # Tags are part of EcsComponent
            entities=[tag],
            column_map=[0, -1],
            columns=[
                [component_record],
            ]
        )

        self.__entity_index.get_archetype_map(self.EcsComponent)[archetype_record.archetype] = 0
        component_record.archetype_map[archetype_record.archetype] = 1

        self.__entity_index.register(
            entity=tag,
            name="EcsTag",
            archetype=archetype_record.archetype,
            row=0,
            component_record=component_record,
            is_pair=True,
        )

        logger.info(f"\n\n**** bootstrapped EcsTag ****\n")

        return Entity(tag, self)

    def __bootstrap_ecs_entity(self) -> int:
        """Constructs the base entity archetype to ensure base entities can manually inject into archetype."""

        logger.info(f"bootstrapping EcsEntity.")

        entity = self.tag(name="EcsEntity")

        archetype_record = self.archetype(
            entity,
            entities=[],
            column_map=[-1],
            columns=[]
        )

        self.__entity_index.get_archetype_map(entity)[archetype_record.archetype] = 0


        return Entity(entity, self)

    # --- temp because I'm being lazy --
    @property
    def entity_index(self):
        return self.__entity_index

    @property
    def archetype_index(self):
        return self.__archetype_index

    # -- CONSTRUCTION --
    # Manual injection used in most construction to handle edge-case and improve construction speed.

    def entity(self, name: str, entity: int = None):
        """
        Returns an entity registered to the world.
        
        An entity is an integer that can be used to represent anything in the game world.
        From dragons to cities to universes. It is just a representation of "something"
        """

        entity = entity if isinstance(entity, int) else self.__graveyard(revive=True)
        name = name if isinstance(name, str) else "UnnamedEntity"

        archetype: Archetype = self.__archetype_index.archetype(self.EcsEntity)

        row = len(archetype)
        archetype.entities.append(entity)

        self.__entity_index.register(entity, name, archetype, row, None, False)

        logger.info(f"registered entity to world: (id={entity}, name={name})\n")

        # return entity
        return Entity(entity, self)

    def component(self, type: object, name: str = None, component: int = None, is_pair: bool = False) -> int:
        """
        Returns a component registered to the world.

        A component is a datastructure that is purely data-orientated, it has no behaviour.
        This method manually injects the component into the EcsComponent archetype, this is for
        efficency but to avoid edge-case logic from no-source archetype entities when moving
        entities across archetypes.
        """

        component = component if isinstance(component, int) else self.__graveyard(revive=True)
        name = name if isinstance(name, str) else type.__name__

        # Component must be added to EcsComponent
        archetype: Archetype = self.__entity_index.get_archetype(self.EcsComponent)
        component_record = ComponentRecord(type)

        self.__add_component_to(archetype, component, name, component_record, is_pair)

        logger.info(f"registered component to world: (id={component}, name={name})\n")

        # return component
        return Entity(component, self)

    def tag(self, name: str, tag: int = None, is_pair: bool = False):
        """
        Returns a tag registered to the world.

        A tag is a component that has no data, it is purely used to indicate something.
        Manual injection has been used once again for higher performance at the cost ofsmall duplication.
        """

        tag = tag if isinstance(tag, int) else self.__graveyard(revive=True)
        name = name if isinstance(name, str) else "UnnamedTag"

        # Tag must be added to EcsComponent, EcsTag
        archetype: Archetype = self.__entity_index.get_archetype(self.EcsTag)
        component_record = ComponentRecord(None)

        self.__add_component_to(archetype, tag, name, component_record, is_pair)

        logger.info(f"registered tag to world: (id={tag}, name={name})\n")

        # return tag
        return Entity(tag, self)

    def relationship(self, type: object = None, name: str = None, relationship: int = None):
        """
        Returns a relationship registered to the world.

        Relationships are intended to be used as the first part of a pair.
        Relationships are very rarely utilised stand-alone.
        Relationships can ethier be tags or components.
        Relationships that are components will always override the type of a pair.
        """

        if type is None:
            relationship = self.tag(name, relationship)
        else:
            relationship = self.component(type, component=relationship)

        self.ecs_add(relationship, self.EcsRelationship)

        logger.info(f"registered relationship to world: (id={relationship}, name={name if not name is None else type})\n")

        return Entity(relationship, self)

    def pair(self, relationship: int, target: int):
        """
        Returns a pair entity registered to the world.

        A pair is a combination of a relationship and a target, this can be used for querying or built-in logic.
        The pairs type is determined through the following algorithm:
            - relationship has "EcsPairIsTag" trait which forces the pair to always be a tag
            - relationships type if the relationship has a type
            - targets type if the relationship does not have a type and the target does
            - None -> pair is a tag
        """


        if not self.is_relationship(relationship):
            raise TypeError(f"Invalid relationship type, relationship must have EcsRelationship component.")

        pair_entity = BitmanipulationHelper().encode_pair(relationship, target) # Combine the integers

        if isinstance(pair_record := self.__entity_index.entity_record(pair_entity, is_pair=True), EntityRecord):
            logger.debug(f"returning existing pair: (pair={pair_entity}, name={self.__entity_index.get_name(pair_entity)})\n")
            return pair_entity
        
        relationship_record = self.__entity_index.entity_record(relationship)
        target_record = self.__entity_index.entity_record(target)

        pair_name = f"{relationship_record.name}{target_record.name}" # Combine the name

        if self.entity_has_component(relationship, self.EcsPairIsTag, check_inheritance=False):
            pair_type = None

        elif not self.is_tag(relationship):
            # Relationship will be the type
            pair_type = relationship_record.component_record.type
        
        elif not self.is_tag(target) and self.is_component(target):
            # Target will be the type
            pair_type = target_record.component_record.type

        else:
            # Type will be a tag
            pair_type = None

        pair = self.tag(pair_name, pair_entity, is_pair=True) if pair_type is None else self.component(pair_type, pair_name, pair_entity, is_pair=True)

        # Check if wildcard for loggig
        is_wildcard = relationship == self.EcsWildcard or target == self.EcsWildcard
        self.ecs_add(pair, self.EcsPair, is_wildcard=is_wildcard)

        logger.info(f"registered pair to the world (id={pair_entity}, name={pair_name}, type={pair_type})\n")
        return Entity(pair, self)

    def archetype(self, *components, entities: list[int] = None, column_map: list[int] = None, columns: list[list] = None):
        """
        Returns an existing archetype from components or returns a constructed archetype from components.

        Keyword arguments for dependency injection.
        
        """

        entities = [] if entities is None else entities
        column_map = [] if column_map is None else column_map
        columns = [] if columns is None else columns

        # Sort components for unordered, if only one component cast to tuple
        sorted_components = tuple(sorted(components)) if len(components) > 1 else tuple(components)

        if (archetype_record := self.__archetype_index.archetype_record(sorted_components)) is None:
            archetype = Archetype(
                type=sorted_components,
                entities=entities,
                column_map=column_map,
                columns=columns
            )

            if len(archetype.column_map) != len(archetype.type):
                # if this is False ethier the dependency injection was messed up or there was none
                # so update the columns
                archetype.column_map, archetype.columns = self.__archetype_columns(archetype, sorted_components)

            archetype_record = self.__archetype_index.register(archetype)
            logger.info(f"registered archetype to the world: (type={tuple(self.__entity_index.get_name(type_c) for type_c in sorted_components)})\n")
            logger.debug(f"""
                - ENTITIES:  {tuple(self.__entity_index.get_name(entity) for entity in archetype.entities)}
                - COLUMN_MAP: {archetype.column_map}
                - COLUMNS:    {archetype.columns}

            """)
        else:
            logger.info(f"retrieved archetype from world: (type={tuple(self.__entity_index.get_name(component) for component in sorted_components)})")

        return archetype_record

    def __archetype_columns(self, archetype: Archetype, sorted_components: tuple[int]):
        """
        GROUP A:
            Complex user-defined algorithms (eg optimisation, minimisation, scheduling, pattern matching) or equivalent difficulty
            Multi-dimesonal arrays (columns)

        Returns the column_map and columns for the archetype based on sorted_components.
        column_map lines up with the archetypes_type to map index to column index.
        """

        column_map = []
        columns = []

        for index, component in enumerate(sorted_components):
            column_index = -1

            if not self.entity_has_component(component, self.EcsTag, check_inheritance=False):
                column_index = len(columns)
                columns.append([])

            column_map.append(column_index)
            self.__register_archetype_to_component(archetype, component, index)

        return column_map, columns

    def __register_archetype_to_component(self, archetype: Archetype, component: int, index: int):
        """
        GROUP A:
            Complex user-defined algorithms (eg optimisation, minimisation, scheduling, pattern matching) or equivalent difficulty 
            Multi-dimesonal arrays
            Dynamic generation of objects?

        Registers the archetype to the components archetype_map, custom logic for relationships.

        For pair components it will register all wildcard variants to the world.
        Wildcard meaning * -> select all
        so (IsA, *) would select all IsA relationships.

        Wildcard variants aren't accutally added to any entities and therefore the possibility of 
        having a unique archetype_map exists. In this case typically only one component is within an archetype
        therefore only one index is required. 

        However, for wildcards such suuch as (IsA, *) or (*, Dragon) there can be multiple in a single archetype.
        Therefore, this should be reflected within the archetype_map for these respective wildcards. Therefore,
        I will have a list of index's instead of a single index. Although a dictonary was possible it would add
        much more overhead on a larger scale.
        """
        
        archetype_map = self.__entity_index.get_archetype_map(component)
        archetype_map[archetype] = index

        logger.info(f"registered archetype to component: Archetype(type={tuple(self.__entity_index.get_name(type_c) for type_c in archetype.type)}) (component={component}, component_name={self.__entity_index.get_name(component)}) ")

        # Return here if the component is a pair
        if not self.is_pair(component):
            return

        relationship, target = BitmanipulationHelper().decode_pair(component)

        # All combinations of wildcard pairs
        wildcard_pairs = (
            (relationship, self.EcsWildcard),       # (IsA, *)
            (self.EcsWildcard, target),             # (*, Dragon)
            (self.EcsWildcard, self.EcsWildcard)    # (*, *)
        )

        # Create the wildcard relationships and add the archetype to the wildcard
        for wildcard_pair in wildcard_pairs:
            wildcard_relationship, wildcard_target = wildcard_pair[0], wildcard_pair[1]
            wildcard_entity = world.pair(wildcard_relationship, wildcard_target)

            # Add the archetype to the wildcard_entity
            archetype_map = self.__entity_index.get_archetype_map(wildcard_entity)

            # Check if it exists with a list
            if isinstance(indexs := archetype_map.get(archetype), list):
                indexs.append(index) # Adds the index to the list if the list exists
            else:
                archetype_map[archetype] = [index,] # If no list exists create a new list

        logger.info(f"registered archetype to wildcard variants for component.")   # The information is already above so no need to repeat.

    # -- ARCHETYPE --

    def __move_entity(self, entity: int, components: tuple[int], is_add: bool):
        """
        Moves an entity and it's data from their source archetype to a destination archetype determined through added / removed components.
        """

        record: EntityRecord = self.__entity_index.entity_record(entity)
        source: Archetype = record.archetype

        logger.debug(f"moving entity archetype: Entity(id={entity}, name={record.name}) with Components{tuple(self.__entity_index.get_name(component) for component in components)} on {'is_add' if is_add else 'is_remove'}\n")

        # During the traversal some traits will lead to operations that need to be completed
        # after the entity has been successfully moved into it's new archetype
        # opertions are added here to be executed later.
        # passes in a mutable reference
        operation_backlog = []
        destination: Archetype = self.traverse_archetype_cache(source, operation_backlog, components, entity, is_add)

        # O(n) operation on remove operations for each remove component.
        # Possibly more performant method to achieve this but the performance impact
        # would barely be noticeable.
        exceptions = set() if is_add else set(components)
        entity_data = self.__pop_entity_from(source, record.row, exceptions)

        entity_row = len(destination)
        destination.entities.append(entity)

        for index, column_index in enumerate(destination.column_map):
            # Skip tags
            if column_index == -1: continue

            # Use data from stack where possible
            if (component_instance := entity_data.pop()) is None:
                # If it's empty we need to get the type of the current component and construct that
                component = destination.type[index]
                component_type = self.__entity_index.get_component_type(component)
                component_instance = component_type()
            
            column = destination.columns[column_index]
            column.append(component_instance)

        # Update entity_record
        record.archetype = destination
        record.row = entity_row

        # Now that entity has been succesfully moved we can perform the operation_backlog
        for operation in operation_backlog:
            operation()

        logger.info(f"moved entity from source to destination archetype: Entity(id={entity}, name={record.name}) from Source(type={tuple(self.__entity_index.get_name(type_c) for type_c in source.type)}) to Destination(type={tuple(self.__entity_index.get_name(type_c) for type_c in destination.type)})")

    def __pop_entity_from(self, archetype: Archetype, entity_row: int, exceptions: set[int]):
        """
        GROUP A:
            multi-dimesonal arrays
            stack operations
            list operations
            Complex user-defined algorithms (eg optimisation, minimisation, scheduling, pattern matching) or equivalent difficulty?


        Removes an entity from the given archetype and returns it's data as a stack.

        Exceptions -> Do not add these to the stack -> Set for fast membership testing
        """

        stack = Stack()

        if entity_row == len(archetype.entities) - 1:

            # Entity is the last entity or only entity in the archetype
            archetype.entities.pop(entity_row)
            for index, column_index in enumerate(archetype.column_map):
                if column_index == -1: continue

                column = archetype.columns[column_index]
                column_instance = column.pop(entity_row)

                if not archetype.type[index] in exceptions:
                    stack.push(column_instance)

        else:
            # Entity is somewhere in archetype.. in-order to keep row-order we must replace it with the last entity in the archetype.
            archetype.entities[entity_row] = archetype.entities.pop(-1)
            for index, column_index in enumerate(archetype.column_map):
                if column_index == -1: continue

                column = archetype.columns[column_index]

                column_instance = column[entity_row] # store the column instance of entity being popped
                column[entity_row] = column.pop(-1) # replace the column instance with last entity

                if not archetype.type[index] in exceptions:
                    stack.push(column_instance)
                
            # Update the entity_record for the entity that replaced the entity being popped
            self.__entity_index.entity_record(archetype.entities[entity_row]).row = entity_row

        logger.info(f"popped entity from archetype: EntityData({stack})") # other data should already exist from wherever this was called.
        return stack

    def __add_component_to(self, archetype: Archetype, entity: int, name: str, component_record: ComponentRecord, is_pair: bool):
        """
        Adds a component without a source archetype directly to their respective archetype.
        """

        row = len(archetype)
        column = self.__entity_index.get_component_column(self.EcsComponent, archetype)

        archetype.entities.append(entity)
        archetype.columns[column].append(component_record)

        self.__entity_index.register(entity, name, archetype, row, component_record, is_pair)

    # -- ENTITY OPERATIONS --

    def ecs_add(self, entity, *components, is_wildcard=False):
        """Adds the components listed to the entity"""
        if not is_wildcard: logger.info(f"\n\n  ---- ADDING COMPONENTS TO ENTITY ----\n")
        else: logger.info(f"\n\n        ____ADDING WILDCARD____\n\n")

        logger.debug(f" - Entity(id={entity}, name={self.__entity_index.get_name(entity)}) + Components{tuple(self.__entity_index.get_name(component) for component in components)}\n")

        self.__move_entity(entity, components, True)
        if not is_wildcard: logger.info(f"\n\n  ---- ADDED COMPONENTS TO ENTITY ----\n")
        else: logger.info(f"\n\n        ____ADDED WILDCARD___\n")

    def ecs_remove(self, entity, *components):
        """Removes the components listed from the entity"""
        logger.info(f"\n\n---- REMOVING COMPONENTS FROM ENTITY ----\n")
        logger.debug(f" - Entity(id={entity}, name={self.__entity_index.get_name(entity)}) + Components{tuple(self.__entity_index.get_name(component) for component in components)}\n")
        self.__move_entity(entity, components, False)
        logger.info(f"\n\n---- REMOVED COMPONENTS FROM ENTITY ----\n")

    def ecs_set(self, entity, *components):
        """
        Set the attribute values for the components component_instance belonging to the entity.
        Format: (ComponentType, {"attr": value})

        Supports inheritance and overriding. If the entity does not have the component it will check for the component through inheritance.
        if the component is found through inheritance it will add the component to itself and update the data over-riding the inheritance.

        This operation would rarely be utilised to over-ride inheritance so although in the cases it does there is some performance considerations
        there is no real need to be overly concerned. Methods such as get_component are O(1) in non-inheritance cases and O(n) at worse for entities
        with many IsA pairs, it is extremely unlikely an entity will have enough IsA pairs to have any significant performance impacts.
        """

        for component_data in components:
            component_type = component_data[0]
            attributes = component_data[1]

            logger.info(f"""
            Setting component attributes:

            ENTITY:
                - ID:   {entity}
                - NAME: {self.__entity_index.get_name(entity)}
                        
            COMPONENT:
                - ID:   {component_type}
                - NAME: {self.__entity_index.get_name(component_type)}

            ATTRIBUTES: {attributes}
            
            """)

            component_instance = self.get_component(entity, component_type, check_inheritance=False)

            if component_instance is None:
                logger.debug(f"Failed to get_component without inheritance... attempting to get_component with inheritance: ")
                # If there is no component_instance we need to check if there it exists within inheritance
                # Since we are using the component_instance for the parent as the default we need to get their
                # component_instance

                inherited_instance = self.get_component(entity, component_type, check_inheritance=True) # Get the component through inheritance

                if not inherited_instance:
                    # There is no inherited instance ethier
                    logger.error(f"\nFailed to get inherited component, skipping:\nCOMPONENT: {component_type}\nNAME: {self.__entity_index.get_name(component_type)}\nATTRIBUTES: {attributes}")
                    continue

                # Override by adding the component to self
                self.ecs_add(entity, component_type)

                # The component is added but the default dataclass attributes will be used
                # Therefore we need to over-ride them with not only the attributes being set
                # but also the attributes from the component_instance that has been inherited

                inherited_attributes = {field.name: getattr(inherited_instance, field.name)for field in fields(inherited_instance)} # Get all the data from the inherited component_instance
                inherited_attributes.update(attributes) # Replace all data that is being set
                attributes = inherited_attributes # Set attributes to the dictonary accounting for the inherited defaults.

                logger.debug(f"\nUpdated attributes to include inherited components:\nATTRIBUTES: {attributes}")
                component_instance = self.get_component(entity, component_type, check_inheritance=False) # Get the current component_instance that was just added.
            else:
                logger.debug(f"Succesfully got_component without inheritance: {component_instance}")

            # Update all the data
            for attr_name, attr_val in attributes.items():  # For attr, value specified for change
                if hasattr(component_instance, attr_name):  # If the component_instace has that attribute
                    logger.debug(f"Setting {attr_name} to {attr_val}")
                    setattr(component_instance, attr_name, attr_val)    # update the attribute values
        
        logger.success(f"Successfully set entity components.")
                
    def is_alive(self, entity: int | str) -> bool:
        """
        Liveliness check for entities uses entity generation to check against current version being passed.
        """

        # Get the encoded_entity through the passed in entity
        encoded_entity = self.__entity_index.get_encoded_entity(entity)

        # Compare the generation of the encoded and decoded entity
        return BitmanipulationHelper().compare_generation(encoded_entity, entity)

    # -- GETS --

    def get_component(self, entity: int | str, component: int | str, check_inheritance: bool = True, check_can_toggle: bool = True) -> object:
        """
        GROUP A:
            Recursive algorithms
            Graph/Tree Traversal
            Complex user-defined algorithms (eg optimisation, minimisation, scheduling, pattern matching) or equivalent difficulty?

        Returns the component instance belonging to the entity
        
        Gets through inheritance on failure to accomdate IsA inheritance.
        """

        # Get record and archetype respectively.
        record = self.__entity_index.entity_record(entity)
        archetype = record.archetype

        # Check if column is none
        if isinstance(column_index := self.__entity_index.get_component_column(component, archetype), int):
            # Column_index is an integer as expected.
            component_instance = archetype.columns[column_index][record.row]
            logger.debug(f"got component_instance for entity: {component_instance}")

            # Check if component is_enabled

            if check_can_toggle and not self.is_enabled(entity):
                return None

            return component_instance

        if not check_inheritance:
            # Skip inheritance check 
            return None

        if self.has_ecs_dont_inherit(component):
            # Skip don't inherit
            return None

        # Inheritance time
        IsAWildcard = self.pair(self.EcsIsA, self.EcsWildcard) # The entity / pair for all IsA relationships
        wildcard_map = self.__entity_index.get_archetype_map(IsAWildcard) # Map of all archetypes with an IsA relationship

        if not isinstance(indexs := wildcard_map.get(archetype), list):
            # No IsA relationships to check
            return None

        # Indexs is a list of the index of IsA relationships within the archetype
        for index in indexs:
            pair = archetype.type[index]
            _, target = BitmanipulationHelper().decode_pair(pair)

            # Try to get_component from the target.
            if (component_instance := self.get_component(target, component)) is not None:
                logger.debug(f"got component_instance for entity through inheritance: {component_instance}")
                return component_instance
        return None

    def __get_all_relationship_pair_indexs_from(self, source: int | Archetype, relationship: int | str):
        """
        Returns a list of index's referencing the pairs in the archetype made from the relationship.
        """

        if not isinstance(source, Archetype):
            source = self.__entity_index.get_archetype(source)

        wildcard_pair = self.pair(relationship, self.EcsWildcard)

        if not isinstance(wildcard_map := self.__entity_index.get_archetype_map(wildcard_pair), dict):
            # Failed to get wildcard_map
            return None

        return wildcard_map.get(source)

    def __get_all_relationship_pairs_from(self, source: int | Archetype, relationship: int | str):
        """
        Returns all the pairs of a given relationship within an archetype
        
        Possibly add inheritance checking, although it would need to avoid traits.
        """
        
        # I just need to get the index of the (relationship, *) for that archetype
        # then use the indexs to get the pairs in the archetype
        if not isinstance(source, Archetype):
            source = self.__entity_index.get_archetype(source)

        if not isinstance(indexs := self.__get_all_relationship_pair_indexs_from(source, relationship), list):
            return None
    
        pairs = [source.type[index] for index in indexs]
        return pairs

    def __get_ecs_with_components_from(self, component: int, components: list[int] = None):
        """
        GROUP A:
            Graph/Tree Traversal
            Recursive algorithms
            Stack/Queue Operations (with_pairs used as abstract stack)
            Complex user-defined algorithms (eg optimisation, minimisation, scheduling, pattern matching) or equivalent difficulty

        Returns a list of components in which the component is connected to through the with trait.
        Recursively calls to get all with components from with'd components.
        """

        if not hasattr(self, "EcsWith"):
            return None

        # Set the components if they don't already exist, use none to avoid mutable defaults
        if components is None:
            components = []
            logger.info(f"Getting all components connected through ecs_with trait from component {self.__entity_index.get_name(component)}")

        # Get's all the with pairs of the entity directly.
        with_pairs = self.__get_all_relationship_pairs_from(component, self.EcsWith)
        
        # If it's a pair then we shold check if the pair's relationship has any with_pairs.
        # No recursion required here, just get the relationships with_pairs, the same rules will be applied later.
        if self.is_pair(component):
            # If it's a pair decode the relationship and target 
            relationship, target = BitmanipulationHelper().decode_pair(component)

            # Get any wild_cards from the relationship.
            relationship_with_pairs = self.__get_all_relationship_pairs_from(relationship, self.EcsWith)

            # extend the with_pairs with the list if it's not none
            if isinstance(relationship_with_pairs, list):
                if isinstance(with_pairs, list):
                    # Extend if with_pairs already exist
                    with_pairs.extend(relationship_with_pairs)
                else:
                    # Otherwise set
                    with_pairs = relationship_with_pairs

        if with_pairs: logger.critical(f"with_pairs = {tuple(self.__entity_index.get_name(pair) for pair in with_pairs)}")

        if not isinstance(with_pairs, list):
        # if not isinstance(with_pairs := self.__get_all_relationship_pairs_from(component, self.EcsWith), list):
            if not components is None or len(components) != 0:
                logger.debug(f"returning components from get_ecs_with_components: {tuple(self.__entity_index.get_name(type_c) for type_c in components)}")
            return components

        for with_pair in with_pairs:
            _, target = BitmanipulationHelper().decode_pair(with_pair)

            logger.critical(f"target: {target}, name: {self.__entity_index.get_name(target)}")

            # If the target of the with is a relationship
            if self.is_relationship(target):
                # The relationship will take on the target of the component
                # This assumes the component is a pair
                _, pair_target = BitmanipulationHelper().decode_pair(component)
                target = self.pair(target, pair_target)

            # Add the target to our list of components
            components.append(target)

            logger.debug(f"Got component {self.__entity_index.get_name(target)} from ecs_with trait on {self.__entity_index.get_name(component)}")
            components = self.__get_ecs_with_components_from(target, components) # call recursively to check for with's on the gotten component

        return components

    def __get_entities_from_archetype_map(self, archetype_map: dict) -> list:
        """Returns a list of entities from the archetype in the archetype_map"""

        entities = [] # A flat list of all the entites

        for archetype in archetype_map.keys():
            # For each archetype add all the entities to the entities list.
            entities.extend(archetype.entities)
        return entities
        
    def get_children(self, entity: int):
        """Returns all the chiildren of the entity."""    

        # Lookup all archetypes with (ChildOf, Entity)
        # automatic generation isn't required, if it has no children we just return None
        pair = BitmanipulationHelper().encode_pair(self.EcsChildOf, entity)

        # Try to get archetype_map
        if not isinstance(archetype_map := self.__entity_index.get_archetype_map(pair), dict):
            # No archetype_map, therefore return none
            return None

        # get all entities from the archetypes.
        entities = self.__get_entities_from_archetype_map(archetype_map)
        logger.debug(f"Got all children for entity: Entity(id={entity}, name={self.__entity_index.get_name(entity)}) : {entities}")
        return entities

    def get_parent(self, entity: int):
        """Returns the parent of the entity."""

        # (ChildOf, parent) is within the archetype
        # so I just have to get the target of that component.
        if not isinstance(child_of_pairs := self.__get_all_relationship_pairs_from(entity, self.EcsChildOf), list):
            return None
        
        # ChildOf is exclusive so there should only be one pair
        _, parent = BitmanipulationHelper().decode_pair(child_of_pairs[0])
        logger.debug(f"Got parent of entity: Entity(id={entity}, name={self.__entity_index.get_name(entity)}) : Parent(id={parent}, name={self.__entity_index.get_name(parent)})")
        return parent
    
    def get_wildcard_pair(self, entity: int):
        """Return the wildcard pair of the entity"""
        return self.pair(entity, self.EcsWildcard) if self.is_relationship(entity) else self.pair(self.EcsWildcard, entity)

    # -- ARCHETYPE CACHE --

    def traverse_archetype_cache(self, source: Archetype, operation_backlog: list, components: tuple[int], entity: int, is_add: bool):
        """
        Returns the archetype with the components added / removed by traversing the archetype_cache.

        This is essentially just a grid, each archetype has it's own cache that has add and remove edges for each component
        that has previously been added or removed. There is never more than one component as a key to an edge.

        The archetypes are thus nodes with their edges being traversed through the components, getting to the next node
        and adding or removing the respective component.
        """

        # utilising components tuple as a stack, pushing everything onto the stack would be additonal O(n) operation.
        key = "add" if is_add else "remove"
        current_index = 0
        current_archetype_record: ArchetypeRecord = self.__archetype_index.archetype_record(source.type)

        while current_index < len(components):
            component = components[current_index]
            archetype = current_archetype_record.archetype
            archetype_cache = current_archetype_record.archetype_cache

            if not isinstance(component_cache := archetype_cache.get(component), dict):
                # Construct new cache if cache existing
                component_cache = archetype_cache[component] = {"add": None, "remove": None}
                logger.debug(f"Constructed a new component cache for component: Component(id={component}, name={self.__entity_index.get_name(component)})")

            if not isinstance(archetype_record := component_cache.get(key), ArchetypeRecord):
                logger.debug(f"Creating archetype cache for component: Component(id={component}, name={self.__entity_index.get_name(component)}) with key {key}")

                if is_add: destination_components = self.construct_destination_archetype_for_add_edge(archetype, operation_backlog, component, entity)
                else: destination_components = self.construct_destination_archetype_for_remove_edge(archetype, operation_backlog, component, entity)

                archetype_record = self.archetype(*destination_components)

                component_cache[key] = archetype_record
                logger.debug(f"Cached archetype_record in archetype_cache: Archetype(type={tuple(self.__entity_index.get_name(type_c) for type_c in archetype_record.archetype.type)}) for Component(id={component}, name={self.__entity_index.get_name(component)}) with key {key}")
            
            current_archetype_record = archetype_record # Update the record used to traverse cache
            current_index += 1 # iterate to next component

        archetype = current_archetype_record.archetype
        logger.info(f"Traversed archetype_cache getting destination_archetype: Archetype(type={tuple(self.__entity_index.get_name(type_c) for type_c in archetype.type)})")

        return archetype

    def construct_destination_archetype_for_remove_edge(self, source_archetype: Archetype, operation_backlog: list, component: int, entity: int):
        """Returns the destination archetypes type with validation and traits applied"""
        if not self.entity_has_component(source_archetype, component, check_inheritance=False):
            # The component already exists and therefore is invalid, immeditaley skip
            logger.warning(f"Component cannot be removed from source_archetype as component is not in source_archetype.")
            return source_archetype.type

        if self.is_pair(component):
            relationship, target = BitmanipulationHelper().decode_pair(component)

            if self.has_ecs_symmetric(relationship):

                # Symmetric Pair would be the relationship paired with the current entity.
                symmetric_pair = world.pair(relationship, entity)

                # If the entity does not have the symmetric relationship add it to the backlog otherwise leave.
                if self.entity_has_component(target, symmetric_pair):
                    operation_backlog.append(lambda: self.ecs_remove(target, symmetric_pair))

                    logger.debug(f"Removing symmetric_pair from target entity: Pair(id={symmetric_pair}, name={self.__entity_index.get_name(symmetric_pair)})")

        return tuple(type_c for type_c in source_archetype.type if type_c != component)

    def construct_destination_archetype_for_add_edge(self, source_archetype: Archetype, operation_backlog: list, component: int, entity: int):
        """
        GROUP A:
            Complex user-defined algorithms (eg optimisation, minimisation, scheduling, pattern matching) or equivalent difficulty
            Stack/Queue operations: unvalidated components is treated as a queue
            Can be recursive due to symmetry trait

        Returns the destination archetypes type with validation and traitss applied
        """

        if self.entity_has_component(source_archetype, component, check_inheritance=False):
            # The component already exists and therefore is invalid, immeditaley skip
            logger.warning(f"Component cannot be added to source_archetype as component is already in source_archetype.")
            return source_archetype.type

        has_final_trait = self.has_ecs_final(source_archetype)
        if has_final_trait and self.pair_relationship_is(component, self.EcsIsA):
            logger.warning(f"Cannot add IsA pair to source_archetype as archetype has trait EcsFinal.")
            return source_archetype.type

        unvalidated_components = self.__get_unvalidated_components(component)

        validated_exclusive_relationships = set() # A set of exclusive relationships that have been validated, reduces need for redundant checks.
        validated_components = set() # A set allows for faster lookups and order is not really needed.

        # A list of indexs that need to be removed from the source_archetype before final creation.
        source_component_filter = [] 

        # Validate the components

        # Treat the unvalidated_components like a stack
        while unvalidated_components:
            component = unvalidated_components.pop(0) # Pop to replicate stack behaviour

            # Make sure it's not a duplicate
            if self.entity_has_component(source_archetype, component, check_inheritance=False) or component in validated_components:
                logger.warning(f"Invalid component {component} skipped as already in archetype / validated_components.")    
                continue

            # I wonder if I could do the exclusive check here
            if self.is_pair(component):
                relationship, target = BitmanipulationHelper().decode_pair(component)

                if relationship == self.EcsIsA:
                    if has_final_trait:
                        # Invalid cannot add IsA trait if has_final_trait
                        continue

                if self.has_ecs_exclusive(relationship):
                    self.__process_exclusive_component(
                        source_archetype, 
                        validated_components, 
                        validated_exclusive_relationships, 
                        source_component_filter, 
                        relationship
                    )

                if self.has_ecs_symmetric(relationship):

                    # Symmetric Pair would be the relationship paired with the current entity.
                    symmetric_pair = world.pair(relationship, entity)

                    # If the entity does not have the symmetric relationship add it to the backlog otherwise leave.
                    if not self.entity_has_component(target, symmetric_pair):
                        operation_backlog.append(lambda: self.ecs_add(target, symmetric_pair))

                        logger.debug(f"Adding symmetric_pair to target entity: Pair(id={symmetric_pair}, name={self.__entity_index.get_name(symmetric_pair)})")

            # At this point it's valid
            if component == self.EcsFinal: has_final_trait = True   # Keep flag up to date

            validated_components.add(component)

        # Filter out the source_archetype
        filtered_components = self.__get_filtered_source_components(source_archetype.type, source_component_filter)

        # Should be left with only valid components and a list of valid source_components
        logger.debug(f"filtered source_components: {filtered_components}")

        filtered_components.extend(validated_components)
        destination_components = filtered_components

        # Critical just so it's obvious
        logger.info(f"Constructed destination components for add_edge: Components{tuple(self.__entity_index.get_name(component) for component in destination_components)}")
        return destination_components

    # -- Helper methods to abstract add cache constrction. --
    def __get_unvalidated_components(self, component: int):
        """
        Returns a list of components gotten from a component through traits and relationships.
        
        Mostly intended to abstract construction of add componet.
        """

        unvalidated_components = [component,] # component has not gone through full validation
        ecs_with_components = self.__get_ecs_with_components_from(component) # Get all components through with relationship
        # Get other components here...

        # Extend the unvalidated components list, check if not before extending.
        if ecs_with_components is not None: unvalidated_components.extend(ecs_with_components)

        return unvalidated_components

    def __process_exclusive_component(self, source_archetype: Archetype, validated_components: set[int], validated_exclusive_relationships: set[int], source_component_filter: list[int], relationship: int):
        """
        Processes the result of the exclusive trait on a given entity
        """

        # If the same relationship has been validated then replace it.
        if relationship in validated_exclusive_relationships:
            # Remove the prevous validated_relationship.
            validated_components = {
                validated_component for validated_component in validated_components
                if BitmanipulationHelper().decode_entity(validated_component) != relationship
            }
            # no need to remove the validated_relationship in validated_exclusive_relationship as it is being replaced.
            logger.debug(f"Removed previous validated exclusive pair component for relationship {relationship}")
        else:
            # If the exclusive relationship was validated then source_archetype does not have
            # the relationship or the logic has applied, therefore no need to repeat the logic.

            # Check if there is existing indexs through the (relationship, *) map.
            indexs = self.__get_all_relationship_pair_indexs_from(source_archetype, relationship)

            # If there are indexs (Should be None or 1, although should account for the possibility of more just in case.)
            if isinstance(indexs, list):
                # Add the indexs to the filter.
                for index in indexs:
                    logger.debug(f"Adding obselete exclusive relationship to filter: {index}")
                    source_component_filter.append(index)
            
            validated_exclusive_relationships.add(relationship)
        
        logger.debug(f"processed exclusive relationship component.")

    def __get_filtered_source_components(self, source_components: tuple[int], source_component_filter: list[int]):
        """filters source components for components that need to be removed as a result of traits."""
        offset = 0
        source_components = list(source_components)
        for index in source_component_filter:
            adjusted_index = index - offset
            filtered_entity = source_components.pop(adjusted_index)
        return source_components

    # -- HAS --

    def entity_has_component(self, source: int | str | Archetype, component: int | str, check_inheritance: bool = True, check_can_toggle: bool = True, logging: bool = True) -> bool:
        """
        GROUP A:
            Complex user-defined algorithms (eg optimisation, minimisation, scheduling, pattern matching) or equivalent difficulty
            Recursive algorithms
            Graph/Tree Traversal

        Returns True if entity has the component, accounts of inheritance.
        
        check_inheritance -> prevents errors from occuring during initialisation.
        """

        # Get archetype and the components archetype_map respectively 
        if not isinstance(source, Archetype):
            source = self.__entity_index.get_archetype(source)

        archetype_map = self.__entity_index.get_archetype_map(component)

        # Perform base test to check if entity_has_component directly.
        if source in archetype_map:
            # Check if it has can_toggle
            return self.is_enabled(component) if check_can_toggle else True

        if not check_inheritance:
            return False

        if self.has_ecs_dont_inherit(component):
            return False
        
        # Don't Inherit is a trait for individual components.

        # Entity does not have component so we need to check through inheritance:
        # Inheritance is achieved through the IsA relationship, if it has inheritance it must have an IsARelationship
        # We can check if it has an IsA relationship by checking if the archetype is in (IsA, *) archetype

        IsAWildcard = self.pair(self.EcsIsA, self.EcsWildcard) # The entity / pair for all IsA relationships
        wildcard_map = self.__entity_index.get_archetype_map(IsAWildcard) # Map of all archetypes with an IsA relationship

        # Get the indexs in the archetype of all IsA relationships
        if not isinstance(indexs := wildcard_map.get(source), list):
            # There is no entry for the archetype therefore it does not have an IsA relationship.
            return False

        # There is a list of indexs corresponding to the archetype
        # The indexs reference the index of the relationship within the archetypes_type
        
        for index in indexs:
            pair = source.type[index] # Get the pair
            
            # Get relationship and target, relationship should be an IsA relationship but good for logging
            _, target = BitmanipulationHelper().decode_pair(pair)

            # We now need to check if the target has the component, this is completed recursively to account for inheritance
            if self.entity_has_component(target, component):
                # The component has been found, return True, no need to check remaining relationships
                return True

        return False

    # -- is_types --

    def is_component(self, entity: int | str):
        """Returns True if entity is any type of component."""
        if not hasattr(self, "EcsComponent"): return False
        return self.entity_has_component(entity, self.EcsComponent, check_inheritance = False, logging=False)

    def is_tag(self, entity: int | str):
        if not hasattr(self, "EcsTag"): return False
        return self.entity_has_component(entity, self.EcsTag, check_inheritance = False, logging=False)

    def is_entity(self, entity: int | str):
        """Returns True if entity is a base entity (not including components, etc.)"""
        if not hasattr(self, "EcsEntity"): return False
        return self.entity_has_component(entity, self.EcsEntity, check_inheritance = False, logging=False)

    def is_relationship(self, entity: int | str):
        if not hasattr(self, "EcsRelationship"): return False
        return self.entity_has_component(entity, self.EcsRelationship, check_inheritance = False, logging=False)

    def is_pair(self, entity: int | str):
        if not hasattr(self, "EcsPair"): return False
        return self.entity_has_component(entity, self.EcsPair, check_inheritance = False, logging=False)

    def is_enabled(self, entity: int | str):
        """Returns True if component has CanToggle trait and is toggled else False"""
        if not hasattr(self, "EcsCanToggle"):
            return True

        if (can_toggle := self.get_component(entity, self.EcsCanToggle, check_inheritance=False, check_can_toggle=False)) is None:
            return True

        return can_toggle.toggle

    def pair_relationship_is(self, pair: int | str, relationship: int | str):
        """Returns True if the pair's relationship is the given relationship"""
        pair_relationship, target = BitmanipulationHelper().decode_pair(pair)
        return relationship == pair_relationship

    def has_relationship(self, source: int | Archetype, relationship: int) -> bool:
        """Returns True if entity has the given relationship else False -> O(1)"""

        if not isinstance(archetype := source, Archetype):
            # source is an entity, get it's archetype
            archetype = self.__entity_index.get_archetype(source)
        
        if not hasattr(self, "EcsWildcard"):
            return False

        relationship_wildcard = BitmanipulationHelper().encode_pair(relationship, self.EcsWildcard)
        wildcard_archetype = self.__entity_index.get_archetype_map(relationship_wildcard)

        return archetype in wildcard_archetype

    def has_target(self, source: int | Archetype, target: int):
        """Returns True if entity has the given target else False -> O(1)"""
        if not isinstance(archetype := source, Archetype):
            # source is an entity, get it's archetype
            archetype = self.__entity_index.get_archetype(source)
        
        if not hasattr(self, "EcsWildcard"):
            return False

        relationship_wildcard = BitmanipulationHelper().encode_pair(self.EcsWildcard, target)
        wildcard_archetype = self.__entity_index.get_archetype_map(relationship_wildcard)

        return archetype in wildcard_archetype

    # -- HAS TRAITS --

    def has_ecs_is_a(self, source: int | Archetype) -> bool:
        """Returns True if the source has EcsIsA pair. """
        if not hasattr(self, "EcsIsA"): return False
        return self.has_relationship(source, self.EcsIsA)

    def has_ecs_with(self, source: int | Archetype) -> bool:
        """Returns True if the source has EcsWith trait. """
        if not hasattr(self, "EcsWith"): return False
        return self.has_relationship(source, self.EcsWith)

    def has_ecs_final(self, source: int | Archetype) -> bool:
        """Returns True if the source has EcsFinal trait. """
        if not hasattr(self, "EcsFinal"): return False
        return self.entity_has_component(source, self.EcsFinal, check_inheritance=False, logging=False)

    def has_ecs_dont_inherit(self, source: int | Archetype) -> bool:
        if not hasattr(self, "EcsDontInherit"):
            return False

        if not isinstance(source, Archetype):
            source = self.__entity_index.get_archetype(source)

        return self.entity_has_component(source, self.pair(self.EcsOnInstantiate, self.EcsDontInherit), check_inheritance=False)

    def has_ecs_exclusive(self, source: int | Archetype) -> bool:
        if not hasattr(self, "EcsExclusive"): return
        return self.entity_has_component(source, self.EcsExclusive, check_inheritance=False, logging=False)

    def has_ecs_symmetric(self, source: int | Archetype) -> bool:
        if not hasattr(self, "EcsSymmetric"): return
        return self.entity_has_component(source, self.EcsSymmetric, check_inheritance=False, logging=False)

    def has_ecs_can_toggle(self, source: int | Archetype) -> bool:
        if not hasattr(self, "EcsCanToggle"): return
        return self.entity_has_component(source, self.EcsCanToggle, check_inheritance=False, logging=False, check_can_toggle=False)

    # -- Queries --
    def query(self):
        return QueryBuilder(self, self.__archetype_index, self.__entity_index)

    def get_names(self, entites):
        return tuple(self.__entity_index.get_name(entity) for entity in entites)

start = time.perf_counter()
world = World()
end = time.perf_counter()
print(f"The timetaken to initialise the world was: {end - start}")
entity_index = world.entity_index
archetype_index = world.archetype_index

class TestWorld(unittest.TestCase):
    # Initilsation
    def test_bootstrap_component(self):
        # EcsComponent is the first entity and should have autoincremented id of 1
        self.assertEqual(world.EcsComponent, 1)

        # EcsComponent should have generated a archetype in the archetype index
        archetype = archetype_index.archetype(world.EcsComponent)

        # Test the archetypes construction
        # do not test values as they will include other components from initilisation
        self.assertIsInstance(archetype, Archetype)
        self.assertEqual(archetype.type, (world.EcsComponent,))

        # Test the entity record
        entity_record = entity_index.entity_record(world.EcsComponent)
        self.assertIsInstance(entity_record, EntityRecord)

        # Test the values
        self.assertEqual(entity_record.entity, 1) # test fll entity id
        self.assertEqual(entity_record.name, "EcsComponent") # test name is properly registered
        self.assertEqual(entity_record.archetype, archetype) # test archetype is properly registered
        # Ignore row as manipulated throughout initilisation.

        # Test the component record
        component_record  = entity_record.component_record
        self.assertIsInstance(component_record, ComponentRecord)
        self.assertEqual(component_record.type, ComponentRecord)

        # Test the archetype map
        archetype_map = component_record.archetype_map
        self.assertIsInstance(archetype_map, dict)
        self.assertIn(archetype, archetype_map) # archetype should be registered to the archetype_map
        self.assertEqual(archetype_map[archetype], 0) # index in archetype should be 0

    def test_bootstrap_tag(self):
        # EcsTag should autoincrement therefore being 2
        self.assertEqual(world.EcsTag, 2)

        # EcsTag should have generated a archetype in the archetype index
        archetype = archetype_index.archetype((world.EcsComponent, world.EcsTag))

        # Test the archetypes construction
        # do not test values as they will include other components from initilisation
        self.assertIsInstance(archetype, Archetype)
        self.assertEqual(archetype.type, (world.EcsComponent, world.EcsTag))

        # Test the entity record
        entity_record = entity_index.entity_record(world.EcsTag)
        self.assertIsInstance(entity_record, EntityRecord)

        # Test the values
        self.assertEqual(entity_record.entity, 2) # test full entity id
        self.assertEqual(entity_record.name, "EcsTag") # test name is properly registered
        self.assertEqual(entity_record.archetype, archetype) # test archetype is properly registered
        # Ignore row as manipulated throughout initilisation.

        # Test the component record
        component_record  = entity_record.component_record
        self.assertIsInstance(component_record, ComponentRecord)
        self.assertIsNone(component_record.type)

        # Test the archetype map
        archetype_map = component_record.archetype_map
        self.assertIsInstance(archetype_map, dict)
        self.assertIn(archetype, archetype_map) # archetype should be registered to the archetype_map
        self.assertEqual(archetype_map[archetype], 1) # index in archetype should be 1
        self.assertEqual(archetype.column_map[1], -1) # Test that the column map for the archetype is -1
        
    def test_traits_registered_to_world(self):
        """A general check that each trait has been registered to the world."""

        # A list of all traits to be tested
        traits = [
            world.EcsComponent, world.EcsTag, world.EcsEntity, world.EcsRelationship, world.EcsPair,
            world.EcsPairIsTag, world.EcsFinal, world.EcsOnInstantiate, world.EcsDontInherit, world.EcsExclusive,
            world.EcsSymmetric, world.EcsCanToggle, world.EcsWildcard, world.EcsIsA, world.EcsChildOf, world.EcsWith
        ]
        
        for trait in traits: 
            # Test that each trait has been registered to the entity_index
            entity_record = entity_index.entity_record(trait)
            
            # Test that the entity record for each trait can be gotten succesfully
            self.assertIsInstance(entity_record, EntityRecord)

            # Test that each trait is assigned an archetype
            archetype = entity_record.archetype
            self.assertIsInstance(archetype, Archetype)

            # Each traits name should start with Ecs
            self.assertTrue(entity_record.name.startswith("Ecs"))

            # Every trait is a component type so they should be in the archetype map.
            self.assertIn(archetype, entity_index.get_archetype_map(world.EcsComponent))

    # basic get & has methods
    def test_get_component_without_traits(self):
        """Basic test for get method without traits / inheritance."""

        # EcsComponent should have an EcsComponent Component
        component_record = world.get_component(world.EcsComponent, world.EcsComponent, check_inheritance=False, check_can_toggle=False)
        
        # Test the data retrieved is correct therefore validating the method worked
        self.assertIsInstance(component_record, ComponentRecord)
        self.assertEqual(component_record.type, ComponentRecord)

        # Test the method returns safely on failure.
        self.assertIsNone(world.get_component(world.EcsComponent, world.EcsIsA, check_inheritance=False, check_can_toggle=False))

    def test_has_component_without_traits(self):
        """Basic test for has method without traits / inheritance."""

        # EcsComponent should have an EcsComponent Component
        self.assertTrue(world.entity_has_component(world.EcsComponent, world.EcsComponent, check_inheritance=False, check_can_toggle=False))
        # EcsComponent should not have EcsIsA trait
        self.assertFalse(world.entity_has_component(world.EcsComponent, world.EcsIsA, check_inheritance=False, check_can_toggle=False))
        
        # has_component can check with archetypes, e.g. checking if an archetype has a component
        archetype = world.archetype(world.EcsComponent, world.EcsTag).archetype # component, tag archetype
        self.assertTrue(world.entity_has_component(archetype, world.EcsComponent, check_inheritance=False, check_can_toggle=False))
        self.assertTrue(world.entity_has_component(archetype, world.EcsTag, check_inheritance=False, check_can_toggle=False))
        self.assertFalse(world.entity_has_component(archetype, world.EcsIsA, check_inheritance=False, check_can_toggle=False))

    def test_type_trait_checks(self):
        """Tests that the check for each type trait is working as intended."""
        test_entity = world.entity(name="TypeTraitTestEntity")

        # is_component tests if the entity is any kind of component
        self.assertTrue(world.is_component(world.EcsComponent))
        self.assertTrue(world.is_component(world.EcsTag))
        self.assertTrue(world.is_component(world.EcsEntity))
        self.assertTrue(world.is_component(world.EcsRelationship))
        self.assertTrue(world.is_component(world.EcsPair))
        # is_component will return false if the component is an entity
        self.assertFalse(world.is_component(test_entity))

        # is_tag tests if the entity is any kind of tag
        self.assertFalse(world.is_tag(world.EcsComponent))
        self.assertTrue(world.is_tag(world.EcsTag))
        self.assertTrue(world.is_tag(world.EcsEntity))
        self.assertTrue(world.is_tag(world.EcsRelationship))
        self.assertTrue(world.is_tag(world.EcsPair))
        # is_tag will return false if the component is an entity
        self.assertFalse(world.is_tag(test_entity))

        # is_entity tests if the entity is a base entity
        self.assertFalse(world.is_entity(world.EcsComponent))
        self.assertFalse(world.is_entity(world.EcsTag))
        self.assertFalse(world.is_entity(world.EcsEntity))
        self.assertFalse(world.is_entity(world.EcsRelationship))
        self.assertFalse(world.is_entity(world.EcsPair))
        # is_entity will return true if the component is an entity
        self.assertTrue(world.is_entity(test_entity))

        # is_relationship will return true if the component is any type of relationship
        self.assertFalse(world.is_relationship(world.EcsComponent))
        self.assertFalse(world.is_relationship(world.EcsTag))
        self.assertFalse(world.is_relationship(world.EcsEntity))
        self.assertFalse(world.is_relationship(world.EcsRelationship))
        self.assertFalse(world.is_relationship(world.EcsPair))
        # is_relationship will return true if the component is an entity
        self.assertFalse(world.is_relationship(test_entity))

        # Relationships on initilisation are all tags
        self.assertTrue(world.is_relationship(world.EcsIsA))

        # is_pair will return true if the component is a pair... there are no pairs on initilisation.
        self.assertFalse(world.is_pair(world.EcsComponent))
        self.assertFalse(world.is_pair(world.EcsTag))
        self.assertFalse(world.is_pair(world.EcsEntity))
        self.assertFalse(world.is_pair(world.EcsRelationship))
        self.assertFalse(world.is_pair(world.EcsPair))
        # is_pair will return true if the component is an entity
        self.assertFalse(world.is_pair(test_entity))

        test_pair = world.pair(world.EcsOnInstantiate, world.EcsDontInherit)
        self.assertTrue(world.is_pair(test_pair))

    # Entity construction
    def test_entity_construction(self):
        """Intensive test for entity base construction."""
        # Test the base entity is constructed as intended
        unnamed_entity = world.entity(name=None)
        dummy_entity = world.entity(name="Dummy")

        # The entities should be registered to the world in the EcsEntity archetype
        unnamed_entity_record = entity_index.entity_record(unnamed_entity)
        dummy_entity_record = entity_index.entity_record(dummy_entity)

        self.assertIsInstance(unnamed_entity_record, EntityRecord)
        self.assertIsInstance(dummy_entity_record, EntityRecord)

        # Test default / injected name
        self.assertEqual(unnamed_entity_record.name, "UnnamedEntity")
        self.assertEqual(dummy_entity_record.name, "Dummy")
        
        # Use dummy from here as fundamentally the same
        entity_record = dummy_entity_record
        archetype = entity_record.archetype

        # Fresh entity should be registered to EcsEntity archetype
        self.assertIsInstance(archetype, Archetype)
        self.assertEqual(archetype, archetype_index.archetype(world.EcsEntity))

        # Entity should not have a component record
        self.assertIsNone(entity_record.component_record)

    def test_component_construction(self):
        """Intensive test for component base construction."""

        # Component dataclass for testing
        dummy_component_dataclass = make_dataclass(
            cls_name="DummyComponent",
            fields=(
                ("dummy_value", int, 5),
            )
        )

        dummy_component = world.component(type=dummy_component_dataclass)

        # Test the component is registered to the world.
        entity_record = entity_index.entity_record(dummy_component)
        self.assertIsInstance(entity_record, EntityRecord)

        # Test the entity_record data
        self.assertEqual(entity_record.name, "DummyComponent")

        archetype = entity_record.archetype

        # Fresh component should be registered to EcsComponent archetype
        self.assertIsInstance(archetype, Archetype)
        self.assertEqual(archetype, archetype_index.archetype(world.EcsComponent))

        # Component should have a component record with the dataclass as the type
        component_record = entity_record.component_record
        self.assertIsInstance(component_record, ComponentRecord)
        self.assertEqual(component_record.type, dummy_component_dataclass)

        # Component is of type component
        self.assertTrue(world.is_component(dummy_component))

    def test_tag_construction(self):
        """Intensive test for tag base construction."""
        dummy_tag = world.tag(name="DummyTag")

        # Test the tag is registered to the world.
        entity_record = entity_index.entity_record(dummy_tag)
        self.assertIsInstance(entity_record, EntityRecord)

        # Test the entity_record data
        self.assertEqual(entity_record.name, "DummyTag")

        archetype = entity_record.archetype

        # Fresh component should be registered to EcsComponent, EcsTag.
        self.assertIsInstance(archetype, Archetype)
        self.assertEqual(archetype, archetype_index.archetype((world.EcsComponent, world.EcsTag)))

        # Component should have a component record with the dataclass as None
        component_record = entity_record.component_record
        self.assertIsInstance(component_record, ComponentRecord)
        self.assertIsNone(component_record.type)

        # Tag is of type tag
        self.assertTrue(world.is_tag(dummy_tag))

    def test_relationship_construction(self):
        """Intensive test for relationship base component"""

        # Relationships can ethier be tags or components 
        dummy_relationship_component_dataclass = make_dataclass(
            cls_name="DummyRelationshipComponent",
            fields=(
                ("dummy_value", 5, int),
            )
        )

        # Construct both types
        dummy_relationship_component = world.relationship(type=dummy_relationship_component_dataclass)
        dummy_relationship_tag = world.relationship(type=None, name="DummyRelationshipTag")
        logger.error(f"{entity_index.__dict__.get('_EntityIndex__name_index')}")

        # Both should be relationships
        self.assertTrue(world.is_relationship(dummy_relationship_component))
        self.assertTrue(world.is_relationship(dummy_relationship_tag))

        # However, component should be component and not tag
        self.assertFalse(world.is_tag(dummy_relationship_component))
        self.assertTrue(world.is_tag(dummy_relationship_tag))

        # The generation besides this is the same as other methods
        # The adding is done through ecs_add therefore if this is robust this is also robust.

    def test_pair_construction(self):
        """Intensive test for relationship base component"""


        # Pairs are constructed from relationships and targets
        dummy_entity_target = world.entity(name="DummyEntityTarget")
        dummy_component_target = world.component(type=make_dataclass(
            cls_name="DummyComponentTarget",
            fields=(
                ("dummy_value", int, 5),
            )
        ))

        dummy_relationship_component_dataclass = make_dataclass(
            cls_name="DummyRelationshipComponent",
            fields=(
                ("dummy_value", int, 5),
            )
        )

        # Construct both types
        dummy_relationship_component = world.relationship(type=dummy_relationship_component_dataclass)
        dummy_relationship_tag = world.relationship(name="DummyRelationshipTag")

        # Get the precreated dummy components
        self.assertIsInstance(dummy_relationship_component, int)
        self.assertIsInstance(dummy_relationship_tag, int)

        # pairs with entity targets
        component_entity_pair = world.pair(dummy_relationship_component, dummy_entity_target)
        tag_entity_pair = world.pair(dummy_relationship_tag, dummy_entity_target)

        # pairs with component targets
        component_component_pair = world.pair(dummy_relationship_component, dummy_component_target)
        tag_component_pair = world.pair(dummy_relationship_tag, dummy_component_target)

        pairs = [component_entity_pair, tag_entity_pair, component_component_pair, tag_component_pair]

        for pair in pairs:
            # Check that the pairs are registered as pairs.
            self.assertTrue(world.is_pair(pair))

            # Check the names are constructed from the relationship and target
            relationship, target = BitmanipulationHelper().decode_pair(pair)
            self.assertEqual(entity_index.get_name(pair), f"{entity_index.get_name(relationship)}{entity_index.get_name(target)}")

            # Check that a wildcard pair has been created for the relationship and the target
            self.assertIn(world.get_wildcard_pair(relationship), entity_index.entities)
            self.assertIn(world.get_wildcard_pair(target), entity_index.entities)

        # Test algorithm for pair typing
        # Not including traits

        # component_entity_pair should have the relationship type as it is a component
        self.assertFalse(world.is_tag(component_entity_pair))
        self.assertEqual(entity_index.get_component_type(component_entity_pair), entity_index.get_component_type(dummy_relationship_component))

        # tag_entity_pair should have nethier the relationship or pair type and therefore be a tag
        self.assertTrue(world.is_tag(tag_entity_pair))

        # component_component_pair should priotise the relationship having the relationship pair
        self.assertFalse(world.is_tag(component_entity_pair))
        self.assertEqual(entity_index.get_component_type(component_entity_pair), entity_index.get_component_type(dummy_relationship_component))

        # tag_component_pair should have the targets type
        self.assertFalse(world.is_tag(tag_component_pair))
        self.assertEqual(entity_index.get_component_type(tag_component_pair), entity_index.get_component_type(dummy_component_target))

    # Testing adding / removing without inheritance or traits
    def test_move_entity_without_traits(self):
        dummy_dragon = world.entity("DummyDragon") # Dragon entity for testing
        dummy_tag = world.tag("DummyTag") # Tag entity for testing

        # Dummy dragon will be in the entity source archetype
        # In this case a new archetype should be constructed for the move with (EcsEntity, DummyTag)
        # In this case no acutal instance data is being moved.
        dummy_dragon.add(dummy_tag)

        entity_record = entity_index.entity_record(dummy_dragon)
        archetype = entity_record.archetype

        # The archetype should now be (EcsEntity, DummyTag)
        self.assertEqual(archetype, world.archetype(world.EcsEntity, dummy_tag).archetype)

        # Test that the entity is within the archetype
        self.assertIn(dummy_dragon, archetype.entities)

        # Test that the entity has the dummy_tag component
        self.assertIn(dummy_tag, archetype.type) # Through linear search
        self.assertTrue(world.entity_has_component(archetype, dummy_tag, check_inheritance=False, check_can_toggle=False)) # Through my entity component system

        # Test the archetype column_map is constructed as expected
        self.assertEqual(archetype.column_map, [-1, -1])

        # Test that the entity_row has been updated
        self.assertEqual(archetype.entities[entity_record.row], dummy_dragon)

        # Test that the archetype map of dummy_tag is updated correctly
        self.assertIn(archetype, entity_index.get_archetype_map(dummy_tag))

        # Test adding multiple components with acutal values
        dummy_component_one = world.component(type=make_dataclass(cls_name="DummyComponentOne", fields=(("dummy_number", int, 1),)))
        dummy_component_two = world.component(type=make_dataclass(cls_name="DummyComponentTwo", fields=(("dummy_number", int, 2),)))

        dummy_dragon.add(dummy_component_one, dummy_component_two)

        archetype = entity_record.archetype

        # The archetype should now be (EcsEntity, DummyTag, DummyComponentOne, DummyComponentTwo)
        self.assertEqual(archetype, world.archetype(world.EcsEntity, dummy_tag, dummy_component_one, dummy_component_two).archetype)

        # The archetype map should be [-1, -1, 0, 1]
        self.assertEqual(archetype.column_map, [-1, -1, 0, 1])

        # The entities row should still be viable
        self.assertEqual(archetype.entities[entity_record.row], dummy_dragon)

        # The entity should no longer be in the previous archetype
        self.assertNotIn(dummy_dragon, world.archetype(world.EcsEntity, dummy_tag).archetype.entities)

        # Test move from components
        dummy_component_three = world.component(type=make_dataclass(cls_name="DummyComponentThree", fields=(("dummy_number", 3, int),)))

        dummy_dragon.add(dummy_component_three)

        # The archetype should now be (EcsEntity, DummyTag, DummyComponentOne, DummyComponentTwo, DummyComponentThree)
        # we already know this works so no need to test and reset archetype

        # The component instances should be removed from the previous archetype
        self.assertEqual(len(archetype.columns[0]), 0)
        self.assertEqual(len(archetype.columns[1]), 0)

        # The entity may have a component remoevd
        dummy_dragon.remove(dummy_component_three)
        archetype = entity_record.archetype

        # The archetype should now be (EcsEntity, DummyTag, DummyComponentOne, DummyComponentTwo)
        self.assertEqual(archetype, world.archetype(world.EcsEntity, dummy_tag, dummy_component_one, dummy_component_two).archetype)
        
        # The caches for the remove and add operations should all exist
        archetype_cache = archetype_index.archetype_cache(world.archetype(world.EcsEntity, dummy_tag).archetype)

        # Should have had dummy_component_one in add cache
        self.assertIn(dummy_component_one, archetype_cache)
        archetype_record = archetype_cache[dummy_component_one]["add"]
        self.assertIsInstance(archetype_record, ArchetypeRecord)

        # This archetype should then have the dummy_component_two in the add edge
        archetype_cache = archetype_index.archetype_cache(archetype_record.archetype)

        # Should have had dummy_component_two in add cache
        self.assertIn(dummy_component_two, archetype_cache)
        archetype_record = archetype_cache[dummy_component_two]["add"]
        self.assertIsInstance(archetype_record, ArchetypeRecord)

        # This archetype should then have the dummy_component_three in the add edge
        archetype_cache = archetype_index.archetype_cache(archetype_record.archetype)

        # Should have had dummy_component_three in add cache
        self.assertIn(dummy_component_three, archetype_cache)
        archetype_record = archetype_cache[dummy_component_three]["add"]
        self.assertIsInstance(archetype_record, ArchetypeRecord)

        # This archetype should then have the dummy_component_three in the remove edge
        archetype_cache = archetype_index.archetype_cache(archetype_record.archetype)

        # Should then have dummy_component_three in remove cache
        self.assertIn(dummy_component_three, archetype_cache)
        archetype_record = archetype_cache[dummy_component_three]["remove"]
        self.assertIsInstance(archetype_record, ArchetypeRecord)

    def test_entity_set_without_traits(self):
        dummy_shield = world.entity("DummyShield")
        dummy_defense = world.component(type=make_dataclass(cls_name="DummyDefense", fields=(("defense", int, 100),)))

        dummy_shield.add(dummy_defense)

        # Set the value and test if the change occcured.
        preset_defense = dummy_shield.get(dummy_defense).defense
        self.assertEqual(preset_defense, 100)
        dummy_shield.set((dummy_defense, {"defense": 1000, "invalid_attribute": 10000})) # invalid attribute should not error
        postset_defense = dummy_shield.get(dummy_defense).defense
        self.assertEqual(postset_defense, 1000)

    def test_inheritance(self):
        # Some attributes for testing
        sharpness = world.component(type=make_dataclass(cls_name="Sharpness", fields=(("sharpness", int, 100),)))
        durability = world.component(type=make_dataclass(cls_name="Durability", fields=(("durability", int, 100),)))

        # Create two presets to inherit from
        dummy_weapon_preset_one = world.entity(name="WeaponPresetOne").add(sharpness, durability)

        # The default values of this have 2* sharpness but with half durability!
        dummy_weapon_preset_two = world.entity(name="WeaponPresetTwo").add(sharpness, durability)
        dummy_weapon_preset_two.set((sharpness, {"sharpness": 200}), (durability, {"durability": 50}))

        # Two different sword entities that inherit from respective presets
        durable_sword = world.entity(name="DurableSword").is_a(dummy_weapon_preset_one)
        sharp_sword = world.entity(name="SharpSword").is_a(dummy_weapon_preset_two)

        # Test if the checks discover the inheritance.
        self.assertTrue(durable_sword.has(sharpness, durability))
        self.assertTrue(sharp_sword.has(sharpness, durability))

        # Test if the gets give the expected values
        self.assertEqual(durable_sword.get(sharpness).sharpness, 100)
        self.assertEqual(durable_sword.get(durability).durability, 100)

        self.assertEqual(sharp_sword.get(sharpness).sharpness, 200)
        self.assertEqual(sharp_sword.get(durability).durability, 50)

        # Test overriding through set!
        # increase the sharpness, durability should use the inherited instance as a default
        sharp_sword.set((sharpness, {"sharpness": 500})) 

        # expecting sharpness 500 and durability 50
        self.assertEqual(sharp_sword.get(sharpness).sharpness, 500)
        self.assertEqual(sharp_sword.get(durability).durability, 50)

        # the sharpness should be over-riden therefore a check without inheritance returns True
        # the durability shouldn't be overriden therefore a check without inheritance returns False

        self.assertTrue(world.entity_has_component(sharp_sword, sharpness, check_inheritance=False))
        self.assertFalse(world.entity_has_component(sharp_sword, durability, check_inheritance=False))

    def test_trait_ecs_pair_is_tag_logic(self):
        # -- EcsPairIsTag --
        # Entities for demonstration
        orange = world.component(type=make_dataclass(cls_name="Orange", fields=(("acidity", int, 5),)))
        eats = world.relationship(name="Eats").add(world.EcsPairIsTag)

        # Eats relationships should be a tag even if the target has a type / dataclass
        eats_orange = world.pair(eats, orange)
        self.assertTrue(world.is_tag(eats_orange))

    def test_trait_ecs_final_logic(self):
        """Test the trait logic here."""

        # -- EcsFinal ---
        # Entities for demonstration
        monster = world.entity("Monster")
        dragon = world.entity("Dragon")
        snake = world.entity("Snake")

        # Paul is a monster & dragon
        paul = world.entity("Paul").is_a(monster).is_a(dragon)

        # In this case Paul cannot also be a snake! He's a dragon.
        # Therefore Paul is given the final trait to indicate he should not inherit anymore
        paul.add(world.EcsFinal)

        # However, something occurs where we attempt to turn paul into a snake dragon
        paul.is_a(snake)

        # Paul should not have EcsIsASnake added!
        self.assertEqual(world.get_names(entity_index.get_archetype(paul).type), ('EcsEntity', 'EcsFinal', 'EcsIsAMonster', 'EcsIsADragon'))

    def test_trait_ecs_exclusive(self):

        # The ChildOf built-in trait is exclusive.
        # entities for demonstration
        parent_a = world.entity("ParentA")
        parent_b = world.entity("ParentB")
        parent_c = world.entity("ParentC")

        child = world.entity("child")

        # The child is a child_of parent a
        child.child_of(parent_a)

        # Childs archetype type should be ('EcsEntity', 'EcsChildOfParentA)
        self.assertEqual(world.get_names(entity_index.get_archetype(child).type), ('EcsEntity', 'EcsChildOfParentA'))

        # However, parent a tragically dies and the child is adopted...
        child.child_of(parent_b)

        # Childs archetype type should be ('EcsEntity', 'EcsChildOfParentB)
        self.assertEqual(world.get_names(entity_index.get_archetype(child).type), ('EcsEntity', 'EcsChildOfParentB'))

        # Parent A faked their death and comes back for their child
        # Parent C is the enemy of Parent A and steals the child before the ownership is complete
        # Testing if Parent C overrides Parent A when added together...
        child.add(world.pair(world.EcsChildOf, parent_a), world.pair(world.EcsChildOf, parent_c))
        self.assertEqual(world.get_names(entity_index.get_archetype(child).type), ('EcsEntity', 'EcsChildOfParentC'))

    def test_trait_ecs_symmetric(self):
        # Entities for demonstration
        pauls_best_friend = world.entity(name="PaulsBestFriend")
        pauls_girlfriend = world.entity(name="PaulsGirlfriend")
        holding_hands = world.relationship(name="HoldingHands").add(world.EcsSymmetric)

        # If pauls best friend is holding hands with pauls girlfreind
        # pauls girlfriend is holdiing hands with pauls best friend
        pauls_best_friend.add(world.pair(holding_hands, pauls_girlfriend))

        # Test if the opposing symmetric relationship is added to pauls girlfriend
        # Pauls girlfriend should exist within ('EcsEntity', 'HoldingHandsPaulsBestFriend)
        self.assertEqual(world.get_names(entity_index.get_archetype(pauls_girlfriend).type), ('EcsEntity', 'HoldingHandsPaulsBestFriend'))

        # Paul sees them holding hands so they stop
        pauls_girlfriend.remove(world.pair(holding_hands, pauls_best_friend))

        # Pauls beest friend should also lose the symmetric relationship
        self.assertEqual(world.get_names(entity_index.get_archetype(pauls_best_friend).type), ('EcsEntity',))

    def test_trait_ecs_with(self):
        # entities for demonstration
        position = world.component(type=make_dataclass(cls_name="Position", fields=(("x", int, 100), ("y", int, 100))))
        speed = world.component(type=make_dataclass(cls_name="Speed", fields=(("speed", int, 16),)))
        movement = world.tag(name="Movement")

        # For the entity to move they must have a position and a speed
        movement.add(
            world.pair(world.EcsWith, position),
            world.pair(world.EcsWith, speed)
        )

        player = world.entity("Player")

        # The player should have movement, movement should add speed and position aswell
        player.add(movement)

        # All the components should be approved with the entity being added to the following archetype.
        self.assertEqual(world.get_names(entity_index.get_archetype(player).type), ('EcsEntity', 'Position', 'Speed', 'Movement'))

        # In some cases there will be a with chain, meaning that a component that adds a with value should check for the added components own withs
        player_movement = world.tag(name="PlayerMovement").add(world.pair(world.EcsWith, movement))

        # remove the players position, speed and movement for the test
        player.remove(position, speed, movement)
        
        # Ensure correct removal
        self.assertEqual(world.get_names(entity_index.get_archetype(player).type), ('EcsEntity',))

        # adding player_movement should add movement and all it's respective with pairs
        player.add(player_movement)

        # That would result in this archetype as the expected result
        self.assertEqual(world.get_names(entity_index.get_archetype(player).type), ('EcsEntity', 'Position', 'Speed', 'Movement', 'PlayerMovement'))

        # In the case of relationships that have a source pair
        # the relationship should take on the entity that the source pair
        # is with'd

        # entities for testing
        likes = world.relationship(type=None, name="Likes")
        loves = world.relationship(type=None, name="Loves")

        cheese_cake = world.entity(name="Cheesecake")
        cheese_cake_enjoyer = world.entity(name="CheeseCakeEnjoyer")

        # When you love someone or something or also like it
        # Therefore whenever you add a LovesRelationship to an entity
        # The LikesRelationship should also be added to the entity
        loves.add(world.pair(world.EcsWith, likes))

        # Loves cheesecake should also add Likes cheesecake
        cheese_cake_enjoyer.add(world.pair(loves, cheese_cake))

        # Test that the result is as expected.
        self.assertEqual(world.get_names(entity_index.get_archetype(cheese_cake_enjoyer).type), ('EcsEntity', 'LikesCheesecake', 'LovesCheesecake'))

        # Validation and traits are applied whenever a with relationship is applied!
        # I will not test every trait but will use a common case where duplicated results may try to be added
        speedy_boy = world.entity(name="SpeedyBoy").add(speed)

        # Speed should be added
        self.assertEqual(world.get_names(entity_index.get_archetype(speedy_boy).type), ('EcsEntity', 'Speed'))

        # Add movement with working with chain
        speedy_boy.add(movement)

        # Should not be duplicated speed as duplcation removed during validation
        self.assertEqual(world.get_names(entity_index.get_archetype(speedy_boy).type), ('EcsEntity', 'Position', 'Speed', 'Movement'))

    # Testing the entity builder methods is unneeded as tested throughout other tests
    # Testing queries
    def test_querying(self):
        world = World() # Utilising a fresh world instance to ensure queries are not overwritten.

        # Tag entities for testing
        # I will be using purely tags for the most part for more concise testing
        health = world.tag(name="Health")
        level = world.tag(name="Level")
        defense = world.tag(name="Defense")
        speed = world.tag(name="Speed")

        # I will construct the archetypes so they appear within queries
        test_archetypes = [
            world.archetype(health).archetype,
            world.archetype(health, level).archetype,
            world.archetype(health, level, defense).archetype,
            world.archetype(health, level, defense, speed).archetype,
        ]

        # select query should select every archetype with the component in the type
        # this should select all the archetypes with health, meaning all 4 archetypes
        health_archetypes = world.query().select_(health).execute()

        # The result should be equal to our testing list (unsorted so cast to sets)
        self.assertSetEqual(set(health_archetypes), set(test_archetypes))

        # This can be tested by selecting each element individually.
        level_archetypes = world.query().select_(level).execute()
        defense_archetypes = world.query().select_(defense).execute()
        speed_archetypes = world.query().select_(speed).execute()

        # Level should have (health, level), (health, level, defense), (health, level, defense, speed)
        # It should not have just (health,) therefore everything excluding the first archetype
        self.assertSetEqual(set(test_archetypes[1:]), set(level_archetypes))

        # The construction of archetype means the same test with an additonal split can be applied for each
        self.assertSetEqual(set(test_archetypes[2:]), set(defense_archetypes))
        self.assertSetEqual(set(test_archetypes[3:]), set(speed_archetypes))

        # Now that select is working the basic logic gates should be tested
        # if we wanted every archetype that has health and defense for some calculation.
        archetypes = world.query().select_(health).with_(defense).execute()

        # This should have the last two archetypes within the test archetypes
        self.assertSetEqual(set(test_archetypes[2:]), set(archetypes))

        # To test the with_any I can get all archetypes with ethier level or defense
        archetypes = world.query().select_(health).with_any_(level, defense).execute()

        # This should have (health, level), (health, level, defense) and (health, level, defense, speed)
        # whereas with does not include (health, level) as it did not have defense
        self.assertSetEqual(set(test_archetypes[1:]), set(archetypes))

        # with_ethier is an exclusive or meaning it can only have one of the components
        archetypes = world.query().select_(health).with_ethier_(level, speed).execute()

        # This should have (health, level), (health, level, defense) but not (health, level, defense, speed)
        # This is because the final test archetype has both level and speed
        self.assertSetEqual(set([test_archetypes[1], test_archetypes[2]]), set(archetypes))

        # The without trait can be tested simply by getting health archetypes without defense
        archetypes = world.query().select_(health).without_(defense).execute()

        # This should return (health), (health, level) and none others as they all include defense
        self.assertSetEqual(set(test_archetypes[:2]), set(archetypes))

        # without trait will look for a complete match meaning if the query has multiple components
        archetypes = world.query().select_(health).without_(defense, speed).execute()

        # This should have (health, level, defense) as it does not include "speed"
        self.assertSetEqual(set(test_archetypes[:3]), set(archetypes))

        # In contrast without_any is a NOR meaning (health, level, defense would not be included)
        archetypes = world.query().select_(health).without_any_(defense, speed).execute()
        self.assertSetEqual(set(test_archetypes[:2]), set(archetypes))

        # This tests the logic gates effectively, testing shortcuts effectively requires more setup.

        dragon = world.entity(name="Dragon").add(health, level, speed, defense)
        wyvern = world.entity(name="Wyvern").child_of(dragon) # Subspecies of dragon
        drake = world.entity(name="Drake").child_of(dragon)

        # Get all children of dragon
        dragon_subspecies = world.query().select_(world.EcsEntity).child_of_(dragon).execute()
        
        # This should return a singular archetype with both wyvern and drake within the entities
        self.assertEqual(len(dragon_subspecies), 1) # Should only have one entry
        self.assertEqual(world.get_names(dragon_subspecies[0].entities), ('Wyvern', 'Drake')) # Contains correct entities

        # Test if is_a works as expected
        paul_the_dragon = world.entity("PaulTheDragon").is_a(dragon)
        jonathon_the_dragon = world.entity("JohnathonTheDragon").is_a(dragon)

        # Get all archetypes that inherit from dragon
        inherits_from_dragon = world.query().select_(world.EcsEntity).is_a_(dragon).execute()

        # This should return a singular archetype with both paul and jonathon within the entities
        self.assertEqual(len(dragon_subspecies), 1) # Should only have one entry
        self.assertEqual(world.get_names(inherits_from_dragon[0].entities), ('PaulTheDragon', 'JohnathonTheDragon')) # Contains correct entities
        
if __name__ == "__main__":
    unittest.main(verbosity=2)


