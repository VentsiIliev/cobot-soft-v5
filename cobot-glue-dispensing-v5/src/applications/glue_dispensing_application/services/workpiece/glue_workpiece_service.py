from applications.glue_dispensing_application.repositories.workpiece.glue_workpiece_json_repository import \
    GlueWorkpieceJsonRepository
from core.services.workpiece.BaseWorkpieceService import BaseWorkpieceService


class GlueWorkpieceService(BaseWorkpieceService):
    def __init__(self, repository:GlueWorkpieceJsonRepository):
        super().__init__(repository)
