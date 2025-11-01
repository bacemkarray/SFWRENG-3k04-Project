PARAMETER_RULES = {
    "Lower Rate Limit": (50, 175),
    "Upper Rate Limit": (50, 175),
    "Maximum Sensor Rate": (50, 175),
    "Fixed AV Delay": (70, 300),
    "Atrial Amplitude": (0.5, 7.0),
    "Atrial Pulse Width": (0.05, 1.9),
    "Atrial Sensitivity": (0.25, 10.0),
    "Ventricular Amplitude": (0.5, 7.0),
    "Ventricular Pulse Width": (0.05, 1.9),
    "Ventricular Sensitivity": (0.25, 10.0),
    "ARP": (150, 500),
    "VRP": (150, 500)
}


def validate_param(param_name, value):
    rule = PARAMETER_RULES.get(param_name)
    try:
        val = float(value)
    except ValueError:
        return False, f"{param_name} must be numeric."

    low, high = rule
    if not (low <= val <= high):
        return False, f"{param_name} must be between {low} and {high}."
    
    return True, ""
