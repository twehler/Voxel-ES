import logging
import os
from math import cos, sin, pi

import numpy as np
import panda3d
from direct.showbase.ShowBase import ShowBase
from panda3d.core import (
    GeomVertexFormat, GeomVertexData, Geom, 
    GeomVertexWriter, GeomTriangles, GeomNode, 
    LVector3, LColor, DirectionalLight, AmbientLight, 
    WindowProperties, ClockObject, Loader, loadPrcFileData,
    SamplerState, Texture
)

from common import *

logger_geometry = logging.getLogger(__name__)


class Voxel:

    def __init__(self, texture_coords = (4, 0)):
    
        self.texture_coords = texture_coords

    # creates a voxel which is part of a larger mesh
    # appends data to an existing list
    def generate_embedded(self, x, y, z, v_writer, n_writer, t_writer, tris, vdata, voxel_map):
           
        atlas_res = 90.0       # Total width of your PNG
        tile_full_res = 18.0   # 90 / 5 tiles = 18 pixels per tile slot
        inner_res = 16.0       # The actual texture content (18 - 2 pixels for padding)
        padding = 1            # 1 pixel border on all sides

        # Calculate pixel start for the specific tile
        pixel_u = self.texture_coords[0] * tile_full_res
        pixel_v = self.texture_coords[1] * tile_full_res

        # Inset by padding and add half-texel offset (0.5) to hit the pixel center
        u_start = (pixel_u + padding + 0.5) / atlas_res
        v_start = (pixel_v + padding + 0.5) / atlas_res
        u_end = (pixel_u + padding + inner_res - 0.7) / atlas_res
        v_end = (pixel_v + padding + inner_res - 0.7) / atlas_res

        # Panda3D standart corner mapping
        uvs = [
            (u_start, v_start),
            (u_start, v_end),
            (u_end, v_end),
            (u_end, v_start)
            ]

        if x == 0 and y == 0 and z == 0:  # Only print for first voxel
            print(f"Texture coords: {self.texture_coords}")
            print(f"UV range: u={u_start:.6f} to {u_end:.6f}")
            print(f"UV range: v={v_start:.6f} to {v_end:.6f}")
            print(f"UV coverage: {(u_end - u_start) * atlas_res:.2f} pixels wide")


        # the voxel-map should make it possible to render only the faces which are not between blocks
        # Local helper to add a face to the shared writers
        def add_face(p1, p2, p3, p4, norm):
            
                 
            start = vdata.getNumRows() # counts the already existing vertices

            # generating vertices, normals and colors for a single voxel-face
            for i, p in enumerate([p1, p2, p3, p4]):
                # Apply the (x, y, z) offset here
                v_writer.addData3(p[0] + x, p[1] + y, p[2] + z)
                n_writer.addData3(norm)
                t_writer.addData2(uvs[i][0], uvs[i][1])

            tris.addVertices(start, start + 1, start + 2)
            tris.addVertices(start, start + 2, start + 3)


        # generating all 6 faces of the voxel at their target-position
        # but only if the faces are not between blocks

        # Bottom (check for z - 1)
        if (x, y, z - 1) not in voxel_map:
            add_face((0,0,0), (0,1,0), (1,1,0), (1,0,0), LVector3(0,0,-1))

        # Top (check for z + 1)
        if (x, y, z + 1) not in voxel_map:
            add_face((0,0,1), (1,0,1), (1,1,1), (0,1,1), LVector3(0,0,1))

        # Front (check for y - 1)
        if (x, y - 1, z) not in voxel_map:
            add_face((0,0,0), (1,0,0), (1,0,1), (0,0,1), LVector3(0,-1,0))

        # Back (check for y + 1)
        if (x, y + 1, z) not in voxel_map:
            add_face((1,1,0), (0,1,0), (0,1,1), (1,1,1), LVector3(0,1,0))
        
        # Left (check for x - 1)
        if (x - 1, y, z) not in voxel_map:
            add_face((0,1,0), (0,0,0), (0,0,1), (0,1,1), LVector3(-1,0,0))

        # Right (check for x + 1)
        if (x + 1, y, z) not in voxel_map:
            add_face((1,0,0), (1,1,0), (1,1,1), (1,0,1), LVector3(1,0,0))

        




# This is the object which holds joint voxels (for example a landscape) in an efficient way
class VoxelMesh:
    def __init__(self, base_voxel_object):
        self.base_voxel_object = base_voxel_object 

        self.format = GeomVertexFormat.getV3n3t2()
        self.vdata = GeomVertexData('map_data', self.format, Geom.UHStatic)

        # Create the writers that will be shared by all voxels
        self.vertex = GeomVertexWriter(self.vdata, 'vertex')
        self.normal = GeomVertexWriter(self.vdata, 'normal') 
        self.tris = GeomTriangles(Geom.UHStatic)
        self.texcoord = GeomVertexWriter(self.vdata, 'texcoord')

    def generate_base_terrain(self, x_size, y_size, max_height):
        # Loading Perlin noise
        try:
            h_data = np.load("Perlin/heightmap.npy")
        except FileNotFoundError:
            print("Run perlin.py first!")
            return None

        # We use a dictionary where every key is a tuple (x, y, z) and values are the Voxel objects
        # This "voxel-map" is used to not render faces that are between two voxels
        voxel_map = {}

        logger_geometry.debug("Generating Voxel-Map.")
        for x in range(x_size):
            for y in range(y_size):

                # Mapping Perlin noise on top of the world to create more realistic terrain
                height = int(h_data[x,y] * max_height) 

                for z in range(height + 1):
                    # For a flat 1000x1000 floor, z is always 0
                    pos = (x, y, z)
                    voxel_map[pos] = self.base_voxel_object 

        # Creating test-form floating in sky
        pos1 = (50, 50, 50)
        pos2 = (51, 50, 50)
        pos3 = (52, 50, 50)
        pos4 = (52, 50, 51)
        pos5 = (52, 50, 52)
        voxel_map[pos1] = self.base_voxel_object
        voxel_map[pos2] = self.base_voxel_object
        voxel_map[pos3] = self.base_voxel_object
        voxel_map[pos4] = self.base_voxel_object
        voxel_map[pos5] = self.base_voxel_object
 
        # Drilling a deep hole underneath floating form
        for drillpos in range(30):
            position_to_remove  = (50, 50, drillpos)
            if position_to_remove in voxel_map: 
                del voxel_map[position_to_remove]
            else:
                continue
        
        logger_geometry.debug("Voxel-map successfully generated.")

        for pos, voxel_obj in voxel_map.items():
            vx, vy, vz = pos

            # generating the voxel geometry
            # generate_embedded only generates faces if they are not between voxels
            voxel_obj.generate_embedded(
                vx, vy, vz,
                self.vertex, self.normal, self.texcoord,
                self.tris, self.vdata,
                voxel_map
            )                
        # Create node 
        self.tris.closePrimitive()
        geom = Geom(self.vdata)
        geom.addPrimitive(self.tris)
        node = GeomNode('terrain_node')
        node.addGeom(geom)
        return node


