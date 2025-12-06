from communication_layer.api.v1 import Constants
from communication_layer.api.v1.endpoints import workpiece_endpoints
from core.controllers.BaseController import BaseController
from core.services.workpiece.BaseWorkpieceService import BaseWorkpieceService


class BaseWorkpieceController(BaseController):
    """
    Base controller for workpiece-related operations.
    Inherits from BaseController to provide common controller functionalities.
    """

    def __init__(self, workpieceService: BaseWorkpieceService, workpiece_cls):
        """
        Args:
            workpieceService: instance of BaseWorkpieceService
            workpiece_cls: optional class or factory used to construct workpiece instances from dicts.
                          Expected to provide a classmethod `from_dict(data)` or be a callable that
                          returns a workpiece instance when given the raw data dict.
        """
        if not isinstance(workpieceService, BaseWorkpieceService):
            raise ValueError("workpieceService must be an instance of BaseWorkpieceService")
        self.workpieceService = workpieceService
        # Validate workpiece_cls if provided (deferred: we'll check at use-time as well)
        self.workpiece_cls = workpiece_cls
        super().__init__()
        self._initialize_handlers()

    # ============================================================
    # REGISTER HANDLERS
    # ============================================================
    def _initialize_handlers(self):
        self.register_handler(workpiece_endpoints.WORKPIECE_GET_ALL, lambda data=None: self._get_all_workpieces())
        self.register_handler(workpiece_endpoints.WORKPIECE_GET_BY_ID,
                              lambda data: self._get_workpiece_by_id(data.get("id") if data else None))
        self.register_handler(workpiece_endpoints.WORKPIECE_SAVE, lambda data: self._save_workpiece(data))
        self.register_handler(workpiece_endpoints.WORKPIECE_DELETE,
                              lambda data: self._delete_workpiece_by_id(data.get("id") if data else None))
        self.register_handler(workpiece_endpoints.WORKPIECE_SAVE_DXF, lambda data: self._save_workpiece_dxf(data))

    # =========================
    # INTERNAL HANDLERS
    # =========================
    def _get_all_workpieces(self):
        workpieces = self.workpieceService.load_all()
        for wp in workpieces:
            print(f"Loaded workpiece: ID={wp.workpieceId}, Name={wp.name}")

        return {
            "status": Constants.RESPONSE_STATUS_SUCCESS,
            "message": "Loaded all workpieces",
            "data": workpieces,
        }

    def _get_workpiece_by_id(self, workpieceId):
        if not workpieceId:
            return {
                "status": Constants.RESPONSE_STATUS_ERROR,
                "message": "No workpiece ID provided",
                "data": None,
            }
        workpiece = self.workpieceService.get_workpiece_by_id(workpieceId)
        if not workpiece:
            return {
                "status": Constants.RESPONSE_STATUS_ERROR,
                "message": f"Workpiece {workpieceId} not found",
                "data": None,
            }
        return {
            "status": Constants.RESPONSE_STATUS_SUCCESS,
            "message": f"Workpiece {workpieceId} retrieved",
            "data": workpiece,
        }

    def _save_workpiece(self, data):
        if not data:
            return {
                "status": Constants.RESPONSE_STATUS_ERROR,
                "message": "No data provided for saving workpiece",
                "data": None,
            }
        try:
            workpiece = self.workpiece_cls.from_dict(data)
            print(f"Workpiece after from_dict: {workpiece}")
        except Exception as e:
            return {
                "status": Constants.RESPONSE_STATUS_ERROR,
                "message": f"Error creating Workpiece from data: {e}",
                "data": None,
            }
        result = self.workpieceService.save_workpiece(workpiece)
        status = Constants.RESPONSE_STATUS_SUCCESS if result else Constants.RESPONSE_STATUS_ERROR
        return {"status": status, "message": "Workpiece saved", "data": None}

    def _delete_workpiece_by_id(self, workpieceId):
        if not workpieceId:
            return {
                "status": Constants.RESPONSE_STATUS_ERROR,
                "message": "No workpiece ID provided for deletion",
                "data": None,
            }
        result = self.workpieceService.delete_workpiece_by_id(workpieceId)
        status = Constants.RESPONSE_STATUS_SUCCESS if result else Constants.RESPONSE_STATUS_ERROR
        return {"status": status, "message": "Workpiece deleted" if result else "Failed to delete workpiece", "data": None}

    def _save_workpiece_dxf(self, data):
        # You can implement DXF import logic here
        return {"status": Constants.RESPONSE_STATUS_SUCCESS, "message": "DXF import not implemented yet", "data": None}

