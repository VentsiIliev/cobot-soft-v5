from core.operation_state_management import IOperation


class PaintingOperation(IOperation):
    def _do_start(self, *args, **kwargs):
        print(f"Starting PaintingOperation with args: {args}, kwargs: {kwargs}")

    def _do_stop(self, *args, **kwargs):
        print("Stopping PaintingOperation with args:", args, "kwargs:", kwargs)

    def _do_pause(self, *args, **kwargs):
        print(f"Pausing PaintingOperation with args: {args}, kwargs: {kwargs}")

    def _do_resume(self, *args, **kwargs):
        print(f"Resuming PaintingOperation with args: {args}, kwargs: {kwargs}")