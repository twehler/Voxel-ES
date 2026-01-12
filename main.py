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
from world_geometry import *
from cell import *



""" To Do:

implement textures

implement basic entity class: 
multi-dimensional numpy array, which stores data about: cell-index, cell type, position, rotation, linkage

implement voxel-surface-movement 
--> all blocks should only move by "sliding" on another block

for every cell there is a list of "mandatory cells", on which a cell depends
--> for example, all cells depend on the controller cell
if mandatory cells are not present, the cell dies

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



class VoxelWorld(ShowBase):
    def __init__(self):
        super().__init__()   
        self.setFrameRateMeter(True)
        
        # Setting up controls
        logger_main.info("Setting up controls...")
        self.capture_mouse()
        self.setup_controls()
        self.setup_camera(5, 5, 30)
        self.camera_move_speed = 15
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

        # Importing and setting up texture atlas
        logger_main.info("Setting up texture-atlas")
        base.texture_atlas = self.loader.loadTexture("Textures/texture_atlas.png")
        # Ensuring that textures don't look blurry
        base.texture_atlas.setAnisotropicDegree(0)
        base.texture_atlas.setMinfilter(Texture.FT_nearest)
        base.texture_atlas.setMagfilter(Texture.FT_nearest)
        
        base.texture_atlas.setWrapU(Texture.WM_clamp)
        base.texture_atlas.setWrapV(Texture.WM_clamp)

        # Generating world
        logger_main.debug("------------- Beginning World Generation ----------------")
        
        # Generating textures based on coordinates in the texture atlas
        stone_texture = (0, 4)
        grass1_texture = (1, 4)
        grass2_texture = (2, 4)
        grass3_texture = (3, 4)
        grass4_texture = (4, 4)

        # Generating Voxel objects
        voxel_stone = Voxel(stone_texture)
        voxel_grass1 = Voxel(grass1_texture)
        voxel_grass2 = Voxel(grass2_texture)
        voxel_grass3 = Voxel(grass3_texture)
        voxel_grass4 = Voxel(grass4_texture)


        self.generate_world(100, 100, 5, voxel_grass1)       
        
        logger_main.info("------------- World Generation Complete -----------------")
        
        print(self.render.analyze())  
 
        self.taskMgr.add(self.update_camera, "update_camera")
        logger_main.info("Done.")


        print("---------------- Generating Entities -----------------")

        base_cell1 = BaseCell("#ffb226", pos=(5,5,11), geometry_type="rhombic_dodecahedron", hpr = (20, 9, 30), width = 1.0)   
        cell2 = Cell("#26aaff", pos=(5,5.25,11.25), geometry_type="rhombic_dodecahedron", hpr = (0, 0, 0), width = 1.0)
        cell3 = Cell("#26aaff", pos=(5,5.5,11.5), geometry_type="rhombic_dodecahedron", hpr = (0, 0, 0), width = 1.0)
        cell4 = Cell("#269cff", pos=(5,5.75,11.75), geometry_type="rhombic_dodecahedron", hpr = (0, 0, 0), width = 1.0)
        cell5 = Cell("#269cff", pos=(5,6,12), geometry_type="rhombic_dodecahedron", hpr = (0, 0, 0), width = 1.0)

        base_cell1.render_cell()
        cell2.render_cell()

        # generating a filament-like structure
        base_cell2 = BaseCell("#ffb226", pos=(10,10,11), geometry_type="rhombic_dodecahedron", hpr = (0,0,0), width = 1.0)
        x_base = 10
        y_base = 10
        z_base = 11
        base_cell2.render_cell()    
        for i in range(20):
            x_base += 0.25
            y_base += 0.25
            z_base += 0.25
            cell = Cell("#269cff", pos=(x_base,y_base,z_base), geometry_type="rhombic_dodecahedron", hpr = (0, 0, 0), width = 1.0)
            cell.render_cell()


        # 1. Define orientation and starting point
        target_hpr = LVector3(20, 9, 30)
        current_pos = LVector3(20, 20, 50)
        step_dist = 0.5  # How far each cell is from the previous one

        # 2. Calculate the direction vector using a dummy node
        dummy = render.attachNewNode("dummy")
        dummy.setHpr(target_hpr)
        # In Panda3D, 'forward' is the Y-axis (0, 1, 0)
        direction = render.getRelativeVector(dummy, LVector3(0, 1, 0))
        dummy.removeNode() # Clean up

        # 3. Generate the filament
        base_cell3 = BaseCell("#ffb226", pos=current_pos, hpr=target_hpr, width=1.0)
        base_cell3.render_cell()

        for i in range(20):
            # Move the current position forward by the direction vector * distance
            current_pos += direction * step_dist
            
            cell = Cell("#269cff", pos=current_pos, hpr=target_hpr, width=1.0)
            cell.render_cell()



    def generate_world(self, x, y, max_height, voxel_object):
        voxel_mesh = VoxelMesh(voxel_object)

        # generating voxels inside a mesh
        terrain_node = voxel_mesh.generate_base_terrain(x, y, max_height) 
        terrain_np = self.render.attachNewNode(terrain_node)
        terrain_np.setPos(0,0,0)
        terrain_np.setTexture(base.texture_atlas)

            
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

        self.accept("wheel_up", self.increase_camera_speed)    
        self.accept("wheel_down", self.decrease_camera_speed) 
        
        # update which keyboard keys are being pressed by the user
        # keys are keyboard keys and values are "True" or "False"
    def update_key_map(self, key, value):
        self.key_map[key] = value
    
    def increase_camera_speed(self):
        self.camera_move_speed = self.camera_move_speed * 1.5
   
    def decrease_camera_speed(self):
        self.camera_move_speed = self.camera_move_speed / 1.5
        
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
            
            ########## Camera rotation #########

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
        


            ################## Camera movement ##################
            
            # Using Quarternions (special 3D-Vectors) to move relative to camera orientation
            quat = self.camera.getQuat(self.render)
            forward = quat.getForward() # local Y
            right = quat.getRight()     # local X
            up = LVector3(0,0,1) # up and down is always moving directly in z axis         
            
            # flattening horizontal vectors, so that movement doesn't occur up and down if the camera looks up or down
            forward.setZ(0)
            forward.normalize()
            right.setZ(0)
            right.normalize()

            move_dir = LVector3(0, 0, 0) # In Panda3D, LVector3 is a normal, linear vector in 3 dimensions

            if self.key_map['forward']:  
                move_dir += forward
            if self.key_map['backward']: 
                move_dir -= forward
            if self.key_map['left']:     
                move_dir -= right
            if self.key_map['right']:    
                move_dir += right
            if self.key_map['up']:       
                move_dir += up
            if self.key_map['down']:     
                move_dir -= up

            move_dir.normalize() # Prevents moving faster diagonally
            
            # Translate the movement relative to where the camera is looking
            # setPos(reference_node, movement_vector), performs matrix multiplication in C++ backend
            # setPos(x, y, z) would also be possible (method overloading feature from Panda3D)
            self.camera.setPos(self.camera.getPos() + move_dir * self.camera_move_speed * dt)

        return task.cont  


app = VoxelWorld()
app.run()
