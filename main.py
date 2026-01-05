import logging
import os
from math import cos, sin, pi

import panda3d
from direct.showbase.ShowBase import ShowBase
from panda3d.core import (
    GeomVertexFormat, GeomVertexData, Geom, 
    GeomVertexWriter, GeomTriangles, GeomNode, 
    LVector3, LColor, DirectionalLight, AmbientLight, 
    WindowProperties, ClockObject, Loader
)

from panda3d.core import loadPrcFileData

# Force V-Sync to match your monitor's refresh rate
loadPrcFileData("", "sync-video #t")
# Optional: Cap the frame rate at 60 to see if it stabilizes
loadPrcFileData("", "framebuffer-vertical-sync #t")
loadPrcFileData("", "clock-mode limited")
loadPrcFileData("", "clock-frame-rate 60")



""" DONE:

Don't render faces between blocks

"""





""" To Do:

implement greedy meshing
implement primitive landscape generation with noise


implement basic entity class: 
multi-dimensional numpy array, which stores data about: cell-index, cell type, position, rotation, linkage

implement voxel-surface-movement 
--> all blocks should only move by "sliding" on another block

expand voxel-class: 
there is a list of "mandatory neighbors", on which a voxel depends
--> for example, all voxels depend on the controller cell
if mandatory neighbors are not present, the cell dies

implement voxel: "ControllerCell"
implement voxel: "SliderCell"
implement voxel: "PhotosyntheticCell"
implement voxel: "GutCell"
implement voxel: "FoodSuckerCell"

implement method: remove_voxel
implement method: add_voxel

implement entity: "BasicTerrestrialHerbivore"
implement entity: "UnicellularAlgae"


"""




# Get the directory of the current script, ensure that the script is run from there
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir) # Change the working directory to the script's directory
print("Working Directory:", os.getcwd())


# Function for global root logger setup
def logging_setup():
    logging.basicConfig(
        filename="main.log",
        level = logging.DEBUG,
        format='%(asctime)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s'
        )
    
logging_setup()

logger_main = logging.getLogger(__name__)

logger_main.info("------------------------------------------------------")
logger_main.info("-------- Entering main simulation script -------------")
logger_main.info("------------------------------------------------------")


def degToRad(degrees):
    return degrees * (pi / 180.0)

def hex_to_rgba(hex_str):        
    hex_str = hex_str.lstrip('#')
    r, g, b = tuple(int(hex_str[i:i+2], 16) / 255.0 for i in (0, 2, 4))
    return LColor(r, g, b, 1.0)


class Voxel:

    def __init__(self, rgb_color="3dc53dff"):
        self.color = hex_to_rgba(rgb_color)
        self.position = None
        self.material = None

    
    # generates a single Voxel with its own geometry node
    def generate_single(self):

        # providing a stencil for geometry inside the GPU
        geom_format = GeomVertexFormat.getV3n3c4()
        vdata = GeomVertexData('voxel', geom_format, Geom.UHStatic)
        vertex = GeomVertexWriter(vdata, 'vertex')
        normal = GeomVertexWriter(vdata, 'normal')
        color = GeomVertexWriter(vdata, 'color')
        tris = GeomTriangles(Geom.UHStatic)

        # inner function to add all 6 faces of the cube, each with 4 points on space and a normal 
        # the finished cube will have 24 overlapping vertices to ensure proper texture behaviour
        def add_face(p1, p2, p3, p4, norm):
            start = vdata.getNumRows()
            for p in [p1, p2, p3, p4]:
                vertex.addData3(p)
                normal.addData3(norm)
                color.addData4(self.color)

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


    # creates a voxel which is part of a larger mesh
    # appends data to an existing list
    def generate_embedded(self, x, y, z, v_writer, n_writer, c_writer, tris, vdata, neighbor_map):
        
        # the neighbor-map should make it possible to render only the faces which are not between blocks
        # Local helper to add a face to the shared writers
        def add_face(p1, p2, p3, p4, norm):

            start = vdata.getNumRows() # counts the already existing vertices

            # generating vertices, normals and colors for a single voxel-face
            for p in [p1, p2, p3, p4]:
                # Apply the (x, y, z) offset here
                v_writer.addData3(p[0] + x, p[1] + y, p[2] + z)
                n_writer.addData3(norm)
                c_writer.addData4(self.color)
            tris.addVertices(start, start + 1, start + 2)
            tris.addVertices(start, start + 2, start + 3)




        # generating all 6 faces of the voxel at their target-position
        # but only if the faces are not between blocks

        # Bottom (z - 1)
        if (x, y, z - 1) not in neighbor_map:
            add_face((0,0,0), (0,1,0), (1,1,0), (1,0,0), LVector3(0,0,-1)) 

        # Top (z + 1)
        if (x, y, z + 1) not in neighbor_map:
            add_face((0,0,1), (1,0,1), (1,1,1), (0,1,1), LVector3(0,0,1))

        # Front (y - 1)
        if (x, y - 1, z) not in neighbor_map:
            add_face((0,0,0), (1,0,0), (1,0,1), (0,0,1), LVector3(0,-1,0))

        # Back (y + 1)
        if (x, y + 1, z) not in neighbor_map:
            add_face((1,1,0), (0,1,0), (0,1,1), (1,1,1), LVector3(0,1,0))
        
        # Left (x - 1)
        if (x - 1, y, z) not in neighbor_map:
            add_face((0,1,0), (0,0,0), (0,0,1), (0,1,1), LVector3(-1,0,0))

        # Right (x + 1)
        if (x + 1, y, z) not in neighbor_map:
            add_face((1,0,0), (1,1,0), (1,1,1), (1,0,1), LVector3(1,0,0))

        




# This is the object which holds joint voxels (for example a landscape) in an efficient way
class VoxelMesh:
    def __init__(self):
        self.format = GeomVertexFormat.getV3n3c4()
        self.vdata = GeomVertexData('map_data', self.format, Geom.UHStatic)

        # Create the writers that will be shared by all voxels
        self.vertex = GeomVertexWriter(self.vdata, 'vertex')
        self.normal = GeomVertexWriter(self.vdata, 'normal')
        self.color = GeomVertexWriter(self.vdata, 'color')
        self.tris = GeomTriangles(Geom.UHStatic)

    def generate_terrain(self, x_size, y_size, z_size, color_hex):
       
        # We use a dictionary where keys are (x, y, z) and values are the Voxel objects
        # This "neighbor-map" is used to not render faces that are between two voxels
        neighbor_map = {}
        

        logger_main.debug("Generating Neighbor-Map.")
        for x in range(x_size):
            for y in range(y_size):
                for z in range(z_size):
                    # For a flat 1000x1000 floor, z is always 0
                    pos = (x, y, z)
                    neighbor_map[pos] = Voxel(color_hex)
        logger_main.debug("Neighbor-map successfully generated.")

        # Now we loop through the map we just created
        
        DEBUG_voxel_counter = 0
        for pos, voxel_obj in neighbor_map.items():
            vx, vy, vz = pos

            # We pass 'neighbor_map' into the voxel so it can check its surroundings
            voxel_obj.generate_embedded(
                vx, vy, vz,
                self.vertex, self.normal, self.color,
                self.tris, self.vdata,
                neighbor_map
            )
            DEBUG_voxel_counter += 1
            logger_main.debug(f"Embedded voxel successfully generated: {DEBUG_voxel_counter}")

    
        # Create node 
        self.tris.closePrimitive()
        geom = Geom(self.vdata)
        geom.addPrimitive(self.tris)
        node = GeomNode('terrain_node')
        node.addGeom(geom)

        
        return node



class VoxelWorld(ShowBase):
    def __init__(self):
        super().__init__()   
        self.setFrameRateMeter(True)
        

        # Setting up controls
        logger_main.info("Setting up controls...")
        
        self.capture_mouse()
        self.setup_controls()
        self.setup_camera(5, 5, 20)
        self.setup_skybox("Skybox/skybox.egg")
        logger_main.info("Done.")
        # Setting up Lighting
        logger_main.info("Setting up lighting...")
        
        dlight = DirectionalLight('dlight')
        dlight.setColor((1, 1, 1, 1))
        dlnp = self.render.attachNewNode(dlight)
        dlnp.setHpr(45, -45, 0) # Hpr = heading, pitch, roll
        self.render.setLight(dlnp)
        alight = AmbientLight('alight')
        alight.setColor((0.3, 0.3, 0.3, 1))
        alnp = self.render.attachNewNode(alight)
        self.render.setLight(alnp)
        logger_main.info("Done.")

        # Creating landscape
        logger_main.debug("Calling function: call_generate_terrain") 
        self.call_generate_terrain(100, 100, 5)       
        logger_main.info("------------- World Generation Complete -----------------")
        
        print(self.render.analyze())  
 
        self.taskMgr.add(self.update_camera, "update_camera")
        logger_main.info("Done.")
        
        
        
    def setup_controls(self):
        
        self.key_map = {
            "forward":False,
            "backward":False,
            "left":False,
            "right":False,
            "up":False,
            "down":False
        }
        
        self.accept('escape', self.release_mouse)
        self.accept('mouse1', self.capture_mouse)    
        
        # -up means that a key is released again
        self.accept("w", self.update_key_map, ["forward", True])
        self.accept("w-up", self.update_key_map, ["forward", False])
        self.accept("a", self.update_key_map, ["left", True])
        self.accept("a-up", self.update_key_map, ["left", False])
        self.accept("s", self.update_key_map, ["backward", True])
        self.accept("s-up", self.update_key_map, ["backward", False])
        self.accept("d", self.update_key_map, ["right", True])
        self.accept("d-up", self.update_key_map, ["right", False])
        self.accept("space", self.update_key_map, ["up", True])
        self.accept("space-up", self.update_key_map, ["up", False])
        self.accept("lshift", self.update_key_map, ["down", True])
        self.accept("lshift-up", self.update_key_map, ["down", False])
        
        
        
        
    # update which keyboard keys are being pressed by the user
    # keys are keyboard keys and values are "True" or "False"
    def update_key_map(self, key, value):
        self.key_map[key] = value
        
        
        
    def capture_mouse(self):
        self.camera_swing_activated = True
        
        md = self.win.getPointer(0)   # get mouse cursor position relative to the game window
        self.last_mouseX = md.getX()
        self.last_mouseY = md.getY()     
        
        
        properties = WindowProperties()
        properties.setCursorHidden(True) #cursor will not be shown
        properties.setMouseMode(WindowProperties.M_relative) #cursor will be held in the middle of the image
        self.win.requestProperties(properties)

    def release_mouse(self):
        self.camera_swing_activated = False
        properties = WindowProperties()
        properties.setCursorHidden(False) #cursor will not be shown
        properties.setMouseMode(WindowProperties.M_absolute) #cursor will be held in the middle of the image
        self.win.requestProperties(properties)
        
    def setup_camera(self, x, y, z):
        self.disableMouse()     # disables standart mouse navigation
        self.camera.setPos(x, y, z)
        self.camera.lookAt(0, 5, 0)
        
    def setup_skybox(self, skybox_model):
        skybox = self.loader.loadModel(skybox_model)
        skybox.setScale(500)
        skybox.setBin("background", 1)
        skybox.setDepthWrite(0)
        skybox.setLightOff()
        skybox.reparentTo(self.render)      
        
        
    # function which updates the camera position, based on the movements of the mouse
   
    def update_camera(self, task):
        dt = globalClock.getDt()
        
        if self.camera_swing_activated:

            md = self.win.getPointer(0) #Mouse-Data object
            win_props = self.win.getProperties()
            
            center_x = win_props.getXSize() // 2
            center_y = win_props.getYSize() // 2
            mouse_change_X = md.getX() - center_x
            mouse_change_Y = md.getY() - center_y
            
            # Reset pointer to avoid double-reading the same delta
            self.win.movePointer(0, center_x, center_y)
                
            sensitivity = 5.0  # Mouse sensitivity 
            
            # H / Heading = Rotation around vertical axis
            # P / Pitch = Tilting up and down
            new_H = self.camera.getH() - (mouse_change_X * sensitivity * dt)
            new_P = self.camera.getP() - (mouse_change_Y * sensitivity * dt)
            
            self.camera.setHpr(new_H, min(90, max(-90, new_P)), 0)

            # Using a vector-based approach for movement
            # LVector is a normal, linear vector object in 3D space
            move_vec = LVector3(0, 0, 0) 
            playerMoveSpeed = 10.0


            # in Panda3D, y goes forward/backward and x goes to the side from camera perspective
            # z goes up and down

            if self.key_map['forward']:  
                move_vec.setY(1)
            if self.key_map['backward']: 
                move_vec.setY(-1)
            if self.key_map['left']:     
                move_vec.setX(-1)
            if self.key_map['right']:    
                move_vec.setX(1)
            if self.key_map['up']:       
                move_vec.setZ(1)
            if self.key_map['down']:     
                move_vec.setZ(-1)

            move_vec.normalize() # Prevents moving faster diagonally
            
            # Translate the movement relative to where the camera is looking
            # setPos(reference_node, movement_vector), performs matrix multiplication in C++ backend
            # setPos(x, y, z) would also be possible (method overloading feature from Panda3D)
            self.camera.setPos(self.camera, move_vec * playerMoveSpeed * dt)

        return task.cont  

    
    def call_generate_terrain(self, x, y, z):
        voxel_mesh = VoxelMesh()

        # generating voxels inside a mesh
        terrain_node = voxel_mesh.generate_terrain(x, y, z, "3dc53dff")
        terrain_np = self.render.attachNewNode(terrain_node)
        terrain_np.setPos(0,0,0)

    
app = VoxelWorld()
app.run()
