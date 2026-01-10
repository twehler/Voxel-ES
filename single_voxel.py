   
class Voxel:

    def __init__(self, texture_coords = (4, 0)):
    
        self.texture_coords = texture_coords

    
    # generates a single Voxel with its own geometry node
    def generate_single(self):

        # providing a stencil for geometry inside the GPU
        geom_format = GeomVertexFormat.getV3n3t4()
        vdata = GeomVertexData('voxel', geom_format, Geom.UHStatic)
        vertex = GeomVertexWriter(vdata, 'vertex')
        normal = GeomVertexWriter(vdata, 'normal')      
        tris = GeomTriangles(Geom.UHStatic)

        # inner function to add all 6 faces of the cube, each with 4 points on space and a normal 
        # the finished cube will have 24 overlapping vertices to ensure proper texture behaviour
        def add_face(p1, p2, p3, p4, norm):
            start = vdata.getNumRows()
            for p in [p1, p2, p3, p4]:
                vertex.addData3(p)
                normal.addData3(norm)     

            tris.addVertices(start, start + 1, start + 2)
            tris.addVertices(start, start + 2, start + 3)

        # Define cube faces
        # Bottom (Z=0) - Looking from below
        add_face((0,0,0), (0,1,0), (1,1,0), (1,0,0), LVector3(0,0,-1))
        # Top (Z=1) - Looking from above
        add_face((0,0,1), (1,0,1), (1,1,1), (0,1,1), LVector3(0,0,1))
        # Front (Y=0) - Looking from -Y
        add_face((0,0,0), (1,0,0), (1,0,1), (0,0,1), LVector3(0,-1,0))
        # Back (Y=1) - Looking from +Y
        add_face((1,1,0), (0,1,0), (0,1,1), (1,1,1), LVector3(0,1,0))
        # Left (X=0) - Looking from -X
        add_face((0,1,0), (0,0,0), (0,0,1), (0,1,1), LVector3(-1,0,0))
        # Right (X=1) - Looking from +X
        add_face((1,0,0), (1,1,0), (1,1,1), (1,0,1), LVector3(1,0,0))          

        geom = Geom(vdata)
        geom.addPrimitive(tris)
        node = GeomNode('voxel-node')
        node.addGeom(geom)
        return node
