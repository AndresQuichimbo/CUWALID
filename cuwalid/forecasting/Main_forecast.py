import json
from cuwalid.forecasting.components.N00_cuwalid_HAD_get_csv_TS_files_from_multi_CSV import get_csv_TS_files_from_multi_CSV
from cuwalid.forecasting.components.N01a_cuwalid_HAD_get_TWSA_from_mult_files import get_TWSA_from_mult_files
from cuwalid.forecasting.components.N01b_cuwalid_HAD_get_additional_variables_multi_netcdf import get_additional_variables_multi_netcdf
from cuwalid.forecasting.components.N02a_cuwalid_HAD_get_percentiles_multi_files import get_percentiles_multi_files
from cuwalid.forecasting.components.N02c_cuwalid_HAD_get_extremes_quantiles_multi_netcdf import get_extremes_quantiles_multi_netcdf
from cuwalid.forecasting.components.N02d_cuwalid_HAD_get_average_multi_netcdf import get_average_multi_netcdf
from cuwalid.forecasting.components.N03_cuwalid_HAD_get_anomalies_multi_netcdf import get_anomalies_multi_netcdf
from cuwalid.forecasting.components.N04a_cuwalid_HAD_get_tercile_hindcast_fluxes import get_tercile_hindcast_fluxes
from cuwalid.forecasting.components.N04b_cuwalid_HAD_get_tercile_hindcast_extreme_values import get_tercile_hindcast_extreme_values
from cuwalid.forecasting.components.N05_cuwalid_HAD_extract_forecasting_variable import extract_forecasting_variable
from cuwalid.forecasting.components.N06_cuwalid_HAD_get_areas_terciles import get_areas_terciles
from cuwalid.forecasting.components.N07_cuwalid_HAD_get_update_TWSA import get_update_TWSA
from cuwalid.forecasting.components.N08_cuwalid_HAD_get_updated_TWSA_ensamble import get_updated_TWSA_ensamble
from cuwalid.forecasting.components.N09_cuwalid_HAD_get_ensamble_forecasting import get_ensamble_forecasting
from cuwalid.forecasting.components.N10a_cuwalid_HAD_get_probabilistic_tercile_forecast_ensamble import get_probabilistic_tercile_forecast_ensamble
from cuwalid.forecasting.components.N10b_cuwalid_HAD_get_deterministic_forecast_ensamble import get_deterministic_forecast_ensamble
from cuwalid.forecasting.components.N11a_cuwalid_HAD_plot_tercile_probability_forecast import plot_tercile_probability_forecast
from cuwalid.forecasting.components.N11b_cuwalid_HAD_plot_deterministic_forecast import plot_deterministic_forecast

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
        # Run N00_cuwalid_HAD_get_csv_TS_files_from_multi_CSV code
        get_csv_TS_files_from_multi_CSV(model_path, hindcast_model_name, start_year, end_year)

        print("test 2")
        # Run N01a_cuwalid_HAD_get_TWSA_from_mult_files code
        get_TWSA_from_mult_files(model_path, hindcast_model_name, start_year, end_year)

        print("test 3")
        # Run N01b_cuwalid_HAD_get_additional_variables_multi_netcdf code
        get_additional_variables_multi_netcdf(model_path, hindcast_model_name, start_year, end_year)

        print("test 5")
        # Run N02a_cuwalid_HAD_get_percentiles_multi_files code
        get_percentiles_multi_files(model_path, hindcast_model_name, start_year, end_year, season, variables, postpp_path)

        print("test 6")
        # Run N02c_cuwalid_HAD_get_extremes_quantiles_multi_netcdf code
        get_extremes_quantiles_multi_netcdf(model_path, hindcast_model_name, start_year, end_year, season, variables, postpp_path)

        print("test 7")
        # Run N02d_cuwalid_HAD_get_average_multi_netcdf code
        get_average_multi_netcdf(model_path, hindcast_model_name, start_year, end_year, season, variables, postpp_path)

        print("test 8")
        # Run N03_cuwalid_HAD_get_anomalies_multi_netcdf code
        get_anomalies_multi_netcdf(model_path, hindcast_model_name, start_year, end_year, season, variables, postpp_path)


    # ----------------------FORECASTING-----------------------    

    if include_forecast:

        print("Running forecasting")

        # Getting forecast config
        forecast_model_name = config['forecast_model_name']

        print("test 9")
        # Run N04a_cuwalid_HAD_get_tercile_hindcast_fluxes code
        get_tercile_hindcast_fluxes(model_path, forecast_model_name, season, variables, postpp_path)

        print("test 10")
        # Run N04b_cuwalid_HAD_get_tercile_hindcast_extreme_values code
        get_tercile_hindcast_extreme_values(model_path, forecast_model_name, season, variables, postpp_path)

        print("test 11")
        # Run N05_cuwalid_HAD_extract_forecasting_variable code
        extract_forecasting_variable(model_path, forecast_model_name, season, variables, postpp_path)

        print("test 12")
        # Run N06_cuwalid_HAD_get_areas_terciles code    
        get_areas_terciles(model_path, forecast_model_name, season, variables, postpp_path)

        print("test 13")
        # Run N07_cuwalid_HAD_get_update_TWSA code    
        get_update_TWSA(model_path, forecast_model_name)

        print("test 14")
        # Run N08_cuwalid_HAD_get_updated_TWSA_ensamble code    
        get_updated_TWSA_ensamble(model_path, forecast_model_name)

        print("test 15")
        # Run N09_cuwalid_HAD_get_ensamble_forecasting code    
        get_ensamble_forecasting(model_path, forecast_model_name, variables, postpp_path)

        print("test 16")
        # Run N10a_cuwalid_HAD_get_probabilistic_tercile_forecast_ensamble code    
        get_probabilistic_tercile_forecast_ensamble(model_path, forecast_model_name, season, variables, postpp_path)

        print("test 17")
        # Run N10b_cuwalid_HAD_get_deterministic_forecast_ensamble code
        get_deterministic_forecast_ensamble(model_path, forecast_model_name, season, variables, postpp_path)


    # ----------------------PLOTTING-----------------------

    if include_plotting:

        print("Running plotting")

        print("test 18")
        # Run N11a_cuwalid_HAD_plot_tercile_probability_forecast code
        plot_tercile_probability_forecast(model_path, forecast_model_name, season, variables, postpp_path)

        print("test 19")
        # Run N11b_cuwalid_HAD_plot_deterministic_forecast code
        plot_deterministic_forecast(model_path, forecast_model_name, season, variables, postpp_path)


