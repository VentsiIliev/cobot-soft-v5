"""
Workpiece Handler - API Gateway

Handles all workpiece-related requests including CRUD operations, creation workflow, and DXF import.
"""

import traceback

from communication_layer.api.v1 import Constants
from communication_layer.api.v1.Response import Response
from communication_layer.api.v1.endpoints import workpiece_endpoints
from communication_layer.api_gateway.interfaces.dispatch import IDispatcher

class WorkpieceDispatch(IDispatcher):
    """
    Handles workpiece operations for the API gateway.
    
    This handler manages workpiece creation, saving, deletion, and import operations.
    """
    
    def __init__(self, application, workpieceController):
        """
        Initialize the WorkpieceHandler.
        
        Args:
            application: Application instance
            workpieceController: Workpiece controller instance
        """
        self.application = application
        self.workpieceController = workpieceController

    def dispatch(self, parts: list, request: str, data: dict = None) -> dict:
        """
        Route workpiece requests to appropriate handlers.
        
        Args:
            parts (list): Parsed request parts
            request (str): Full request string
            data: Request data
            
        Returns:
            dict: Response dictionary with operation result
        """
        print(f"WorkpieceHandler: Handling request: {request} with parts: {parts} data {data}")
        
        # Handle both new RESTful endpoints and legacy endpoints
        if request in [workpiece_endpoints.WORKPIECE_SAVE] or (len(parts) > 1 and parts[1] == "save"):
            return self.handle_save_workpiece(request, parts, data)
        elif request in [workpiece_endpoints.WORKPIECE_SAVE_DXF] or (len(parts) > 1 and parts[1] == "dxf"):
            return self.handle_save_workpiece_from_dxf(data)
        elif request in [workpiece_endpoints.WORKPIECE_GET_ALL] or (len(parts) > 1 and parts[1] == "getall"):
            return self.handle_get_all_workpieces()
        elif request in [workpiece_endpoints.WORKPIECE_DELETE] or (len(parts) > 1 and parts[1] == "delete"):
            return self.handle_delete_workpiece(data)
        elif request in [workpiece_endpoints.WORKPIECE_GET_BY_ID] or (len(parts) > 1 and parts[1] == "getbyid"):
            return self.handle_get_workpiece_by_id(data)
        else:
            raise ValueError(f"Unknown request: {request}")

    
    def handle_save_workpiece(self, request, parts, data):
        """
        Handle workpiece saving with spray pattern transformation.
        
        Args:
            request (str): Full request string
            parts (list): Parsed request parts
            data (dict): Workpiece data to save
            
        Returns:
            dict: Response indicating success or failure
        """
        print("WorkpieceHandler: Handling save workpiece")
        
        try:
            
            # Save workpiece
            result = self.workpieceController._save_workpiece(data)
            
            if result:
                return Response(
                    Constants.RESPONSE_STATUS_SUCCESS, 
                    message="Workpiece saved successfully"
                ).to_dict()
            else:
                return Response(
                    Constants.RESPONSE_STATUS_ERROR, 
                    message="Error saving workpiece"
                ).to_dict()
                
        except Exception as e:
            print(f"WorkpieceDispatcher: Error saving workpiece: {e}")
            traceback.print_exc()
            return Response(
                Constants.RESPONSE_STATUS_ERROR, 
                message=f"Error saving workpiece: {e}"
            ).to_dict()
    
    def handle_save_workpiece_from_dxf(self, data):
        """
        Handle workpiece import from DXF format.
        
        Args:
            data: DXF workpiece data
            
        Returns:
            dict: Response indicating success or failure
        """
        print("WorkpieceHandler: Handling save workpiece from DXF")
        
        try:
            result = self.workpieceController.handlePostRequest(data)
            
            if result:
                return Response(
                    Constants.RESPONSE_STATUS_SUCCESS, 
                    message="Workpiece saved successfully"
                ).to_dict()
            else:
                return Response(
                    Constants.RESPONSE_STATUS_ERROR, 
                    message="Error saving workpiece"
                ).to_dict()
                
        except Exception as e:
            print(f"WorkpieceHandler: Error saving workpiece from DXF: {e}")
            return Response(
                Constants.RESPONSE_STATUS_ERROR, 
                message=f"Error saving workpiece from DXF: {e}"
            ).to_dict()
    
    def handle_get_all_workpieces(self):
        """
        Handle getting all workpieces.
        
        Returns:
            dict: Response with all workpieces data
        """
        print("WorkpieceHandler: Handling get all workpieces")
        
        try:
            return self.workpieceController._get_all_workpieces()
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(
                Constants.RESPONSE_STATUS_ERROR, 
                message=f"Error getting all workpieces: {e}"
            ).to_dict()
    
    def handle_get_workpiece_by_id(self, data):
        """
        Handle getting workpiece by ID.
        
        Args:
            data (dict): Request data containing workpiece ID
            
        Returns:
            dict: Response with workpiece data or error
        """
        print(f"WorkpieceHandler: Handling get workpiece by ID: {data}")
        
        try:
            workpieceId = data.get("workpieceId", None)
            if workpieceId is None:
                return Response(
                    Constants.RESPONSE_STATUS_ERROR,
                    message="Workpiece ID not provided"
                ).to_dict()

            workpiece = self.workpieceController.get_workpiece_by_id(workpieceId)
            print(f"WorkpieceHandler: Retrieved workpiece: {workpiece}")
            if workpiece:
                # Convert workpiece object to dictionary for serialization
                workpiece_dict = workpiece.to_dict()
                return Response(
                    Constants.RESPONSE_STATUS_SUCCESS,
                    data=workpiece_dict
                ).to_dict()
            else:
                return Response(
                    Constants.RESPONSE_STATUS_ERROR,
                    message="Workpiece not found"
                ).to_dict()
                
        except Exception as e:
            print(f"WorkpieceHandler: Error getting workpiece by ID: {e}")
            return Response(
                Constants.RESPONSE_STATUS_ERROR, 
                message=f"Error getting workpiece by ID: {e}"
            ).to_dict()
    
    def handle_delete_workpiece(self, data):
        """
        Handle workpiece deletion.
        
        Args:
            data (dict): Request data containing workpiece ID
            
        Returns:
            dict: Response indicating success or failure
        """
        print(f"WorkpieceHandler: Handling delete workpiece: {data}")
        
        try:
            workpieceId = data.get("workpieceId", None)
            if workpieceId is None:
                return Response(
                    Constants.RESPONSE_STATUS_ERROR, 
                    message="Workpiece ID not provided"
                ).to_dict()
            
            result = self.workpieceController.delete_workpiece_by_id(workpieceId)
            
            if result:
                return Response(
                    Constants.RESPONSE_STATUS_SUCCESS, 
                    message="Workpiece deleted successfully"
                ).to_dict()
            else:
                return Response(
                    Constants.RESPONSE_STATUS_ERROR, 
                    message="Error deleting workpiece"
                ).to_dict()
                
        except Exception as e:
            print(f"WorkpieceHandler: Error deleting workpiece: {e}")
            return Response(
                Constants.RESPONSE_STATUS_ERROR, 
                message=f"Error deleting workpiece: {e}"
            ).to_dict()