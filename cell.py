import math
from panda3d.core import (
    GeomVertexFormat, GeomVertexData, Geom, 
    GeomVertexWriter, GeomTriangles, GeomNode, 
    LVector3, LColor
)

class Cell:
    def __init__(self, geometry_type = "rhombic_dodecahedron", pos=LVector3(0,0,0), hpr=LVector3(0,0,0), hex_color="#FFFFFF", size=1.0):
       
        self.x = pos[0]
        self.y = pos[1]
        self.z = pos[2]
        self.size = size

        if geometry_type == "rhombic_dodecahedron":
            self.node_path = self.generate_rhombic_dodecahedron(self.x, self.y, self.z, self.size)
        if geometry_type == "dodecahedron":
            self.node_path = self.generate_dodecahedron(self.x, self.y, self.z, self.size)
       
        # attach to world
        self.node_path.reparentTo(render)
         
        # Set Position and Rotation
        self.node_path.setPos(pos)
        self.node_path.setHpr(hpr)
 
        # Apply Color
        self.set_hex_color(hex_color)

      
    def set_hex_color(self, hex_str):
        hex_str = hex_str.lstrip('#')
        r, g, b = tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))
        # Normalize to 0.0 - 1.0
        self.node_path.setColor(r/255, g/255, b/255, 1.0)


    def generate_rhombic_dodecahedron(self, x, y, z, total_width=1.0):
        """
        Generate a rhombic dodecahedron with correct topology.
        
        A rhombic dodecahedron has:
        - 14 vertices (8 from cube + 6 from octahedron)
        - 12 rhombic faces
        - 24 edges
        
        Each rhombic face connects 2 cube vertices and 2 octahedron tips.
        """
        s = total_width / 4.0

        # 14 vertices
        v = [
            # Inner cube vertices (0-7)
            LVector3( s,  s,  s),  # 0
            LVector3( s,  s, -s),  # 1
            LVector3( s, -s,  s),  # 2
            LVector3( s, -s, -s),  # 3
            LVector3(-s,  s,  s),  # 4
            LVector3(-s,  s, -s),  # 5
            LVector3(-s, -s,  s),  # 6
            LVector3(-s, -s, -s),  # 7
            # Outer octahedron tips (8-13)
            LVector3( 2*s,  0,   0),   # 8  (+X)
            LVector3(-2*s,  0,   0),   # 9  (-X)
            LVector3( 0,   2*s,  0),   # 10 (+Y)
            LVector3( 0,  -2*s,  0),   # 11 (-Y)
            LVector3( 0,   0,   2*s),  # 12 (+Z)
            LVector3( 0,   0,  -2*s)   # 13 (-Z)
        ]

        # 12 rhombic faces
        # Each face has 2 cube vertices and 2 octahedron tips
        # Vertices ordered counter-clockwise when viewed from outside
        face_indices = [
            # Top faces (involving +Y tip, vertex 10)
            (10, 0, 8, 1),   # top-right
            (10, 1, 13, 5),  # top-back
            (10, 5, 9, 4),   # top-left
            (10, 4, 12, 0),  # top-front
            
            # Bottom faces (involving -Y tip, vertex 11)
            (11, 2, 8, 3),   # bottom-right
            (11, 3, 13, 7),  # bottom-back
            (11, 7, 9, 6),   # bottom-left
            (11, 6, 12, 2),  # bottom-front
            
            # Side faces (connecting +Z and -Z tips)
            (12, 0, 10, 4),  # front-top (reordered for consistency)
            (12, 6, 11, 2),  # front-bottom (reordered for consistency)
            (13, 1, 10, 5),  # back-top (reordered for consistency)
            (13, 7, 11, 3),  # back-bottom (reordered for consistency)
        ]

        gformat = GeomVertexFormat.getV3n3()
        vdata = GeomVertexData('rhombic', gformat, Geom.UHStatic)
        vertex_writer = GeomVertexWriter(vdata, 'vertex')
        normal_writer = GeomVertexWriter(vdata, 'normal')
        tris = GeomTriangles(Geom.UHStatic)

        world_pos = LVector3(x, y, z)

        for face in face_indices:
            start = vdata.getNumRows()
            
            # Get the 4 corner points of this rhombus
            points = [v[face[0]], v[face[1]], v[face[2]], v[face[3]]]

            # Calculate face normal (right-hand rule)
            edge1 = points[1] - points[0]
            edge2 = points[2] - points[0]
            face_normal = edge1.cross(edge2)
            face_normal.normalize()

            # Write vertices and normals
            for point in points:
                vertex_writer.addData3(point + world_pos)
                normal_writer.addData3(face_normal)

            # Create 2 triangles from the 4-vertex rhombus
            tris.addVertices(start, start + 1, start + 2)
            tris.addVertices(start, start + 2, start + 3)
       
        geom = Geom(vdata)
        geom.addPrimitive(tris)
        node = GeomNode('rhombic_cell_node')
        node.addGeom(geom)
        return render.attachNewNode(node)


    def generate_rhombic_dodecahedron_old(self, x, y, z, total_width=1.0):
        """
        Generate a rhombic dodecahedron with correct topology.
        
        A rhombic dodecahedron has:
        - 14 vertices (8 from cube + 6 from octahedron)
        - 12 rhombic faces
        - 24 edges
        
        Each rhombic face connects 2 cube vertices and 2 octahedron tips.
        """
        s = total_width / 4.0

        # 14 vertices
        v = [
            # Inner cube vertices (0-7)
            LVector3( s,  s,  s),  # 0
            LVector3( s,  s, -s),  # 1
            LVector3( s, -s,  s),  # 2
            LVector3( s, -s, -s),  # 3
            LVector3(-s,  s,  s),  # 4
            LVector3(-s,  s, -s),  # 5
            LVector3(-s, -s,  s),  # 6
            LVector3(-s, -s, -s),  # 7
            # Outer octahedron tips (8-13)
            LVector3( 2*s,  0,   0),   # 8  (+X)
            LVector3(-2*s,  0,   0),   # 9  (-X)
            LVector3( 0,   2*s,  0),   # 10 (+Y)
            LVector3( 0,  -2*s,  0),   # 11 (-Y)
            LVector3( 0,   0,   2*s),  # 12 (+Z)
            LVector3( 0,   0,  -2*s)   # 13 (-Z)
        ]

        # 12 rhombic faces
        # Each face has 2 cube vertices and 2 octahedron tips
        # Format: (tip1, cube_v1, tip2, cube_v2) going counter-clockwise from outside
        face_indices = [
            # Faces connecting +X and +Y tips
            (10, 0, 8, 1),   # top-right-front
            (10, 4, 9, 5),   # top-left-back
            
            # Faces connecting +X and -Y tips  
            (8, 2, 11, 3),   # right-bottom-front
            (9, 6, 11, 7),   # left-bottom-back
            
            # Faces connecting +X and +Z tips
            (12, 0, 8, 2),   # front-right-top
            (12, 4, 9, 6),   # front-left-bottom
            
            # Faces connecting +X and -Z tips
            (8, 1, 13, 3),   # back-right-top
            (9, 5, 13, 7),   # back-left-bottom
            
            # Faces connecting +Y and +Z tips
            (10, 0, 12, 4),  # top-front
            
            # Faces connecting +Y and -Z tips
            (10, 1, 13, 5),  # top-back
            
            # Faces connecting -Y and +Z tips
            (11, 2, 12, 6),  # bottom-front
            
            # Faces connecting -Y and -Z tips
            (11, 3, 13, 7),  # bottom-back
        ]

        gformat = GeomVertexFormat.getV3n3()
        vdata = GeomVertexData('rhombic', gformat, Geom.UHStatic)
        vertex_writer = GeomVertexWriter(vdata, 'vertex')
        normal_writer = GeomVertexWriter(vdata, 'normal')
        tris = GeomTriangles(Geom.UHStatic)

        world_pos = LVector3(x, y, z)

        for face in face_indices:
            start = vdata.getNumRows()
            
            # Get the 4 corner points of this rhombus
            points = [v[face[0]], v[face[1]], v[face[2]], v[face[3]]]

            # Calculate face normal (right-hand rule)
            edge1 = points[1] - points[0]
            edge2 = points[2] - points[0]
            face_normal = edge1.cross(edge2)
            face_normal.normalize()

            # Write vertices and normals
            for point in points:
                vertex_writer.addData3(point + world_pos)
                normal_writer.addData3(face_normal)

            # Create 2 triangles from the 4-vertex rhombus
            tris.addVertices(start, start + 1, start + 2)
            tris.addVertices(start, start + 2, start + 3)
       
        geom = Geom(vdata)
        geom.addPrimitive(tris)
        node = GeomNode('rhombic_cell_node')
        node.addGeom(geom)
        return render.attachNewNode(node)

    def generate_dodecahedron(self, size):
        phi = (1 + math.sqrt(5)) / 2
        a, b = size, size / phi

        vertices = [
            LVector3( a,  a,  a), LVector3( a,  a, -a), LVector3( a, -a,  a), LVector3( a, -a, -a),
            LVector3(-a,  a,  a), LVector3(-a,  a, -a), LVector3(-a, -a,  a), LVector3(-a, -a, -a),
            LVector3( 0,  b,  phi*a), LVector3( 0,  b, -phi*a), LVector3( 0, -b,  phi*a), LVector3( 0, -b, -phi*a),
            LVector3( b,  phi*a,  0), LVector3( b, -phi*a,  0), LVector3(-b,  phi*a,  0), LVector3(-b, -phi*a,  0),
            LVector3( phi*a,  0,  b), LVector3( phi*a,  0, -b), LVector3(-phi*a,  0,  b), LVector3(-phi*a,  0, -b)
        ]

        # 12 Pentagonal faces defined by vertex indices
        faces = [
            [0, 12, 14, 4, 8], [0, 8, 10, 2, 16], [0, 16, 17, 1, 12],
            [4, 14, 15, 6, 18], [4, 18, 10, 8, 0], [1, 9, 11, 3, 17],
            [2, 13, 15, 6, 10], [2, 10, 18, 6, 13], [3, 11, 7, 15, 13],
            [3, 13, 2, 16, 17], [3, 17, 1, 9, 11], [19, 5, 14, 12, 1] # indices vary by orientation
        ]

        format = GeomVertexFormat.getV3n3() # Position and Normal
        vdata = GeomVertexData('dodeca', format, Geom.UHStatic)
        
        vertex = GeomVertexWriter(vdata, 'vertex')
        normal = GeomVertexWriter(vdata, 'normal')
        tris = GeomTriangles(Geom.UHStatic)

        for indices in faces:
            start_idx = vdata.getNumRows()
            # Normal calculation for lighting
            v0, v1, v2 = vertices[indices[0]], vertices[indices[1]], vertices[indices[2]]
            face_normal = (v1 - v0).cross(v2 - v0)
            face_normal.normalize()

            for idx in indices:
                vertex.addData3(vertices[idx])
                normal.addData3(face_normal)
            
            # Triangulate pentagon (fan method)
            tris.addVertices(start_idx, start_idx + 1, start_idx + 2)
            tris.addVertices(start_idx, start_idx + 2, start_idx + 3)
            tris.addVertices(start_idx, start_idx + 3, start_idx + 4)

        geom = Geom(vdata)
        geom.addPrimitive(tris)
        node = GeomNode('cell_node')
        node.addGeom(geom)
        return render.attachNewNode(node)
