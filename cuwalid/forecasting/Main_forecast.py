import json
from cuwalid.forecasting.components.hindcast import *
from cuwalid.forecasting.components.forecast import *
from cuwalid.forecasting.components.plotting import *

def run_forecast(config_path):

    # Load JSON data from the config_path
    with open(config_path, 'r') as file:
        config = json.load(file)

    include_hincast = config["run_hindcast"]
    include_forecast = config["run_forecast"]
    include_plotting = config["run_plotting"]

    model_path = config['model_path']
    postpp_path = config['postpp_path']
    season = config['season']
    start_year = config['start_year']
    end_year = config['end_year']
    variables = config['variables']

    # ----------------------HINDCAST-----------------------

    if include_hincast:

        print("Running hindcast")

        # Getting hindcast configuration
        hindcast_model_name = config['hindcast_model_name']
        

        print("test 1")
        get_csv_TS_files_from_multi_CSV(model_path, hindcast_model_name, start_year, end_year)

        print("test 2")
        get_TWSA_from_mult_files(model_path, hindcast_model_name, start_year, end_year)

        print("test 3")
        get_additional_variables_multi_netcdf(model_path, hindcast_model_name, start_year, end_year)

        print("test 5")
        get_percentiles_multi_files(model_path, hindcast_model_name, start_year, end_year, season, variables, postpp_path)

        print("test 6")
        get_extremes_quantiles_multi_netcdf(model_path, hindcast_model_name, start_year, end_year, season, variables, postpp_path)

        print("test 7")
        get_average_multi_netcdf(model_path, hindcast_model_name, start_year, end_year, season, variables, postpp_path)

        print("test 8")
        get_anomalies_multi_netcdf(model_path, hindcast_model_name, start_year, end_year, season, variables, postpp_path)


    # ----------------------FORECASTING-----------------------    

    if include_forecast:

        print("Running forecasting")

        # Getting forecast config
        forecast_model_name = config['forecast_model_name']

        print("test 9")
        get_tercile_hindcast_fluxes(model_path, forecast_model_name, season, variables, postpp_path)

        print("test 10")
        get_tercile_hindcast_extreme_values(model_path, forecast_model_name, season, variables, postpp_path)

        print("test 11")
        extract_forecasting_variable(model_path, forecast_model_name, season, variables, postpp_path)

        print("test 12")
        get_areas_terciles(model_path, forecast_model_name, season, variables, postpp_path)

        print("test 13") 
        get_update_TWSA(model_path, forecast_model_name)

        print("test 14") 
        get_updated_TWSA_ensamble(model_path, forecast_model_name)

        print("test 15")   
        get_ensamble_forecasting(model_path, forecast_model_name, variables, postpp_path)

        print("test 16")  
        get_probabilistic_tercile_forecast_ensamble(model_path, forecast_model_name, season, variables, postpp_path)

        print("test 17")
        get_deterministic_forecast_ensamble(model_path, forecast_model_name, season, variables, postpp_path)


    # ----------------------PLOTTING-----------------------

    if include_plotting:

        print("Running plotting")

        print("test 18")
        plot_tercile_probability_forecast(model_path, forecast_model_name, season, variables, postpp_path)

        print("test 19")
        plot_deterministic_forecast(model_path, forecast_model_name, season, variables, postpp_path)


