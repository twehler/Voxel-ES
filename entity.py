import math

from random import choice
import panda3d
from panda3d.core import (
    GeomVertexFormat, GeomVertexData, Geom,
    GeomVertexWriter, GeomTriangles, GeomNode,
    LVector3, LColor, NodePath
)

from common import *
from cell import *

logging_setup()
logger_entity = logging.getLogger(__name__)



class Entity:

    def __init__(self, entity_pos, entity_hpr):

        self.entity_pos = entity_pos
        self.entity_hpr = entity_hpr
        self.speed = 1.0

        # generating base-cell and cell-index for the entity
        self.base_cell = BaseCell(pos=self.entity_pos, hpr = self.entity_hpr)     
        self.cells = [self.base_cell]

        # execute a function every second
        base.taskMgr.doMethodLater(1.0, self.update_entity, "add_cell")
            
        for obj in self.cells:
            obj.render_cell()

    def update_entity(self, task):
        self.add_cell(self.base_cell, "EnergyStorage")
        return task.cont

    def add_cell(self, contact_cell, new_cell_type, specific_location = None):
        # attach a new cell to a contact cell
        # if no specific position is designated, the function will take free neighbor location randomly
       
        # check if free_neighbor_positions is empty
        if contact_cell.free_neighbor_positions == True:
   

            if specific_location != None:
                current_pos = specific_location
            
            # if no specific location is given, choose a random position around the cell
            # remove that position from free_neighbor_positions
            else:
                current_pos = random.choice(contact_cell.free_neighbor_positions)
                del free_neighbor_positions[current_pos]

            match new_cell_type:
                case "Bone":
                    new_cell = BoneCell(pos = (contact_cell.pos + current_pos), hpr = (0,0,0))
                case "EnergyStorage":
                    new_cell = EnergyStorageCell(pos = (contact_cell.pos + current_pos), hpr = (0,0,0))
                case "Excretion":
                    new_cell = ExcretionCell(pos = (contact_cell.pos + current_pos), hpr = (0,0,0))
                case "Glider":
                    new_cell = GliderCell(pos = (contact_cell.pos + current_pos), hpr = (0,0,0))
                case "Fin":
                    new_cell = FinCell(pos = (contact_cell.pos + current_pos), hpr = (0,0,0))
                case "FoodIngestionCell":
                    new_cell = FoodIngestionCell(pos = (contact_cell.pos + current_pos), hpr = (0,0,0))
                case "Gastric":
                    new_cell = GastricCell(pos = (contact_cell.pos + current_pos), hpr = (0,0,0))
                case "Hard":
                    new_cell = HardCell(pos = (contact_cell.pos + current_pos), hpr = (0,0,0))
                case "Muscle":
                    new_cell = MuscleCell(pos = (contact_cell.pos + current_pos), hpr = (0,0,0))
                case "Neural":
                    new_cell = NeuralCell(pos = (contact_cell.pos + current_pos), hpr = (0,0,0))
                case "Optic":
                    new_cell = OpticCell(pos = (contact_cell.pos + current_pos), hpr = (0,0,0))
                case "Photosynthetic":
                    new_cell = PhotosyntheticCell(pos = (contact_cell.pos + current_pos), hpr = (0,0,0))
                case "PlantLeafCell":
                    new_cell = PlantLeafCell(pos = (contact_cell.pos + current_pos), hpr = (0,0,0))
                case "PlantRoot":
                    new_cell = PlantRootCell(pos = (contact_cell.pos + current_pos), hpr = (0,0,0))
                case "PlantNode":
                    new_cell = PlantNodeCell(pos = (contact_cell.pos + current_pos), hpr = (0,0,0))

        else:
            pass

    def remove_cell(self, cell_index):
        pass


    def move_entity(self, move_hpr, speed):
        # move the base cell and all other cells which are attached to it
        pass

