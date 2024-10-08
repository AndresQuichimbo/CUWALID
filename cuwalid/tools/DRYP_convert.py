import json
import re
import os
import sys

def convert_text_to_json(input_file, output_file=None):
    """
    Converts a text file to a JSON file based on its format.

    This function reads an input text file, determines its format based on the first line, 
    and parses the content into a predefined JSON structure. The converted JSON is saved 
    to a specified output file. If the conversion is successful, the original input file 
    is deleted.

    Parameters
    ----------
    input_file : str
        Path to the input text file to be converted. The file should be in either DWAPM_SET 
        or drylandmodel format.

    output_file : str, optional
        Path to the output JSON file. If not provided, the output file is named based on 
        the input file name with a '.json' extension.

    Returns
    -------
    None
        The function does not return any value. It saves the converted JSON to a file and 
        may delete the input file if the conversion is successful.

    Raises
    ------
    Exception
        If there is an error during file saving or deletion, an exception is printed.

    Notes
    -----
    The function supports two formats:
    
    - DWAPM_SET: The input file is expected to have settings in a specific format. The 
      corresponding JSON structure and mappings for this format are predefined.
    
    - drylandmodel: The input file is expected to describe a dryland model. The function 
      parses the file into a predefined JSON structure based on mappings for this format.

    Example
    -------
    convert_text_to_json('path/to/input_file.txt', 'path/to/output_file.json')
    """

    if not output_file:
        output_file = os.path.splitext(input_file)[0] + '.json'

    # Define JSON structures for different formats
    json_structure_dryland = {
        "drylandmodel": {
            "model_name": None
        },
        "TERRAIN": {
            "path_dem": None,
            "path_Qo": None,
            "path_fdl": None,
            "path_riv_decay": None,
            "path_mask": None,
            "path_riv_len": None,
            "path_riv_width": None,
            "path_riv_elev": None
        },
        "VEGETATION": {
            "path_veg_kc": None,
            "path_veg_lulc": None,
            "path_veg_nn": None
        },
        "UNSATURATED": {
            "path_uz_theta_sat": None,
            "path_uz_theta_res": None,
            "path_uz_theta_awc": None,
            "path_uz_theta_wp": None,
            "path_uz_root": None,
            "path_uz_lambda": None,
            "path_uz_psi": None,
            "path_uz_ksat": None,
            "path_uz_sigmaksat": None,
            "path_uz_theta": None,
            "path_riv_ksat": None
        },
        "SATURATED": {
            "path_sz_mask": None,
            "path_sz_ksat": None,
            "path_sz_sy": None,
            "path_sz_wte": None,
            "path_sz_bc_flux": None,
            "path_sz_bc_head": None,
            "path_sz_bottom": None
        },
        "METEO": {
            "path_pre": None,
            "path_pet": None,
            "path_aof": None,
            "Other": None
        },
        "GROUNDWATER": {
            "path_gw_depth": None,
            "path_gw_bdd": None,
            "path_gw_2l_bottom": None,
            "path_gw_2l_ksat": None,
            "path_gw_2l_sy": None,
            "path_gw_2l_ss": None,
            "path_gw_2l_wte": None,
            "path_gw_type": None,
            "path_gw_lake_elev": None,
            "path_pnds_vmax": None,
            "path_pnds_shape_par": None
        },
        "OUTPUT": {
            "path_out_sz": None,
            "path_out_uz": None,
            "path_out_oz": None,
            "path_output": None,
            "Other": None,
            "path_setting": None,
            "path_vg_settings": None,
            "path_rp_settings": None,
            "path_of_settings": None,
            "path_projection": None
        }
    }

    json_structure_settings = {
        "SETTINGS": {
            "start_date": None,
            "end_date": None,
            "dt_of": None,
            "dt_gw": None
        },
        "READING": {
            "data_read": None,
            "data_step": None,
            "data_reproject": None,
            "data_interp": None
        },
        "COMPONENTS": {
            "method_inf": None,
            "method_gw": None,
            "not used 1": None,
            "not used 2": None
        },
        "OUTPUT": {
            "output_csv": None,
            "output_grid": None,
            "output_dt": None,
            "Save discharge in volumetric rate units": None,
            "not used 2": None,
            "not used 3": None
        },
        "GLOBAL_FACTORS": {
            "uz_kdt": None,
            "uz_kdroot": None,
            "uz_kawc": None,
            "uz_kkast": None,
            "uz_ksigma": None,
            "riv_kksat": None,
            "riv_kdecay": None,
            "riv_kwidth": None,
            "sz_kksat": None,
            "sz_ksy": None,
            "of_kflow": None
        }
    }

    mappings_dryland = {
        "Model name": "drylandmodel.model_name",
        "Topography (DEM)": "TERRAIN.path_dem",
        "Flow Direction (fd)": "TERRAIN.path_fdl",
        "River decay parameters": "TERRAIN.path_riv_decay",
        "Basin Mask (catchment)": "TERRAIN.path_mask",
        "River length": "TERRAIN.path_riv_len",
        "River width": "TERRAIN.path_riv_width",
        "River bottom elevation": "TERRAIN.path_riv_elev",
        "Vegetation type Kc": "VEGETATION.path_veg_kc",
        "Soil land use": "VEGETATION.path_veg_lulc",
        "Soil porosity: porosity": "UNSATURATED.path_uz_theta_sat",
        "Theta residual": "UNSATURATED.path_uz_theta_res",
        "Available Water content (AWC)": "UNSATURATED.path_uz_theta_awc",
        "Wilting Point (wp)": "UNSATURATED.path_uz_theta_wp",
        "Soil Depth (D)": "UNSATURATED.path_uz_root",
        "Soi particle distribution parameter (b)": "UNSATURATED.path_uz_lambda",
        "Soil suction head": "UNSATURATED.path_uz_psi",
        "Saturated hydraulic conductivity": "UNSATURATED.path_uz_ksat",
        "sigma_Ksat": "UNSATURATED.path_uz_sigmaksat",
        "Initial soil water content": "UNSATURATED.path_uz_theta",
        "Channel saturated hydraulic conductivity": "UNSATURATED.path_riv_ksat",
        "Groundwater Boundary condition (domain)": "SATURATED.path_sz_mask",
        "Aquifer Sat. Hydraulic Conductivity (Ksat_aq)": "SATURATED.path_sz_ksat",
        "Specific Yield": "SATURATED.path_sz_sy",
        "Initial Conditions Water table elevation": "SATURATED.path_sz_wte",
        "Flux Boundary Conditions": "SATURATED.path_sz_bc_flux",
        "Head Boundary Conditions": "SATURATED.path_sz_bc_head",
        "Aquifer bottom elevation": "SATURATED.path_sz_bottom",
        "Precipitation": "METEO.path_pre",
        "Potential Evapotranspiration": "METEO.path_pet",
        "Water abstractions file": "METEO.path_aof",
        "Discharge point results": "OUTPUT.path_out_sz",
        "Soil point results output": "OUTPUT.path_out_uz",
        "Groundwater point results": "OUTPUT.path_out_oz",
        "Folder location results": "OUTPUT.path_output",
        "MODEL PARAMETER SETTINGS FILE": "OUTPUT.path_setting",
        "GROUNDWATER ADITIONAL PARAMETER FILES": "OUTPUT.path_gw_settings",
        "INTERCEPTION MODEL": "OUTPUT.path_vg_settings",
        "RIPARIAN PROPERTIES": "OUTPUT.path_rp_settings",
        "BOUNDARY CONDITIONS OF": "OUTPUT.path_of_settings",
        "DATASET PROJECTIONS AND COORDINANTES": "OUTPUT.path_projection"
    }

    mappings_settings = {
        2: "SETTINGS.start_date",
        4: "SETTINGS.end_date",
        6: "SETTINGS.dt_of",
        8: "SETTINGS.dt_gw",
        13: "READING.data_read",
        15: "READING.data_step",
        17: "READING.data_reproject",
        19: "READING.data_interp",
        22: "COMPONENTS.method_inf",
        24: "COMPONENTS.method_gw",
        26: "COMPONENTS.not used 1",
        28: "COMPONENTS.not used 2",
        33: "OUTPUT.output_csv",
        35: "OUTPUT.output_grid",
        39: "OUTPUT.Save discharge in volumetric rate units",
        46: "GLOBAL_FACTORS.uz_kdt",
        48: "GLOBAL_FACTORS.uz_kdroot",
        50: "GLOBAL_FACTORS.uz_kawc",
        52: "GLOBAL_FACTORS.uz_kkast",
        54: "GLOBAL_FACTORS.uz_ksigma",
        56: "GLOBAL_FACTORS.riv_kksat",
        58: "GLOBAL_FACTORS.riv_kdecay",
        60: "GLOBAL_FACTORS.riv_kwidth",
        62: "GLOBAL_FACTORS.sz_kksat",
        64: "GLOBAL_FACTORS.sz_ksy"
    }

    def clean_key(key):
        # Remove extraneous characters from the key
        key = re.sub(r'[-=]+.*', '', key).strip()
        return key

    def parse_dryland(lines, json_structure, mappings):
        key = None
        for line in lines:
            line = line.strip()

            if line.endswith(':'):
                # This is a key line
                key = line[:-1].strip()

            elif key:
                # This is the value line
                value = line.strip()
                if value.lower() == 'none':
                    value = None

                # Find the corresponding JSON path and update it
                key = clean_key(key)
                if key in mappings:
                    json_key = mappings[key]
                    keys = json_key.split('.')
                    d = json_structure
                    for k in keys[:-1]:
                        d = d[k]

                    if key == "MODEL PARAMETER SETTINGS FILE":
                        base_name, _ = os.path.splitext(value)
                        value = base_name + ".json"
                    d[keys[-1]] = value

                key = None

    def parse_settings(lines, json_structure, mappings):
        iterator = iter(lines)
        
        for line in iterator:
            
            line = line.strip()

            # Skip header lines
            if line.startswith("DWAPM_SET") or line.startswith("========"):
                continue
            
            # Check if the line ends with a number in brackets
            
            match = re.match(r'(.*?)(?:\((\d+)\))$', line)
            if match:
                key = int(match.group(2))  # Extract the number in brackets as the key
                # Extract the key part before the number in brackets
                description = match.group(1).strip()
                
                # Look for the value on the next line
                try:
                    value_line = next(iterator).strip()
                    if value_line.lower() == 'none':
                        value = None
                    else:
                        value = value_line.strip()
                        
                    # Find the corresponding JSON path and update it
                    if key in mappings:
                        json_key = mappings[key]
                        keys = json_key.split('.')
                        d = json_structure
                        for k in keys[:-1]:
                            d = d[k]
                        d[keys[-1]] = value
                except StopIteration:
                    # Handle the case where there is no following line for value
                    pass

        return json_structure


    # Read the input text file
    with open(input_file, 'r') as file:
        lines = file.readlines()

    # Determine which format the file is in
    first_line = lines[0].strip()
    print(f'Format determined: {first_line}')

    if first_line == "DWAPM_SET":
        # Settings file format
        parse_settings(iter(lines), json_structure_settings, mappings_settings)
        json_structure = json_structure_settings
    elif first_line == "drylandmodel":
        # Dryland model file format
        parse_dryland(lines, json_structure_dryland, mappings_dryland)
        json_structure = json_structure_dryland
    else:
        print(f'{input_file} format not available for conversion')
        return

    # Set the output file if not provided
    if output_file is None:
        output_file = os.path.splitext(input_file)[0] + '.json'

    # Save the JSON structure to a file
    try:
        with open(output_file, 'w') as file:
            json.dump(json_structure, file, indent=4)
            print(f'Successfully saved JSON to {output_file}')
        
        # Remove the old input file after successful conversion
        os.remove(input_file)
        print(f'Successfully deleted the old file: {input_file}')
        
    except Exception as e:
        print(f'Failed to save JSON or delete old file. Error: {e}')


if __name__ == "__main__":

    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python -m path.to.your.module <input_file> [output_file]")
    else:
        input_file = sys.argv[1]
        
        if len(sys.argv) == 3:
            output_file = sys.argv[2]
        else:
            output_file = None

        convert_text_to_json(input_file, output_file)

