import math
from panda3d.core import (
    GeomVertexFormat, GeomVertexData, Geom, 
    GeomVertexWriter, GeomTriangles, GeomNode, 
    LVector3, LColor, NodePath
)

from common import *

logging_setup()
logger_cell = logging.getLogger(__name__)


# Class for creating position, geometry and color
class Cell:
    def __init__(self, hex_color, pos, geometry_type, hpr, width, height, gravity):
       
        if not isinstance(gravity, bool):
            raise TypeError(f"Argument 'gravity' must be boolean, not {type(gravity).__name__}")

        if not isinstance(geometry_type, string):
            raise TypeError(f"Argument 'geometry_type' must be 'rhombic_dodecahedron'.")



        self.x = pos[0]
        self.y = pos[1]
        self.z = pos[2]
        self.width = width
        self.height = height

        if geometry_type == "rhombic_dodecahedron":
            self.node_path = self.generate_rhombic_dodecahedron(self.x, self.y, self.z, self.width)
        else:
            raise ValueError(f"Unsupported geometry: {geometry_type}")

        # Set Position and Rotation
        self.node_path.setPos(pos)
        self.node_path.setHpr(hpr)
 
        # Apply Color
        self.set_hex_color(hex_color)
   
    def render_cell(self):    
        self.node_path.reparentTo(render)
       
    def set_hex_color(self, hex_str):
        hex_str = hex_str.lstrip('#')
        r, g, b = tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))
        # Normalize to 0.0 - 1.0
        self.node_path.setColor(r/255, g/255, b/255, 1.0)


    def generate_rhombic_dodecahedron(self, x, y, z, total_width=1.0):
        # s is the 'unit' size. Tips are at 2s.
        s = total_width / 4.0
        world_pos = LVector3(x, y, z)

        # 1. Setup Data - using V3N3 (no textures) for simplicity
        geom_format = GeomVertexFormat.getV3n3()
        vdata = GeomVertexData('rhombic', geom_format, Geom.UHStatic)
        vertex = GeomVertexWriter(vdata, 'vertex')
        normal = GeomVertexWriter(vdata, 'normal')
        tris = GeomTriangles(Geom.UHStatic)

        # 2. Define the 14 Vertices
        v = [
            # Cube (0-7)
            LVector3( s, s, s), LVector3( s, s,-s), LVector3( s,-s, s), LVector3( s,-s,-s),
            LVector3(-s, s, s), LVector3(-s, s,-s), LVector3(-s,-s, s), LVector3(-s,-s,-s),
            # Octahedron / Tips (8-13)
            LVector3( 2*s, 0, 0), LVector3(-2*s, 0, 0), # +X (8), -X (9)
            LVector3(0,  2*s, 0), LVector3(0, -2*s, 0), # +Y (10), -Y (11)
            LVector3(0, 0,  2*s), LVector3(0, 0, -2*s)  # +Z (12), -Z (13)
        ]

        def add_face(p1, p2, p3, p4):
            """p1: center tip, p2/p4: side cube corners, p3: opposite tip"""
            start = vdata.getNumRows()
            pts = [v[p1], v[p2], v[p3], v[p4]]
            
            # Calculate outward normal
            edge1 = pts[1] - pts[0]
            edge2 = pts[2] - pts[0]
            norm = edge1.cross(edge2)
            norm.normalize()

            for p in pts:
                vertex.addData3(p + world_pos)
                normal.addData3(norm)
            
            # Two triangles for the diamond
            tris.addVertices(start, start + 1, start + 2)
            tris.addVertices(start, start + 2, start + 3)

        # 3. Define the 12 Diamond Faces
        # Top Cap (Connected to +Z tip: index 12)
        add_face(12, 0, 10, 4) # Top-Front (+Y)
        add_face(12, 4,  9, 6) # Top-Left (-X)
        add_face(12, 6, 11, 2) # Top-Back (-Y)
        add_face(12, 2,  8, 0) # Top-Right (+X)

        # Bottom Cap (Connected to -Z tip: index 13)
        add_face(5, 10, 1, 13) # Bottom-Front (+Y)
        add_face(7, 9, 5, 13) # Bottom-Left (-X)
        add_face(3, 11, 7, 13) # Bottom-Back (-Y)
        add_face(1, 8, 3, 13) # Bottom-Right (+X)

        # Middle Ring (Side connectors)
        add_face(1, 10, 0, 8)  # Side +X/+Y
        add_face(5, 9, 4, 10)  # Side +Y/-X
        add_face(7, 11, 6, 9) # Side -X/-Y
        add_face(3, 8, 2, 11)  # Side -Y/+X

        # 4. Finalize
        geom = Geom(vdata)
        geom.addPrimitive(tris)
        node = GeomNode('rhombic_cell')
        node.addGeom(geom)
        return NodePath(node)



class BaseCell(Cell):
    def __init__(self, hex_color, pos, geometry_type, hpr=LVector3, width, height, gravity):
        super().__init__(hex_color, pos, geometry_type, hpr=LVector3, width, height, gravity)
        
        logger_cell.info("------------- Generating Base-Cell -------------")
        if not isinstance(gravity, bool):
            raise TypeError(f"Argument 'gravity' must be boolean, not {type(gravity).__name__}")    


class BoneCell(Cell):
    def __init__(self, hex_color, pos, geometry_type, hpr=LVector3, width, height, gravity):
    ┊   super().__init__(hex_color, pos, geometry_type, hpr=LVector3, width, height, gravity)
    ┊
    ┊   logger_cell.info("------------- Generating Bone-Cell -------------")
    ┊   if not isinstance(gravity, bool):
    ┊   ┊   raise TypeError(f"Argument 'gravity' must be boolean, not {type(gravity).__name__}")


class GliderCell(Cell):
    def __init__(self, hex_color, pos, geometry_type, hpr=LVector3, width, height, gravity):
    ┊   super().__init__(hex_color, pos, geometry_type, hpr=LVector3, width, height, gravity)
    ┊
    ┊   logger_cell.info("------------- Generating Glider-Cell -------------")
    ┊   if not isinstance(gravity, bool):
    ┊   ┊   raise TypeError(f"Argument 'gravity' must be boolean, not {type(gravity).__name__}")


class MuscleCell(Cell):
    def __init__(self, hex_color, pos, geometry_type, hpr=LVector3, width, height, gravity):
    ┊   super().__init__(hex_color, pos, geometry_type, hpr=LVector3, width, height, gravity)
    ┊
    ┊   logger_cell.info("------------- Generating Muscle-Cell -------------")
    ┊   if not isinstance(gravity, bool):
    ┊   ┊   raise TypeError(f"Argument 'gravity' must be boolean, not {type(gravity).__name__}")


class FinCell(Cell):
    def __init__(self, hex_color, pos, geometry_type, hpr=LVector3, width, height, gravity):
    ┊   super().__init__(hex_color, pos, geometry_type, hpr=LVector3, width, height, gravity)
    ┊
    ┊   logger_cell.info("------------- Generating Fin-Cell -------------")
    ┊   if not isinstance(gravity, bool):
    ┊   ┊   raise TypeError(f"Argument 'gravity' must be boolean, not {type(gravity).__name__}")


class HardCell(Cell):
    def __init__(self, hex_color, pos, geometry_type, hpr=LVector3, width, height, gravity):
    ┊   super().__init__(hex_color, pos, geometry_type, hpr=LVector3, width, height, gravity)
    ┊
    ┊   logger_cell.info("------------- Generating Base-Cell -------------")
    ┊   if not isinstance(gravity, bool):
    ┊   ┊   raise TypeError(f"Argument 'gravity' must be boolean, not {type(gravity).__name__}")


class OpticCell(Cell):
    def __init__(self, hex_color, pos, geometry_type, hpr=LVector3, width, height, gravity):
    ┊   super().__init__(hex_color, pos, geometry_type, hpr=LVector3, width, height, gravity)
    ┊
    ┊   logger_cell.info("------------- Generating Optic-Cell -------------")
    ┊   if not isinstance(gravity, bool):
    ┊   ┊   raise TypeError(f"Argument 'gravity' must be boolean, not {type(gravity).__name__}")


class GastricCell(Cell):
    def __init__(self, hex_color, pos, geometry_type, hpr=LVector3, width, height, gravity):
    ┊   super().__init__(hex_color, pos, geometry_type, hpr=LVector3, width, height, gravity)
    ┊
    ┊   logger_cell.info("------------- Generating Gastric-Cell -------------")
    ┊   if not isinstance(gravity, bool):
    ┊   ┊   raise TypeError(f"Argument 'gravity' must be boolean, not {type(gravity).__name__}")


class ExcretionCell(Cell):
    def __init__(self, hex_color, pos, geometry_type, hpr=LVector3, width, height, gravity):
    ┊   super().__init__(hex_color, pos, geometry_type, hpr=LVector3, width, height, gravity)
    ┊
    ┊   logger_cell.info("------------- Generating Excretion-Cell -------------")
    ┊   if not isinstance(gravity, bool):
    ┊   ┊   raise TypeError(f"Argument 'gravity' must be boolean, not {type(gravity).__name__}")


class PhotosyntheticCell(Cell):
    def __init__(self, hex_color, pos, geometry_type, hpr=LVector3, width, height, gravity):
    ┊   super().__init__(hex_color, pos, geometry_type, hpr=LVector3, width, height, gravity)
    ┊
    ┊   logger_cell.info("------------- Generating Photosynthetic-Cell -------------")
    ┊   if not isinstance(gravity, bool):
    ┊   ┊   raise TypeError(f"Argument 'gravity' must be boolean, not {type(gravity).__name__}")


class EnergyStorageCell(Cell):
    def __init__(self, hex_color, pos, geometry_type, hpr=LVector3, width, height, gravity):
    ┊   super().__init__(hex_color, pos, geometry_type, hpr=LVector3, width, height, gravity)
    ┊
    ┊   logger_cell.info("------------- Generating Energy-Storage-Cell -------------")
    ┊   if not isinstance(gravity, bool):
    ┊   ┊   raise TypeError(f"Argument 'gravity' must be boolean, not {type(gravity).__name__}")


class NeuralCell(Cell):
    def __init__(self, hex_color, pos, geometry_type, hpr=LVector3, width, height, gravity):
    ┊   super().__init__(hex_color, pos, geometry_type, hpr=LVector3, width, height, gravity)
    ┊
    ┊   logger_cell.info("------------- Generating Base-Cell -------------")
    ┊   if not isinstance(gravity, bool):
    ┊   ┊   raise TypeError(f"Argument 'gravity' must be boolean, not {type(gravity).__name__}")








