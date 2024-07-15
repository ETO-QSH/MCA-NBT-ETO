
from mca import Region, Block, EmptyRegion, EmptyChunk, EmptySection
from mca.errors import ChunkNotFound, OutOfBoundsCoordinates
from mca.nbt import NBTFile
from nbt.world import WorldFolder
import random, copy, uuid, re, nbt

ChunkDict = {}
names = locals()
bbmodel_template = {"meta":{"format_version":"4.10","model_format":"java_block","box_uv":False},"name":None,"parent":"","ambientocclusion":False,"front_gui_light":False,"visible_box":[0,0,0],"variable_placeholders":"","variable_placeholder_buttons":[],"unhandled_root_fields":{},"resolution":{"width":16,"height":16},"elements":[],"outliner":[],"textures":[]}
cude_template = {"name":"cube","box_uv":False,"rescale":False,"locked":False,"render_order":"default","allow_mirror_modeling":False,"from":[],"to":[],"autouv":1,"color":0,"origin":[0,0,0],"faces":{"north":{"uv":[0,0,1,1]},"east":{"uv":[0,0,1,1]},"south":{"uv":[0,0,1,1]},"west":{"uv":[0,0,1,1]},"up":{"uv":[0,0,1,1]},"down":{"uv":[0,0,1,1]}},"type":"cube","uuid":None}

def one_chunk_to_bbmodel(DICT):
    for l, y in enumerate(DICT[list(DICT.keys())[0]].keys()):
        for m, z in enumerate(DICT[list(DICT.keys())[0]][y]):
            for n, x in enumerate(z):
                if x != 'None' and x != 'air':
                    UUID = str(uuid.uuid1())
                    cude_template["name"] = x
                    cude_template["from"] = [n,l,m]
                    cude_template["to"] = [n+1,l+1,m+1]
                    cude_template["uuid"] = UUID
                    cude_template["color"] = random.choices(range(0, 16))
                    bbmodel_template["name"] = list(DICT.keys())[0]
                    bbmodel_template["elements"].append(copy.deepcopy(cude_template))
                    bbmodel_template["outliner"].append(copy.deepcopy(UUID))
    bbmodel = str(bbmodel_template)
    bbmodel = re.sub(r"\s+", "", bbmodel)
    bbmodel = bbmodel.replace("'", '"')
    bbmodel = bbmodel.replace("True", 'true')
    bbmodel = bbmodel.replace("False", 'false')
    with open('{}.bbmodel'.format(list(DICT.keys())[0]), 'w') as f:
        print(bbmodel, file=f)

def get_one_chunk(chunk, y_range):
    DICT = {}
    for y in y_range:
        DICT['{}'.format(y)] = []
        for z in range(16):
            DICT['{}'.format(y)].append([])
            for x in range(16):
                DICT['{}'.format(y)][z].append([str(chunk.get_block(x, y, z)).split(':')[1] if ':' in str(chunk.get_block(x, y, z)) else 'None'][0])
    #one_chunk_to_bbmodel({str(chunk):DICT})
    return DICT

def get_chunk_block(world_folder, chunkList):
    world = WorldFolder(world_folder)
    print('Start!!!')
    for chunk in world.get_chunks():
        if str(chunk) in chunkList.keys():
            ChunkDict['{}'.format(chunk)] = copy.deepcopy(get_one_chunk(chunk, chunkList[str(chunk)]))
    #with open('outputETO.txt', 'w') as f:
    #    print(ChunkDict, file=f)
    print('Done!!!')
    return ChunkDict

#get_chunk_block(r'D:\Program Files\PCL2\.minecraft\saves\118', {'Chunk(0,0)': range(-64, 320)})

#def set_single_chunk_block(world_folder, mca_name, blocklist):
#    region = Region.from_file(world_folder+'\\region\\'+mca_name)
#    new_region = EmptyRegion(0, 0)
#    new_chunk_set = set()
#    chunkList = {}
#    nx_nz = set()
#    for block in blocklist:
#        id, x, y, z = block
#        nx, nz, ny = x//16, z//16, y//16
#        names['new_chunk_%s_%s' % (nx, nz)] = EmptyChunk(nx, nz)
#        new_chunk_set.add(names['new_chunk_%s_%s' % (nx, nz)])
#        chunkList['Chunk(%s,%s)' % (nx, nz)] = range(-64, 320)
#        nx_nz.add((nx, nz))
#    ChunkDict = get_chunk_block(world_folder, chunkList)
#    for l in list(ChunkDict):
#        for m in ChunkDict[l].keys():
#            y = int(m)
#            for z, n in enumerate(ChunkDict[l][m]):
#                for x, id in enumerate(ChunkDict[l][m][z]):
#                    if id == 'None':
#                        names['new_chunk_%s_%s' % (l[6:-1].split(",")[0], l[6:-1].split(",")[1])].set_block(Block('air'), x, y, z)
#                    else:
#                        names['new_chunk_%s_%s' % (l[6:-1].split(",")[0], l[6:-1].split(",")[1])].set_block(Block(id), x, y, z)
#    for block in blocklist:
#        id, x, y, z = block
#        nx, nz = x // 16, z // 16
#        names['new_chunk_%s_%s' % (nx, nz)].set_block(Block(id), x%16, y, z%16)
#    for x in range(32):
#        for z in range(32):
#            if (x, z) not in nx_nz:
#                try:
#                    new_region.add_chunk(region.get_chunk(x, z))
#                except ChunkNotFound:
#                    pass
#    for new_chunk in list(new_chunk_set):
#        new_region.add_chunk(new_chunk)
#    new_region.save(world_folder+'\\region\\'+mca_name) # h*(32*16)**2
#
#blocklist = [['diamond_block', 300, 200, 300], ['gold_block', 301, 200, 300], ['gold_block', 300, 200, 301], ['diamond_block', 301, 200, 301]]
#
#set_single_chunk_block(r'D:\Program Files\PCL2\.minecraft\saves\118', 'r.0.0.mca', blocklist)


def set_world_block(world_folder, blocklist):
    chunkList = {}
    #section_set = {}
    new_region_set = {}
    new_chunk_set = {}
    new_section_set = {}
    for block in blocklist:
        id, x, y, z = block
        if 'new_region_%s_%s' % (x//512, z//512) not in new_region_set.keys():
            try:
                names['mca_region_%s_%s' % (x//512, z//512)] = Region.from_file(world_folder+'\\region\\'+'r.{}.{}.mca'.format(x//512, z//512))
                #names['new_region_%s_%s' % (x // 512, z // 512)] = Region(names['mca_region_%s_%s' % (x//512, z//512)])
                names['new_region_%s_%s' % (x//512, z//512)] = EmptyRegion(0, 0)
                for ax in range(32):
                    for az in range(32):
                        try:
                            names['new_region_%s_%s' % (x//512, z//512)].add_chunk(names['mca_region_%s_%s' % (x//512, z//512)].get_chunk(ax, az))
                        except ChunkNotFound:
                            print('Chunk({},{}) not found!'.format(ax, az))
                        except OutOfBoundsCoordinates:
                            print('Chunk({},{}) not found!'.format(ax, az))
                new_region_set['new_region_%s_%s' % (x//512, z//512)] = [names['new_region_%s_%s' % (x//512, z//512)], x//512, z//512]
            except FileNotFoundError:
                print('Region r.{}.{}.mca not found!'.format(x//512, z//512))
        #try:
        #    for ky in range(-4, 20):
        #        names['section_%s_%s_%s' % (x//16, z//16, ky)] = names['mca_region_%s_%s' % (x//512, z//512)].get_chunk(x%512//16, z%512//16).get_section(ky)
        #        section_set['section_%s_%s_%s' % (x//16, z//16, ky)] = [names['section_%s_%s_%s' % (x//16, z//16, ky)], x//16, z//16]
        #except ChunkNotFound:
        #    print('Chunk({},{}) not found!'.format(x%512//16, z%512//16))
        #except KeyError:
        #    print('Chunk({},{}) not found!'.format(x%512//16, z%512//16))
        for ky in range(-4, 20):
            names['new_section_%s_%s_%s' % (x//16, z//16, ky)] = EmptySection(ky)
            new_section_set['new_section_%s_%s_%s' % (x//16, z//16, ky)] = [names['new_section_%s_%s_%s' % (x//16, z//16, ky)], x//16, z//16]
        #names['new_section_%s_%s_%s' % (x//16, z//16, y//16)] = EmptySection(y//16)
        names['new_chunk_%s_%s' % (x//16, z//16)] = EmptyChunk((x%512)//16, (z%512)//16)
        #new_section_set['new_section_%s_%s_%s' % (x//16, z//16, y//16)] = [names['new_section_%s_%s_%s' % (x//16, z//16, y//16)], x//16, z//16]
        new_chunk_set['new_chunk_%s_%s' % (x//16, z//16)] = [names['new_chunk_%s_%s' % (x//16, z//16)], x//512, z//512]
        #chunkList['Chunk(%s,%s)' % (x//16, z//16)] = range((y//16)*16, (y//16)*16+16)
        chunkList['Chunk(%s,%s)' % (x//16, z//16)] = range(-64, 320)

    print(list(new_section_set))
    print(list(new_chunk_set))
    print(list(new_region_set))
    ChunkDict = get_chunk_block(world_folder, chunkList)
    for l in list(ChunkDict):
        for m in ChunkDict[l].keys():
            y = int(m)
            for z, n in enumerate(ChunkDict[l][m]):
                for x, id in enumerate(ChunkDict[l][m][z]):
                    if id == 'None':
                        names['new_section_%s_%s_%s' % (l[6:-1].split(",")[0], l[6:-1].split(",")[1], y//16)].set_block(Block('air'), x, y%16, z)
                    else:
                        names['new_section_%s_%s_%s' % (l[6:-1].split(",")[0], l[6:-1].split(",")[1], y//16)].set_block(Block(id), x, y%16, z)

    for block in blocklist:
        id, x, y, z = block
        names['new_section_%s_%s_%s' % (x//16, z//16, y//16)].set_block(Block(id), x%16, y%16, z%16)

    #for section in list(section_set):
    #    print((type(section_set[section][0])))
    #    names['new_chunk_%s_%s' % (section_set[section][1], section_set[section][2])].add_section(section_set[section][0])

    for section in list(new_section_set):
        names['new_chunk_%s_%s' % (new_section_set[section][1], new_section_set[section][2])].add_section(new_section_set[section][0])

    for chunk in list(new_chunk_set):
        try:
            names['new_region_%s_%s' % (new_chunk_set[chunk][1], new_chunk_set[chunk][2])].add_chunk(new_chunk_set[chunk][0])
        except KeyError:
            print('File r.%s.%s.mca not find!' % (new_chunk_set[chunk][1], new_chunk_set[chunk][2]))

    for region in list(new_region_set):
        try:
            new_region_set[region][0].save(world_folder+'\\region\\'+'r.{}.{}.mca'.format(new_region_set[region][1], new_region_set[region][2]))
        except KeyError:
            print('File r.{}.{}.mca not find!'.format(new_region_set[region][1], new_region_set[region][2]))

blocklist = [['diamond_block', 300, 200, 300], ['gold_block', 301, 200, 300], ['gold_block', 300, 200, 301], ['diamond_block', 301, 200, 301],
             ['diamond_block', 600, 200, 600], ['gold_block', 601, 200, 600], ['gold_block', 600, 200, 601], ['diamond_block', 601, 200, 601],
             ['diamond_block', -400, 200, -400], ['gold_block', -401, 200, -400], ['gold_block', -400, 200, -401], ['diamond_block', -401, 200, -401]]

set_world_block(r'D:\Program Files\PCL2\.minecraft\saves\118', blocklist)
