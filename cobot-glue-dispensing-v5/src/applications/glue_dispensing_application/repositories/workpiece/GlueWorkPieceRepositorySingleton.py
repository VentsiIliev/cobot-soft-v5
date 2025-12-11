from applications.glue_dispensing_application.repositories.workpiece.glue_workpiece_json_repository import \
    GlueWorkpieceJsonRepository
from applications.glue_dispensing_application.model.workpiece.GlueWorkpiece import GlueWorkpiece
from modules.shared.GlueWorkpieceField import GlueWorkpieceField

from core.application.ApplicationContext import get_workpiece_storage_path
class GlueWorkPieceRepositorySingleton:
    """
       Singleton class responsible for managing a single instance of the Workpiece repository.
       The class ensures that only one instance of the repository is created and provides a global
       point of access to it.

       This class uses `WorkpieceJsonRepository` to handle storage and retrieval of workpieces
       as JSON data.

       Attributes:
           _instance (GlueWorkpieceJsonRepository or None): The single instance of the repository.

       Methods:
           get_instance(cls): Returns the singleton instance of the WorkpieceJsonRepository.
       """

    _instance = None

    @classmethod
    def get_instance(cls):
        """
                Retrieves the singleton instance of the `WorkpieceJsonRepository`. If the instance does
                not exist, it is created and initialized with necessary parameters.

                The repository is initialized with a directory path and a list of fields representing the
                attributes of a Workpiece. This ensures that the repository is set up to manage and store
                Workpiece objects correctly.

                Args:
                    cls (type): The class type, used to access the singleton instance.

                Returns:
                    GlueWorkpieceJsonRepository: The singleton instance of the repository.

                Notes:
                    The instance is created with the directory `"system/storage"` and
                    a set of `WorkpieceField` attributes such as `WORKPIECE_ID`, `NAME`, `DESCRIPTION`,
                    and others required for managing Workpiece data.

                Example:
                    repo = WorkPieceRepositorySingleton.get_instance()
                    workpiece_data = repo.get_workpieces()  # Example of interacting with the repository
                """
        if cls._instance is None:
            # Get application-specific workpiece storage path
            storage_dir = get_workpiece_storage_path(create_if_missing=True)
            
            # If no application context is set, fall back to system storage
            if storage_dir is None:
                from modules import PathResolver, PathType
                storage_dir = PathResolver.get_path(PathType.WORKPIECE_STORAGE)
                print("Warning: No application context set, using system-wide workpiece storage")
            
            fields = [GlueWorkpieceField.WORKPIECE_ID, GlueWorkpieceField.NAME, GlueWorkpieceField.DESCRIPTION,
                      GlueWorkpieceField.TOOL_ID, GlueWorkpieceField.GRIPPER_ID,
                      GlueWorkpieceField.GLUE_TYPE, GlueWorkpieceField.PROGRAM, GlueWorkpieceField.MATERIAL, GlueWorkpieceField.CONTOUR,
                      GlueWorkpieceField.OFFSET, GlueWorkpieceField.HEIGHT, GlueWorkpieceField.SPRAY_PATTERN,
                      GlueWorkpieceField.CONTOUR_AREA,
                      GlueWorkpieceField.NOZZLES]
            cls._instance = GlueWorkpieceJsonRepository(storage_dir, fields, GlueWorkpiece)
            
            print(f"GlueWorkPieceRepository initialized with storage: {storage_dir}")
        return cls._instance