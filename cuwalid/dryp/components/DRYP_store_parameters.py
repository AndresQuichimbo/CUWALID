import os
import ast

class get_store_parameters(object):
    """Setting model input varables and environmental states
    """
    def __init__(self, fname):
        
        if fname != None and os.path.exists(fname):
            # read variables for grided dataset
            self.var_grid = reading(fname)["store_var_grid"]

            # read variables for grided dataset
            self.var_point = reading(fname)["store_var_point"]

            # read variables for grided dataset
            self.var_avg = reading(fname)["store_var_avg"]

            # read variables for grided dataset for lakes
            self.var_grid_rp = reading(fname)["store_var_grid_rp"]
    
            # read variables for grided dataset for lakes
            self.var_grid_pnd = reading(fname)["store_var_grid_pnd"]

            # read variables for grided dataset for lakes
            self.var_grid_lks = reading(fname)["store_var_grid_lks"]


        else:
            print("Store variable option not provided, default parameters applied")
	        # variables for grided dataset
            self.var_grid = {'pre': True, 'pet': True, 'run': True,
                'aet': True, 'inf': True, 'tht': True,
                'rch': True, 'egw': True, 'wte': True,
                'gdh': True, 'twsc': True, 'chb': True,
                'tls': True}
            
            # variables for grided dataset
            self.var_point = {'aet': True, 'inf': True, 'dis': True,
                 'tht': True, 'rch': True, 'wte': True,
                 'gdh': True, 'ssz': True}

            # variables for grided dataset
            self.var_avg = {'pre': True, 'pet': True, 'run': True,
                 'aet': True, 'inf': True, 'tht': True,
                 'rch': True, 'egw': True, 'wte': True,
                 'gdh': True, 'twsc': True, 'chb': True,
                 'tls': True}

            # variables for grided dataset
            self.var_grid_rp = {'aet': True, 'fch': True, 'tls': True,
                   'tht': True, 'ssz': True}
    
            # variables for grided dataset
            self.var_grid_pnd = {'epd': True, 'vpd': True, 'aoz': True,
                   #'tht': True, 'ssz': True,
                   }
            # variables for grided dataset
            self.var_grid_lks = {'slks': True,# 'vpd': True, 'aoz': True,
                   #'tht': True, 'ssz': True,
                   }


def reading(fname):
    s = open(fname, 'r').read()
    return ast.literal_eval(s)