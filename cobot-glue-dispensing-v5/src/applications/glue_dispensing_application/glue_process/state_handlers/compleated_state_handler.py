from applications.glue_dispensing_application.glue_process.state_machine.GlueProcessState import GlueProcessState

def handle_completed_state(context):
   sm = context.state_machine
   print("Handling COMPLETED state.")
   print("Glue dispensing process completed successfully.")
   
   # Set flag to indicate operation is completed
   context.operation_just_completed = True
   context.service.generatorOff()
   
   return GlueProcessState.IDLE # return next state to transition to