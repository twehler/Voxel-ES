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



""" To Do:
Fix bug: Camera Stuttering
Join multiple cubes into a 3D-plane
Join triangles of multiple blocks into a single square with two triangles 


"""




# Get the directory of the current script, ensure that the script is run from there
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir) # Change the working directory to the script's directory
print("Working Directory:", os.getcwd())


# Function for global root logger setup
def logging_setup():
    logging.basicConfig(
        filename="voxel_evolution.log",
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


class Voxel:
    def __init__(self, hex_color="#ffffff"):
        self.color = self.hex_to_rgba(hex_color)

    def hex_to_rgba(self, hex_str):        
        hex_str = hex_str.lstrip('#')
        r, g, b = tuple(int(hex_str[i:i+2], 16) / 255.0 for i in (0, 2, 4))
        return LColor(r, g, b, 1.0)

    def generate(self):
        format = GeomVertexFormat.getV3n3c4()
        vdata = GeomVertexData('voxel', format, Geom.UHStatic)

        vertex = GeomVertexWriter(vdata, 'vertex')
        normal = GeomVertexWriter(vdata, 'normal')
        color = GeomVertexWriter(vdata, 'color')
        tris = GeomTriangles(Geom.UHStatic)

        # inner function to add all 6 faces of the cube, each with 4 points
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





class VoxelWorld(ShowBase):
    def __init__(self):
        super().__init__()   
        
        # Setting up controls
        logger_main.info("Setting up controls...")
        
        self.capture_mouse()
        self.setup_controls()
        self.setup_camera()
        self.setup_skybox("cbt-panda3d-minecraft-main/skybox/skybox.egg")
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

        # Creating voxels (x, y, z)
        logger_main.info("Generating stationary voxels...")
        self.create_voxel(position=(0, 10, 0), color="#3498db")
        self.create_voxel(position=(3, 10, 0), color="#3498db")
        self.create_voxel(position=(1, 10, 0), color="#e74c3c")
        self.create_voxel(position=(0, 11, 1), color="#2ecc71")     
        
        self.taskMgr.add(self.update_camera, "update")
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
        self.accept("lshift-up", self.update_key_map, ["up", False])
        
        
        
        
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
        
    def setup_camera(self):
        self.disableMouse()     # disables standart mouse navigation
        self.camera.setPos(5, 5, 5)
        #self.camera.lookAt(0, 5, 0)
        
    def setup_skybox(self, skybox_model):
        skybox = self.loader.loadModel(skybox_model)
        skybox.setScale(500)
        skybox.setBin("background", 1)
        skybox.setDepthWrite(0)
        skybox.setLightOff()
        skybox.reparentTo(self.render)

    def create_voxel(self, position, color):
        voxel_factory = Voxel(color)
        voxel_geom = voxel_factory.generate()
        
        # generating node path & rendering
        voxel_np = self.render.attachNewNode(voxel_geom)
        voxel_np.setPos(position)
        
        
        
        
        
    # function which updates the camera position, based on the movements of the mouse
    def update_camera(self, task):
        dt = globalClock.getDt() # delta time        
        md = self.win.getPointer(0) # get mouse cursor position relative to the game window
        
        playerMoveSpeed = 10

        x_movement = 0
        y_movement = 0
        z_movement = 0

        if self.key_map['forward']:
            x_movement -= dt * playerMoveSpeed * sin(degToRad(self.camera.getH()))
            y_movement += dt * playerMoveSpeed * cos(degToRad(self.camera.getH()))
        if self.key_map['backward']:
            x_movement += dt * playerMoveSpeed * sin(degToRad(self.camera.getH()))
            y_movement -= dt * playerMoveSpeed * cos(degToRad(self.camera.getH()))
        if self.key_map['left']:
            x_movement -= dt * playerMoveSpeed * cos(degToRad(self.camera.getH()))
            y_movement -= dt * playerMoveSpeed * sin(degToRad(self.camera.getH()))
        if self.key_map['right']:
            x_movement += dt * playerMoveSpeed * cos(degToRad(self.camera.getH()))
            y_movement += dt * playerMoveSpeed * sin(degToRad(self.camera.getH()))
        if self.key_map['up']:
            z_movement += dt * playerMoveSpeed
        if self.key_map['down']:
            z_movement -= dt * playerMoveSpeed

        self.camera.setPos(
            self.camera.getX() + x_movement,
            self.camera.getY() + y_movement,
            self.camera.getZ() + z_movement,
        )
        
        if self.camera_swing_activated == True:
            mouseX = md.getX()
            mouseY = md.getY()
            
            mouse_change_X = mouseX - self.last_mouseX
            mouse_change_Y = mouseY - self.last_mouseY
            
            current_H = self.camera.getH()
            current_P = self.camera.getP()
            
            self.cameraSwingFactor = 8
            
            self.camera.setHpr(
                    current_H - mouse_change_X * dt * self.cameraSwingFactor,
                    min(90, max(-90, current_P - mouse_change_Y * dt * self.cameraSwingFactor)),
                    0
                )
            
            self.last_mouseX = mouseX
            self.last_mouseY = mouseY
            
        return task.cont
        

app = VoxelWorld()
app.run()