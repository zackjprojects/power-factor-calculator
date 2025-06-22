import math

def get_float_input(prompt, min_val=None, max_val=None):
    """Get validated float input from user"""
    while True:
        try:
            value = float(input(prompt))
            if min_val is not None and value < min_val:
                print(f"Value must be >= {min_val}")
                continue
            if max_val is not None and value > max_val:
                print(f"Value must be <= {max_val}")
                continue
            return value
        except ValueError:
            print("Please enter a valid number.")

def get_load_type():
    """Get and validate load type from user"""
    while True:
        load_type = input("Load type (resistive/inductive/capacitive): ").lower().strip()
        if load_type in ['resistive', 'inductive', 'capacitive']:
            return load_type
        print("Please enter 'resistive', 'inductive', or 'capacitive'")

def get_power_factor_sign(load_type):
    """Get power factor sign for inductive/capacitive loads"""
    if load_type == 'inductive':
        while True:
            sign = input("Power factor (lagging/leading): ").lower().strip()
            if sign in ['lagging', 'leading']:
                return 1 if sign == 'lagging' else -1
            print("Please enter 'lagging' or 'leading'")
    elif load_type == 'capacitive':
        while True:
            sign = input("Power factor (lagging/leading): ").lower().strip()
            if sign in ['lagging', 'leading']:
                return -1 if sign == 'leading' else 1
            print("Please enter 'lagging' or 'leading'")
    return 1

def get_desired_power_factor():
    """Get desired power factor and type from user"""
    while True:
        desired_pf = get_float_input("Desired power factor (0-1): ", min_val=0, max_val=1)
        if desired_pf == 1.0:
            return desired_pf, 'unity'
        
        while True:
            pf_type = input("Desired power factor type (lagging/leading): ").lower().strip()
            if pf_type in ['lagging', 'leading']:
                return desired_pf, pf_type
            print("Please enter 'lagging' or 'leading'")

def calculate_load_powers(load_type, **kwargs):
    """Calculate real and reactive power for a load"""
    if load_type == 'resistive':
        P = kwargs['real_power']  # kW
        Q = 0  # kVAR
    elif load_type == 'inductive':
        Q = kwargs['reactive_power']  # kVAR (input)
        pf = kwargs['power_factor']
        sign = kwargs['pf_sign']
        
        # For inductive loads: Q is given, calculate P from power factor
        # Q = P * tan(θ), where cos(θ) = pf
        # So P = Q / tan(θ) = Q / (sqrt(1-pf²)/pf) = Q * pf / sqrt(1-pf²)
        P = Q * pf / math.sqrt(1 - pf**2)  # kW
        Q = sign * Q  # Apply sign (positive for lagging)
    else:  # capacitive
        S = kwargs['reactive_power']  # kVA (but called reactive power in prompt)
        pf = kwargs['power_factor']
        sign = kwargs['pf_sign']
        
        P = S * pf  # kW
        Q_magnitude = math.sqrt(S**2 - P**2)  # kVAR
        Q = sign * Q_magnitude  # kVAR (negative for leading)
    
    return P, Q

def calculate_required_reactive_power(total_P, total_Q, desired_pf, desired_pf_type):
    """Calculate the required reactive power to achieve desired power factor"""
    if desired_pf == 1.0:
        # Unity power factor - cancel all reactive power
        return -total_Q
    
    # Calculate the required reactive power for desired power factor
    # tan(θ) = Q/P, where cos(θ) = desired_pf
    desired_theta = math.acos(desired_pf)
    desired_Q_magnitude = total_P * math.tan(desired_theta)
    
    if desired_pf_type == 'lagging':
        desired_Q = desired_Q_magnitude  # Positive for lagging
    else:  # leading
        desired_Q = -desired_Q_magnitude  # Negative for leading
    
    # Required change in reactive power
    Q_correction = desired_Q - total_Q
    
    return Q_correction

def main():
    print("=" * 60)
    print("POWER FACTOR CORRECTION CALCULATOR")
    print("Single-Phase Parallel Load System")
    print("=" * 60)
    
    # Get system parameters
    print("\n--- SYSTEM PARAMETERS ---")
    voltage = get_float_input("Supply voltage (V): ", min_val=0)
    frequency = get_float_input("Supply frequency (Hz): ", min_val=0)
    num_loads = int(get_float_input("Number of parallel loads: ", min_val=1))
    
    # Initialize totals
    total_P = 0  # kW
    total_Q = 0  # kVAR
    loads_data = []
    
    # Get load data
    print("\n--- LOAD DATA ENTRY ---")
    for i in range(num_loads):
        print(f"\nLoad {i+1}:")
        load_type = get_load_type()
        
        if load_type == 'resistive':
            real_power = get_float_input("  Real power (kW): ", min_val=0)
            P, Q = calculate_load_powers(load_type, real_power=real_power)
            loads_data.append({
                'type': load_type,
                'P': P,
                'Q': Q,
                'real_power': real_power
            })
        elif load_type == 'inductive':
            reactive_power = get_float_input("  Reactive power (kVAR): ", min_val=0)
            power_factor = get_float_input("  Power factor (0-1): ", min_val=0, max_val=1)
            pf_sign = get_power_factor_sign(load_type)
            
            P, Q = calculate_load_powers(
                load_type, 
                reactive_power=reactive_power, 
                power_factor=power_factor,
                pf_sign=pf_sign
            )
            loads_data.append({
                'type': load_type,
                'P': P,
                'Q': Q,
                'reactive_power': reactive_power,
                'power_factor': power_factor,
                'pf_sign': pf_sign
            })
        else:  # capacitive
            reactive_power = get_float_input("  Reactive power (kVA): ", min_val=0)
            power_factor = get_float_input("  Power factor (0-1): ", min_val=0, max_val=1)
            pf_sign = get_power_factor_sign(load_type)
            
            P, Q = calculate_load_powers(
                load_type, 
                reactive_power=reactive_power, 
                power_factor=power_factor,
                pf_sign=pf_sign
            )
            loads_data.append({
                'type': load_type,
                'P': P,
                'Q': Q,
                'reactive_power': reactive_power,
                'power_factor': power_factor,
                'pf_sign': pf_sign
            })
        
        total_P += P
        total_Q += Q
        print(f"  → P = {P:.3f} kW, Q = {Q:.3f} kVAR")
    
    # Calculate system totals before compensation
    total_S = math.sqrt(total_P**2 + total_Q**2)
    current_pf = total_P / total_S if total_S > 0 else 1.0
    current_uncompensated = (total_S * 1000) / voltage  # Convert kVA to VA, then calculate current
    
    # Get desired power factor
    print("\n--- POWER FACTOR CORRECTION TARGET ---")
    desired_pf, desired_pf_type = get_desired_power_factor()
    
    # Calculate required reactive power correction
    Q_correction = calculate_required_reactive_power(total_P, total_Q, desired_pf, desired_pf_type)
    
    # Calculate capacitor/inductor parameters
    if abs(Q_correction) > 1e-6:  # Only if correction is needed
        Q_correction_VAR = abs(Q_correction) * 1000  # Convert to VAR
        X_reactive = voltage**2 / Q_correction_VAR  # Reactive component reactance (Ohms)
        
        if Q_correction < 0:  # Need capacitive correction
            capacitance = 1 / (2 * math.pi * frequency * X_reactive)  # Farads
            inductance = 0
            correction_type = "Capacitive"
        else:  # Need inductive correction
            inductance = X_reactive / (2 * math.pi * frequency)  # Henries
            capacitance = 0
            correction_type = "Inductive"
    else:
        capacitance = 0
        inductance = 0
        X_reactive = float('inf')
        correction_type = "None"
    
    # Calculate system parameters after compensation
    total_Q_after = total_Q + Q_correction
    total_S_after = math.sqrt(total_P**2 + total_Q_after**2)
    current_compensated = (total_S_after * 1000) / voltage
    actual_pf_after = total_P / total_S_after if total_S_after > 0 else 1.0
    
    # Display results
    print("\n" + "=" * 60)
    print("CALCULATION RESULTS")
    print("=" * 60)
    
    print("\n--- LOAD SUMMARY ---")
    for i, load in enumerate(loads_data):
        print(f"Load {i+1} ({load['type']}):")
        if load['type'] == 'resistive':
            print(f"  Input: {load['real_power']:.3f} kW")
        elif load['type'] == 'inductive':
            pf_desc = "lagging" if load['pf_sign'] > 0 else "leading"
            print(f"  Input: {load['reactive_power']:.3f} kVAR, pf = {load['power_factor']:.3f} {pf_desc}")
        else:  # capacitive
            pf_desc = "lagging" if load['pf_sign'] > 0 else "leading"
            print(f"  Input: {load['reactive_power']:.3f} kVA, pf = {load['power_factor']:.3f} {pf_desc}")
        print(f"  Powers: P = {load['P']:.3f} kW, Q = {load['Q']:.3f} kVAR")
    
    print("\n--- SYSTEM TOTALS (BEFORE COMPENSATION) ---")
    print(f"Total Active Power (P):     {total_P:.3f} kW")
    print(f"Total Reactive Power (Q):   {total_Q:.3f} kVAR")
    print(f"Total Apparent Power (S):   {total_S:.3f} kVA")
    pf_type_desc = "lagging" if total_Q > 0 else "leading" if total_Q < 0 else "unity"
    print(f"System Power Factor:        {current_pf:.3f} {pf_type_desc}")
    print(f"Supply Current:             {current_uncompensated:.3f} A")
    
    print("\n--- POWER FACTOR CORRECTION ---")
    desired_pf_desc = desired_pf_type if desired_pf != 1.0 else "unity"
    print(f"Desired Power Factor:       {desired_pf:.3f} {desired_pf_desc}")
    
    if abs(Q_correction) > 1e-6:
        print(f"Required Correction:        {abs(Q_correction):.3f} kVAR ({correction_type.lower()})")
        
        if correction_type == "Capacitive":
            print(f"Capacitance Required:       {capacitance*1e6:.3f} µF")
            print(f"Capacitive Reactance:       {X_reactive:.3f} Ω")
        else:  # Inductive
            print(f"Inductance Required:        {inductance*1e3:.3f} mH")
            print(f"Inductive Reactance:        {X_reactive:.3f} Ω")
        
        print(f"Correction Type:            {correction_type}")
    else:
        print("No power factor correction needed - system already at desired power factor")
    
    print("\n--- SYSTEM PERFORMANCE (AFTER COMPENSATION) ---")
    print(f"Total Active Power (P):     {total_P:.3f} kW")
    print(f"Total Reactive Power (Q):   {total_Q_after:.3f} kVAR")
    print(f"Total Apparent Power (S):   {total_S_after:.3f} kVA")
    actual_pf_type_desc = "lagging" if total_Q_after > 1e-6 else "leading" if total_Q_after < -1e-6 else "unity"
    print(f"System Power Factor:        {actual_pf_after:.3f} {actual_pf_type_desc}")
    print(f"Supply Current:             {current_compensated:.3f} A")
    
    print("\n--- IMPROVEMENT SUMMARY ---")
    current_reduction = current_uncompensated - current_compensated
    current_reduction_percent = (current_reduction / current_uncompensated) * 100 if current_uncompensated > 0 else 0
    print(f"Current Reduction:          {current_reduction:.3f} A ({current_reduction_percent:.1f}%)")
    
    apparent_power_reduction = total_S - total_S_after
    print(f"Apparent Power Reduction:   {apparent_power_reduction:.3f} kVA")
    
    pf_improvement = actual_pf_after - current_pf
    print(f"Power Factor Improvement:   {pf_improvement:.3f}")
    
    print("\n" + "=" * 57)
    print("CALCULATION COMPLETE")
    print("=" * 57)

if __name__ == "__main__":
    main()
