"""
Chunk class
ref: https://minecraft.wiki/w/Chunk_format
"""
import sys
from typing import Union, Tuple, Generator, Optional

from . import nbt
from .block import Block
from .biome import Biome
from .errors import OutOfBoundsCoordinates, DataNotAvailable


def bin_append(a, b, length=None):
    """
    Appends number a to the left of b
    bin_append(0b1, 0b10) = 0b110
    """
    length = length or b.bit_length()
    return (a << length) | b


def nibble(byte_array, index):
    value = byte_array[index // 2]
    if index % 2:
        return value >> 4
    else:
        return value & 0b1111


class Chunk:
    """
    Represents a chunk from a ``.mca`` file.

    Note that this is read only.

    Attributes
    ----------
    x: :class:`int`
        Chunk's X position
    z: :class:`int`
        Chunk's Z position
    version: :class:`int`
        Version of the chunk NBT structure
    data: :class:`nbt.TAG_Compound`
        Raw NBT data of the chunk
    tile_entities: :class:`nbt.TAG_Compound`
        ``self.data['TileEntities']`` as an attribute for easier use
    """
    __slots__ = ('version', 'data', 'x', 'z', 'tile_entities')

    def __init__(self, nbt_data: nbt.NBTFile):
        try:
            self.version = nbt_data['DataVersion'].value
        except KeyError:
            sys.exit("mcapy does not work with Data Version<2844 (21w43a, or Minecraft 1.18 s7)")

        self.data = nbt_data
        self.x = self.data['xPos'].value
        self.z = self.data['zPos'].value
        self.tile_entities = self.data['block_entities']

    def get_section(self, y: int) -> nbt.TAG_Compound:
        """
        Returns the section at given y index
        can also return nothing if section is missing, aka it's empty

        Parameters
        ----------
        y
            Section Y index

        Raises
        ------
        anvil.OutOfBoundsCoordinates
            If Y is not in range of 0 to 15
        """
        if y < -4 or y > 19:
            raise OutOfBoundsCoordinates(f'Y ({y!r}) must be in range of -4 to 19')

        try:
            sections = self.data["sections"]
        except KeyError:
            return None

        for section in sections:
            if section['Y'].value == y:
                return section

    def get_palette(self, section: Union[int, nbt.TAG_Compound]) -> Tuple[Block]:
        """
        Returns the block palette for given section

        Parameters
        ----------
        section
            Either a section NBT tag or an index


        :rtype: Tuple[:class:`anvil.Block`]
        """
        if isinstance(section, int):
            section = self.get_section(section)
        if section is None:
            return
        return tuple(Block.from_palette(i) for i in section['Palette'])

    def get_block(self, x: int, y: int, z: int, section: Union[int, nbt.TAG_Compound]=None) -> Block:
        """
        Returns the block in the given coordinates

        Parameters
        ----------
        int x, y, z
            Block's coordinates in the chunk
        section : int
            Either a section NBT tag or an index. If no section is given,
            assume Y is global and use it for getting the section.

        Raises
        ------
        anvil.OutOfBoundCoordidnates
            If X, Y or Z are not in the proper range

        :rtype: :class:`anvil.Block`
        """
        if x < 0 or x > 15:
            raise OutOfBoundsCoordinates(f'X ({x!r}) must be in range of 0 to 15')
        if z < 0 or z > 15:
            raise OutOfBoundsCoordinates(f'Z ({z!r}) must be in range of 0 to 15')
        if y < -64 or y > 319:
            raise OutOfBoundsCoordinates(f'Y ({y!r}) must be in range of -64 to 319')

        if section is None:
            section = self.get_section(y // 16)
            # global Y to section Y
            y %= 16

        # If its an empty section its most likely an air block
        if section is None or 'block_states' not in section:
            return Block.from_name('minecraft:air')

        # Number of bits each block is on BlockStates
        # Cannot be lower than 4
        bits = max((len(section['block_states']['palette']) - 1).bit_length(), 4)

        # Get index on the block list with the order YZX
        index = y * 16 * 16 + z * 16 + x

        # BlockStates is an array of 64 bit numbers
        # that holds the blocks index on the palette list
        states = section['block_states']['data']

        state = index // (64 // bits)

        # makes sure the number is unsigned
        # by adding 2^64
        # could also use ctypes.c_ulonglong(n).value but that'd require an extra import
        data = states[state]
        if data < 0:
            data += 2**64

        shifted_data = data >> (index % (64 // bits) * bits)

        # get `bits` least significant bits
        # which are the palette index
        palette_id = shifted_data & 2**bits - 1

        block = section['block_states']['palette'][palette_id]
        return Block.from_palette(block)

    def stream_blocks(self, index: int=0, section: Union[int, nbt.TAG_Compound]=None) -> Generator[Block, None, None]:
        """
        Returns a generator for all the blocks in given section

        Parameters
        ----------
        index
            At what block to start from.

            To get an index from (x, y, z), simply do:

            ``y * 256 + z * 16 + x``
        section
            Either a Y index or a section NBT tag.

        Raises
        ------
        anvil.OutOfBoundCoordidnates
            If `section` is not in the range of 0 to 15

        Yields
        ------
        :class:`anvil.Block`
        """
        if isinstance(section, int) and (section < -4 or section > 19):
            raise OutOfBoundsCoordinates(f'section ({section!r}) must be in range of -4 to 19')

        # For better understanding of this code, read get_block()'s source

        if section is None or isinstance(section, int):
            section = self.get_section(section or 0)

        if section is None or 'block_states' not in section:
            air = Block.from_name('minecraft:air')
            for i in range(4096):
                yield air
            return

        states = section['block_states']['data']
        palette = section['block_states']['palette']

        bits = max((len(palette) - 1).bit_length(), 4)

        state = index // (64 // bits)

        data = states[state]
        if data < 0:
            data += 2**64

        bits_mask = 2**bits - 1

        offset = index % (64 // bits) * bits

        data_len = 64 - offset
        data >>= offset

        while index < 4096:
            if data_len < bits:
                state += 1
                new_data = states[state]
                if new_data < 0:
                    new_data += 2**64

                data = new_data
                data_len = 64

            palette_id = data & bits_mask
            yield Block.from_palette(palette[palette_id])

            index += 1
            data >>= bits
            data_len -= bits

    def stream_chunk(self) -> Generator[Block, None, None]:
        """
        Returns a generator for all the blocks in the chunk

        This is a helper function that runs Chunk.stream_blocks from section 0 to 15

        Yields
        ------
        :class:`anvil.Block`
        """
        for i in range(-4,20):
            for block in self.stream_blocks(section=i):
                yield block

    def get_tile_entity(self, x: int, y: int, z: int) -> Optional[nbt.TAG_Compound]:
        """
        Returns the tile entity at given coordinates, or ``None`` if there isn't a tile entity

        To iterate through all tile entities in the chunk, use :class:`Chunk.tile_entities`
        """
        for tile_entity in self.tile_entities:
            t_x, t_y, t_z = [tile_entity[k].value for k in 'xyz']
            if x == t_x and y == t_y and z == t_z:
                return tile_entity

    def get_biome(self, x: int, y: int, z: int) -> Biome:
        """
        Returns the biome given x, y, z
        """
        if x < 0 or x > 15:
            raise OutOfBoundsCoordinates(f'X ({x!r}) must be in range of 0 to 15')
        if z < 0 or z > 15:
            raise OutOfBoundsCoordinates(f'Z ({z!r}) must be in range of 0 to 15')
        if y < -64 or y > 319:
            raise OutOfBoundsCoordinates(f'Y ({y!r}) must be in range of -64 to 319')

        section = self.get_section(y // 16)
        if 'biomes' not in section:
            raise DataNotAvailable('Biomes are not available')
        
        biomes = section['biomes']
        biomes_palette = biomes['palette']

        # If there is only one biome, 'data' is not required
        if 'data' not in biomes:
            return Biome.from_name(biomes_palette[0].value)

        states = biomes['data']

        index = ((y % 16 // 4) * 4 * 4) + (z // 4) * 4 + (x // 4)
        bits = (len(biomes_palette) - 1).bit_length()
        state = index // (64 // bits)
        data = states[state]

        # makes sure the number is unsigned
        # by adding 2^64
        # could also use ctypes.c_ulonglong(n).value but that'd require an extra import
        if data < 0:
            data += 2**64

        shifted_data = data >> (index % (64 // bits) * bits)
        # TODO: fix here if index can span across 2 64bit numbers

        # get `bits` least significant bits
        # which are the palette index
        palette_id = shifted_data & 2**bits - 1
        return Biome.from_name(biomes_palette[palette_id].value)
