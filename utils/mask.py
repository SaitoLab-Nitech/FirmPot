
#------------------------------------------------
# Import
#------------------------------------------------

import re
import sys
sys.dont_write_bytecode = True
import json

from utils.utils import run_cmd
from utils.params import hardware_info

#------------------------------------------------
# Regular expressions for dates
#------------------------------------------------

# Week
pattern_week = r'((Sun|Mon|Tues?|Wed(?:nes)?|Thu(?:rs)?|Fri|Sat(?:ur))(?:day)?)'

# Year
pattern_year = r'\d{4}'

# Month
pattern_month = r'((1[0-2]|0?[1-9])|(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?))'

# Day
pattern_day = r'([12][0-9]|3[01]|0?[1-9])(th)?'

# Date
pattern_date_1 = pattern_year  + r'[// -]+' + pattern_month + r'[// -]+' + pattern_day # yyyy-mm-dd
pattern_date_2 = pattern_month  + r'[// -]+' + pattern_day + r'[// -]+' + pattern_year # mm/dd/yy
pattern_date_3 = pattern_day  + r'[// -]+' + pattern_month + r'[// -]+' + pattern_year # dd-mm-yy

#------------------------------------------------
# Regular expressions for Time
#------------------------------------------------

# Hour
pattern_hour = r'(1[0-9]|2[0-4]|0?[0-9])(h|hour)?'

# Minute
pattern_min = r'([1-5][0-9]|0?[0-9])(m|min|miniutes)?'

# Seconds
pattern_sec = r'([1-5][0-9]|0?[0-9])(s|sec|seconds)?'

# Time
pattern_time = pattern_hour + r':' + pattern_min + r':' + pattern_sec # hh:mm:ss  

#------------------------------------------------
# Masking List
#------------------------------------------------

hardware_info["KERNELINFO"] = run_cmd("uname -r")[0]    
data = json.loads(" ".join(run_cmd("lshw -C processor -C display -json")))
for d in data:
    if "processor" in d.values():
        hardware_info["CPUINFO"] = d["product"]
    if "display" in d.values():
        hardware_info["GPUINFO"] = d["product"]

#------------------------------------------------
# Functions
#------------------------------------------------

def mask_str(string):

    for key, value in hardware_info.items():
        string = string.replace(value, key)

    # date
    string = re.sub(pattern_date_1, "DATEINFO", string)
    string = re.sub(pattern_date_2, "DATEINFO", string)
    string = re.sub(pattern_date_3, "DATEINFO", string)
    string = re.sub(pattern_time, "TIMEINFO", string)
    
    return string

