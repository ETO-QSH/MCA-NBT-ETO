"""
Create empty chunk
"""
from typing import List, Union
from .biome import Biome
from .block import Block
from .empty_section import EmptySection
from .errors import OutOfBoundsCoordinates, EmptySectionAlreadyExists
from . import nbt

WORLD_VERSION = 2844 # 21w43a Minecraft 1.18 snapshot 7
#WORLD_VERSION = 3953 # 1.21
NUM_SECTIONS_PER_CHUNK = 24

class EmptyChunk:
    """
    Used for making own chunks

    Attributes
    ----------
    x: :class:`int`
        Chunk's X position
    z: :class:`int`
        Chunk's Z position
    sections: List[:class:`anvil.EmptySection`]
        List of all the sections in this chunk
    version: :class:`int`
        Chunk's DataVersion
    """

    __slots__ = ('x', 'z', 'sections', 'version')
    def __init__(self, x: int, z: int, version: int = WORLD_VERSION):
        self.x = x
        self.z = z
        self.version = version
        self.sections: List[Union[EmptySection,None]] = [None] * NUM_SECTIONS_PER_CHUNK

    def add_section(self, section: EmptySection, replace: bool = True):
        """
        Adds a section to the chunk

        Parameters
        ----------
        section
            Section to add
        replace
            Whether to replace section if one at same Y already exists
        
        Raises
        ------
        anvil.EmptySectionAlreadyExists
            If ``replace`` is ``False`` and section with same Y already exists in this chunk
        """
        if section.y < -4 or section.y + 4 > NUM_SECTIONS_PER_CHUNK:
            raise OutOfBoundsCoordinates('section Y is too high.')
        if self.sections[section.y + 4] and not replace:
            raise EmptySectionAlreadyExists(f'EmptySection (Y={section.y}) already exists in this chunk')
        self.sections[section.y + 4] = section

    def get_block(self, x: int, y: int, z: int) -> Block:
        """
        Gets the block at given coordinates
        
        Parameters
        ----------
        int x, z
            In range of 0 to 15
        y
            In range of -64 to 319

        Raises
        ------
        anvil.OutOfBoundCoordidnates
            If X, Y or Z are not in the proper range

        Returns
        -------
        block : :class:`anvil.Block` or None
            Returns ``None`` if the section is empty, meaning the block
            is most likely an air block.
        """
        if x < 0 or x > 15:
            raise OutOfBoundsCoordinates(f'X ({x!r}) must be in range of 0 to 15')
        if z < 0 or z > 15:
            raise OutOfBoundsCoordinates(f'Z ({z!r}) must be in range of 0 to 15')
        if y < -64 or y > 319:
            raise OutOfBoundsCoordinates(f'Y ({y!r}) must be in range of 0 to 255')
        section = self.sections[ (y + 64) // 16]
        if section is None:
            return None
        return section.get_block(x, y % 16, z)

    def set_block(self, block: Block, x: int, y: int, z: int):
        """
        Sets block at given coordinates
        
        Parameters
        ----------
        int x, z
            In range of 0 to 15
        y
            In range of -64 to 319

        Raises
        ------
        anvil.OutOfBoundCoordidnates
            If X, Y or Z are not in the proper range
        
        """
        if x < 0 or x > 15:
            raise OutOfBoundsCoordinates(f'X ({x!r}) must be in range of 0 to 15')
        if z < 0 or z > 15:
            raise OutOfBoundsCoordinates(f'Z ({z!r}) must be in range of 0 to 15')
        if y < -64 or y > 319:
            raise OutOfBoundsCoordinates(f'Y ({y!r}) must be in range of 0 to 255')
        section = self.sections[ (y + 64) // 16]
        if section is None:
            section = EmptySection( y // 16)
            self.add_section(section)
        section.set_block(block, x, y % 16, z)


    def set_biome(self, biome: Biome, x: int, y: int, z: int):
        """
        Sets biome at given coordinates
        
        Parameters
        ----------
        int x, z
            In range of 0 to 15
        y
            In range of -64 to 319

        Raises
        ------
        anvil.OutOfBoundCoordidnates
            If X, Y or Z are not in the proper range
        
        """
        if x < 0 or x > 15:
            raise OutOfBoundsCoordinates(f'X ({x!r}) must be in range of 0 to 15')
        if z < 0 or z > 15:
            raise OutOfBoundsCoordinates(f'Z ({z!r}) must be in range of 0 to 15')
        if y < -64 or y > 319:
            raise OutOfBoundsCoordinates(f'Y ({y!r}) must be in range of 0 to 255')
        section = self.sections[ (y + 64) // 16]
        if section is None:
            section = EmptySection( y // 16)
            self.add_section(section)
        section.set_biome(biome, x // 4, (y % 16) // 4, z // 4)

    def save(self) -> nbt.NBTFile:
        """
        Saves the chunk data to a :class:`NBTFile`

        Notes
        -----
        Does not contain most data a regular chunk would have,
        but minecraft stills accept it.
        """
        root = nbt.NBTFile()
        root.tags.append(nbt.TAG_Int(name='DataVersion',value=self.version))
        #level = nbt.TAG_Compound()
        # Needs to be in a separate line because it just gets
        # ignored if you pass it as a kwarg in the constructor
        root.tags.extend([
            nbt.TAG_List(name='Entities', type=nbt.TAG_Compound),
            nbt.TAG_List(name='block_entities', type=nbt.TAG_Compound),
            nbt.TAG_List(name='LiquidTicks', type=nbt.TAG_Compound),
            nbt.TAG_Int(name='xPos', value=self.x),
            nbt.TAG_Int(name='zPos', value=self.z),
            nbt.TAG_Long(name='LastUpdate', value=0),
            nbt.TAG_Long(name='InhabitedTime', value=0),
            nbt.TAG_Byte(name='isLightOn', value=1),
            nbt.TAG_String(name='Status', value='full')
        ])
        sections = nbt.TAG_List(name='sections', type=nbt.TAG_Compound)
        for s in self.sections:
            if s:
                p = s.palette()
                # Minecraft does not save sections that are just air
                # So we can just skip them
                if len(p) == 1 and p[0].name() == 'minecraft:air':
                    continue
                sections.tags.append(s.save())
        root.tags.append(sections)
        return root
