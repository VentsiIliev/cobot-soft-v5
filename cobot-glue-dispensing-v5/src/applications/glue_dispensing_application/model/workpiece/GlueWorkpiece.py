import numpy as np

from applications.glue_dispensing_application.model.workpiece.GlueWorkpieceField import GlueWorkpieceField
from core.model.workpiece.Workpiece import BaseWorkpiece


from modules.shared.core.interfaces.JsonSerializable import JsonSerializable
from modules.shared.tools.enums.ToolID import ToolID
from modules.shared.tools.enums.Program import Program
from modules.shared.tools.enums.Gripper import Gripper



class GlueWorkpiece(BaseWorkpiece, JsonSerializable):
    """
        A class representing a workpieces in a glue dispensing application, including its properties such as ID,
        name, description, tool, gripper, glue type, program, material, contour, offset, height, nozzles,
        contour area, and spray pattern.

        Inherits from BaseWorkpiece and JsonSerializable for basic workpieces functionality and serialization support.
        """
    def __init__(self, workpieceId, name, description, toolID, gripperID, glueType, program, material, contour, offset,
                 height, nozzles, contourArea, glueQty, sprayWidth, pickupPoint, sprayPattern=None):
        """
              Initializes a Workpiece object with specified parameters.

              Args:
                  workpieceId (int): The unique identifier for the workpieces.
                  name (str): The name of the workpieces.
                  description (str): A description of the workpieces.
                  toolID (ToolID): The tool ID associated with the workpieces.
                  gripperID (Gripper): The gripper ID associated with the workpieces.
                  glueType (str): The type of glue used in the workpieces (e.g., "Type A", "Custom Glue X").
                  program (Program): The program associated with the workpieces.
                  material (str): The material of the workpieces.
                  contour (list of np.ndarray): The contour points of the workpieces.
                  offset (float): The offset of the workpieces.
                  height (float): The height of the workpieces.
                  nozzles (list): The list of nozzles associated with the workpieces.
                  contourArea (float): The area of the contour.
                  sprayPattern (optional, list): The spray pattern used for the workpieces. Defaults to an empty list if None.

              """
        super().__init__(workpieceId, contour)
        if sprayPattern is None:
            sprayPattern = []
        self.workpieceId = workpieceId
        self.name = name
        self.description = description
        self.toolID = toolID
        self.gripperID = gripperID
        self.glueType = glueType
        self.program = program
        self.material = material
        self.contour = contour  # This should be a list of nd arrays
        self.offset = offset
        self.height = height
        self.sprayPattern = sprayPattern
        self.contourArea = contourArea
        self.nozzles = nozzles
        self.glueQty = glueQty
        self.sprayWidth = sprayWidth
        self.pickupPoint = pickupPoint  # Placeholder for pickup point

    def __str__(self):
        return (f"Workpiece(ID: {self.workpieceId}, "
                f"Name: {self.name}, "
                f"Description: {self.description}, "
                f"Tool: {self.toolID.value if hasattr(self.toolID, 'value') else self.toolID}, "
                f"Gripper: {self.gripperID.value if hasattr(self.gripperID, 'value') else self.gripperID}, "
                f"Material: {self.material}, "
                f"Height: {self.height}, "
                f"ContourArea: {self.contourArea}), "
                f"PickupPoint: {self.pickupPoint})")

    def get_spray_pattern_contours(self):
        """
        Return list of spray pattern contour entries.
        Each entry is a dict: {"contour": np.ndarray, "settings": dict}
        """
        contours = []
        for entry in self.sprayPattern.get("Contour", []):
            contour_points = np.array(entry.get("contour", []), dtype=np.float32).reshape(-1, 2)
            contours.append({
                "contour": contour_points,
                "settings": entry.get("settings", {})
            })
        return contours


    def get_spray_pattern_fills(self):
        """
        Return list of spray pattern fill entries.
        Each entry is a dict: {"contou  r": np.ndarray, "settings": dict}
        """
        fills = []
        for entry in self.sprayPattern.get("Fill", []):
            contour_points = np.array(entry.get("contour", []), dtype=np.float32).reshape(-1, 2)
            fills.append({
                "contour": contour_points,
                "settings": entry.get("settings", {})
            })
        return fills

    def set_main_contour(self, contour):
      self.contour["contour"] = contour



    def get_main_contour(self):
        """
        Return the main contour without settings.
        Handles both dict and direct format of self.contour.
        Returns numpy array in proper format for nesting operations.
        """

        if isinstance(self.contour, dict) and "contour" in self.contour:
            # Handle dict format: {"contour": points, "settings": {...}}
            contour_data = self.contour["contour"]
        else:
            # Handle direct format: contour data directly
            contour_data = self.contour

        # Convert to numpy array format expected by nesting (N, 1, 2)
        if isinstance(contour_data, np.ndarray):
            if len(contour_data.shape) == 3 and contour_data.shape[1] == 1:
                # Already in correct format (N, 1, 2)
                return contour_data
            elif len(contour_data.shape) == 2:
                # Convert from (N, 2) to (N, 1, 2)
                return contour_data.reshape(-1, 1, 2)
            else:
                # Flatten and reshape
                return contour_data.reshape(-1, 2).reshape(-1, 1, 2)
        else:
            # Handle list format - convert to numpy array
            flat_points = []
            for point in contour_data:
                if isinstance(point, (list, tuple, np.ndarray)):
                    # Handle nested structures like [[[x, y]]] or [[x, y]]
                    while isinstance(point, (list, tuple, np.ndarray)) and len(point) == 1:
                        point = point[0]
                    if len(point) >= 2:
                        # Recursively flatten nested coordinates
                        x, y = point[0], point[1]
                        while isinstance(x, (list, tuple, np.ndarray)):
                            x = x[0] if len(x) > 0 else 0
                        while isinstance(y, (list, tuple, np.ndarray)):
                            y = y[0] if len(y) > 0 else 0
                        flat_points.append([float(x), float(y)])

            if flat_points:
                return np.array(flat_points, dtype=np.float32).reshape(-1, 1, 2)
            else:
                return np.array([], dtype=np.float32).reshape(0, 1, 2)

    def get_main_contour_settings(self):
        """
        Return the settings associated with the main contour.
        If no settings are found, return an empty dictionary.
        """
        if isinstance(self.contour, dict) and "settings" in self.contour:
            return self.contour["settings"]
        return {}

    @staticmethod
    def serialize(workpiece):
        def convert_ndarray_to_list(obj):
            if isinstance(obj, np.ndarray):
                if obj.ndim == 2 and obj.shape[1] == 2:
                    obj = obj.reshape(-1, 1, 2)  # ✅ normalize before list conversion
                return obj.tolist()
            elif isinstance(obj, dict) and "contour" in obj:
                contour = obj["contour"]
                if isinstance(contour, np.ndarray) and contour.ndim == 2 and contour.shape[1] == 2:
                    contour = contour.reshape(-1, 1, 2)
                return {
                    "contour": convert_ndarray_to_list(contour),
                    "settings": dict(obj.get("settings", {}))
                }
            elif isinstance(obj, list):
                return [convert_ndarray_to_list(item) for item in obj]
            return obj

        # ✅ Handle dict contour directly
        contour_data = convert_ndarray_to_list(workpiece.contour)

        if isinstance(workpiece.sprayPattern, dict):
            spray_pattern_dict = {
                key: [convert_ndarray_to_list(seg) for seg in val]
                for key, val in workpiece.sprayPattern.items()
            }
        else:
            spray_pattern_dict = convert_ndarray_to_list(workpiece.sprayPattern)

        workpiece.contour = contour_data
        workpiece.sprayPattern = spray_pattern_dict
        return workpiece.to_dict()

    @staticmethod
    def deserialize(data):
        def convert_list_to_ndarray(obj):
            if isinstance(obj, dict) and "contour" in obj:
                arr = np.array(obj["contour"], dtype=np.float32)

                # ✅ Normalize shape to (N, 1, 2)
                if arr.ndim == 1 and arr.shape[0] == 2:
                    arr = arr.reshape(1, 1, 2)  # single point → (1, 1, 2)
                elif arr.ndim == 2 and arr.shape[1] == 2:
                    arr = arr.reshape(-1, 1, 2)  # (N, 2) → (N, 1, 2)

                return {
                    "contour": arr,
                    "settings": obj.get("settings", {})
                }

            elif isinstance(obj, list):
                return [convert_list_to_ndarray(item) for item in obj]

            return obj

        # ----- Main contour -----
        raw_contour = data.get(GlueWorkpieceField.CONTOUR.value, [])

        if isinstance(raw_contour, dict):
            contour = convert_list_to_ndarray(raw_contour)
        elif isinstance(raw_contour, list):
            contour = [convert_list_to_ndarray(seg) for seg in raw_contour]
        else:
            contour = raw_contour  # unexpected type, leave as-is

        # ----- Spray pattern -----
        raw_spray_pattern = data.get(GlueWorkpieceField.SPRAY_PATTERN.value, {})
        spray_pattern = {}

        if isinstance(raw_spray_pattern, dict):
            for key, pattern in raw_spray_pattern.items():
                spray_pattern[key] = [convert_list_to_ndarray(seg) for seg in pattern]
        else:
            spray_pattern = raw_spray_pattern

        # ----- Build workpiece -----
        workpiece = GlueWorkpiece.from_dict(data)
        workpiece.contour = contour
        workpiece.sprayPattern = spray_pattern
        return workpiece

    def to_dict(self)-> dict:
        """
                Convert the Workpiece object into a dictionary representation.

                Returns:
                    dict: A dictionary containing the Workpiece's properties, suitable for serialization or storage.
                """
        return {
            GlueWorkpieceField.WORKPIECE_ID.value: self.workpieceId,
            GlueWorkpieceField.NAME.value: self.name,
            GlueWorkpieceField.DESCRIPTION.value: self.description,
            GlueWorkpieceField.TOOL_ID.value: self.toolID.value,
            GlueWorkpieceField.GRIPPER_ID.value: self.gripperID.value,
            GlueWorkpieceField.GLUE_TYPE.value: self.glueType,  # glueType is now a plain string
            GlueWorkpieceField.PROGRAM.value: self.program.value,
            GlueWorkpieceField.MATERIAL.value: self.material,
            GlueWorkpieceField.CONTOUR.value: self.contour,
            GlueWorkpieceField.OFFSET.value: self.offset,
            GlueWorkpieceField.HEIGHT.value: self.height,
            GlueWorkpieceField.GLUE_QTY.value: self.glueQty,
            GlueWorkpieceField.SPRAY_WIDTH.value: self.sprayWidth,
            GlueWorkpieceField.PICKUP_POINT.value: self.pickupPoint,
            GlueWorkpieceField.SPRAY_PATTERN.value: self.sprayPattern,
            GlueWorkpieceField.CONTOUR_AREA.value: self.contourArea,
            GlueWorkpieceField.NOZZLES.value: self.nozzles

        }

    @staticmethod
    def flatten_spray_pattern(obj):
        """
             Flatten nested spray pattern lists into a single list.

             Args:
                 obj (list): The spray pattern (possibly nested) to be flattened.

             Returns:
                 list: A flattened list containing all points from the spray pattern.
             """
        if isinstance(obj, list):
            flat_obj = []
            for item in obj:
                if isinstance(item, list):
                    flat_obj.extend(GlueWorkpiece.flatten_spray_pattern(item))
                else:
                    flat_obj.append(item)
            return flat_obj
        return [obj]

    @staticmethod
    def reshape_spray_pattern(obj):
        """
        Reshape spray pattern list into list of (N, 1, 2) numpy arrays.

        Args:
            obj (list): The spray pattern, either a single contour or a list of contours.

        Returns:
            list: A list of numpy arrays representing the reshaped spray pattern contours.

        Raises:
            ValueError: If the spray pattern format is invalid or unrecognized.
        """
        if not obj:
            return []

        # If it's a single contour, flatten and reshape it
        if all(isinstance(pt, (list, np.ndarray)) and len(pt) == 2 for pt in obj):
            grouped = np.array(obj, dtype=np.float32).reshape(-1, 1, 2)
            return [grouped]

        # If it's a list of contours
        if isinstance(obj, list) and all(isinstance(c, list) for c in obj):
            result = []
            for contour in obj:
                if not contour:
                    continue
                flat = GlueWorkpiece.flatten_spray_pattern(contour)
                if all(isinstance(x, (int, float)) for x in flat):
                    grouped = [[flat[i], flat[i + 1]] for i in range(0, len(flat), 2)]
                elif all(isinstance(x, list) and len(x) == 2 for x in flat):
                    grouped = flat
                else:
                    raise ValueError(f"Invalid spray pattern shape: {flat}")
                result.append(np.array(grouped, dtype=np.float32).reshape(-1, 1, 2))
            return result

        raise ValueError(f"Unknown spray pattern format: {obj}")

    @staticmethod
    def from_dict(data: dict):
        """
        Deserialize a dictionary into a Workpiece object.

        Args:
          data (dict): A dictionary representation of a Workpiece.

        Returns:
          GlueWorkpiece: The reconstructed Workpiece object.
        """
        return GlueWorkpiece(
            workpieceId=data[GlueWorkpieceField.WORKPIECE_ID.value],
            name=data[GlueWorkpieceField.NAME.value],
            description=data[GlueWorkpieceField.DESCRIPTION.value],
            toolID=ToolID(data[GlueWorkpieceField.TOOL_ID.value]),
            gripperID=Gripper(data[GlueWorkpieceField.GRIPPER_ID.value]),
            glueType=data[GlueWorkpieceField.GLUE_TYPE.value],  # Glue type is now a plain string
            program=Program(data[GlueWorkpieceField.PROGRAM.value]),
            material=data[GlueWorkpieceField.MATERIAL.value],
            contour=data[GlueWorkpieceField.CONTOUR.value],
            offset=data[GlueWorkpieceField.OFFSET.value],
            height=data.get(GlueWorkpieceField.HEIGHT.value, 4),
            pickupPoint=data.get(GlueWorkpieceField.PICKUP_POINT.value, None),
            nozzles=data.get(GlueWorkpieceField.NOZZLES.value, []),  # Setting nozzles to empty list if missing
            contourArea=data[GlueWorkpieceField.CONTOUR_AREA.value],
            glueQty=data[GlueWorkpieceField.GLUE_QTY.value],
            sprayWidth=data[GlueWorkpieceField.SPRAY_WIDTH.value],
            sprayPattern=data.get(GlueWorkpieceField.SPRAY_PATTERN.value, []),

            # Setting spray pattern to empty list if missing
        )

