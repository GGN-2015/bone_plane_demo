from py_ap200_simple_interface import AimooeExtDrive, I_ConnectionMethod
import numpy as np

# Initialize AimooeExtDrive
drive = AimooeExtDrive()
drive.connect(I_ConnectionMethod.I_USB)

def get_rt_now():
    # BONE-1 is a sample specific tool
    # path and toolname should not contain special characters
    tool_info = drive.get_specific_tool_info(".", ["BONE-1"]).get("BONE-1")
    if tool_info is not None:
        Tto = np.array(tool_info["Origin"])
        Rto = np.array(tool_info["rMatrix"])
        return Rto, Tto 
    return None, None
