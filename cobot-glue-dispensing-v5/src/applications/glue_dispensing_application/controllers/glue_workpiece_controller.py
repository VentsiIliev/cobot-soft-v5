from typing_extensions import override

from applications.glue_dispensing_application.model.workpiece.GlueWorkpieceField import GlueWorkpieceField
from applications.glue_dispensing_application.services.workpiece.glue_workpiece_service import GlueWorkpieceService
from applications.glue_dispensing_application.model.workpiece.GlueWorkpiece import GlueWorkpiece
from core.controllers.workpiece.BaseWorkpieceController import BaseWorkpieceController

from communication_layer.api.v1 import Constants


class GlueWorkpieceController(BaseWorkpieceController):
    """
    Controller for handling workpiece-related requests.

    Supports:
        - CRUD operations
        - Multi-step creation workflow
        - DXF import
    """

    def __init__(self, workpieceService: GlueWorkpieceService):
        if not isinstance(workpieceService, GlueWorkpieceService):
            raise ValueError("workpieceService must be an instance of WorkpieceService")
        self.workpieceService = workpieceService
        super().__init__(self.workpieceService,GlueWorkpiece)
        self._initialize_handlers()
        self.create_workpiece_cache = {}
        self.create_workpiece_step = 1
    # ============================================================
    # REGISTER HANDLERS
    # ============================================================
    def _initialize_handlers(self):
        pass

    # =========================
    # INTERNAL HANDLERS
    # =========================

    @override
    def _save_workpiece(self, data):
        try:
            # Extract and transform spray pattern
            sprayPattern = data.get(GlueWorkpieceField.SPRAY_PATTERN.value, {})
            contours = sprayPattern.get("Contour")
            fill = sprayPattern.get("Fill")

            # Handle external contours
            externalContours = data.get(GlueWorkpieceField.CONTOUR.value, [])
            print(f"WorkpieceHandler: Original contours: {externalContours}")

            if externalContours is None or len(externalContours) == 0:
                externalContour = []
            else:
                # externalContours should be in dict format {"contour": points, "settings": {...}}
                externalContour = externalContours

            data[GlueWorkpieceField.CONTOUR.value] = externalContour

            # Update spray pattern
            sprayPattern['Contour'] = contours
            sprayPattern['Fill'] = fill
            data[GlueWorkpieceField.SPRAY_PATTERN.value] = sprayPattern

            print(f"WorkpieceHandler: Data after transform: {data}")
            return super()._save_workpiece(data=data)
        except Exception as e:
            print(f"WorkpieceHandler: Error in handle_save_workpiece: {e}")
            return {"status": Constants.RESPONSE_STATUS_ERROR, "message": str(e), "data": None}


    def get_workpiece_by_id(self,workpiece_id: str) -> GlueWorkpiece:
        """
        Retrieve a workpiece by its ID.

        Args:
            workpiece_id: ID of the workpiece to retrieve

        Returns:
            GlueWorkpiece instance if found, else None
        """
        workpiece = self.workpieceService.get_workpiece_by_id(workpiece_id)
        return workpiece