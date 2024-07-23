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

    # ----------------------HINDCAST-----------------------

    if include_hincast:

        print("Running hindcast")

        # Getting hindcast configuration
        hindcast_model_name = config['hindcast_model_name']
        hindcast_model_path = config['hindcast_model_path']
        hindcast_postpp_path = config['hindcast_postpp_path']
        hindcast_season = config['hindcast_season']
        hindcast_start_year = config['hindcast_start_year']
        hindcast_end_year = config['hindcast_end_year']
        hindcast_variables = config['hindcast_variables']

        # Run N00_cuwalid_HAD_get_csv_TS_files_from_multi_CSV code
        get_csv_TS_files_from_multi_CSV(hindcast_model_name, hindcast_model_path, hindcast_start_year, hindcast_end_year)

        # Run N01a_cuwalid_HAD_get_TWSA_from_mult_files code
        get_TWSA_from_mult_files(hindcast_model_name, hindcast_model_path, hindcast_start_year, hindcast_end_year)

        # Run N01b_cuwalid_HAD_get_additional_variables_multi_netcdf code
        get_additional_variables_multi_netcdf(hindcast_model_name, hindcast_model_path, hindcast_start_year, hindcast_end_year)

        # Run N02a_cuwalid_HAD_get_percentiles_multi_files code
        get_percentiles_multi_files(hindcast_model_path, hindcast_model_name, hindcast_start_year, hindcast_end_year, hindcast_season, hindcast_variables, hindcast_postpp_path)

        # Run N02c_cuwalid_HAD_get_extremes_quantiles_multi_netcdf code
        get_extremes_quantiles_multi_netcdf(hindcast_model_path, hindcast_model_name, hindcast_start_year, hindcast_end_year, hindcast_season, hindcast_variables, hindcast_postpp_path)

        # Run N02d_cuwalid_HAD_get_average_multi_netcdf code
        get_average_multi_netcdf(hindcast_model_path, hindcast_model_name, hindcast_start_year, hindcast_end_year, hindcast_season, hindcast_variables, hindcast_postpp_path)

        # Run N03_cuwalid_HAD_get_anomalies_multi_netcdf code
        get_anomalies_multi_netcdf(hindcast_model_path, hindcast_model_name, hindcast_start_year, hindcast_end_year, hindcast_season, hindcast_variables, hindcast_postpp_path)


    # ----------------------FORECASTING-----------------------    

    if include_forecast:

        print("Running forecasting")

        # Getting forecast config
        forecast_model_name = config['forecast_model_name']
        forecast_model_path = config['forecast_model_path']
        forecast_postpp_path = config['forecast_postpp_path']
        forecast_threshold_path = config['forecast_threshold_path']
        forecast_season = config['forecast_season']
        forecast_start_year = config['forecast_start_year']
        forecast_end_year = config['forecast_end_year']
        forecast_variables = config['forecast_variables']

        # Run N04a_cuwalid_HAD_get_tercile_hindcast_fluxes code
        get_tercile_hindcast_fluxes(forecast_model_path, forecast_model_name, forecast_variables, forecast_postpp_path)

        # Run N04b_cuwalid_HAD_get_tercile_hindcast_extreme_values code
        get_tercile_hindcast_extreme_values(forecast_model_path, forecast_model_name, forecast_season, forecast_postpp_path)

        # Run N05_cuwalid_HAD_extract_forecasting_variable code
        extract_forecasting_variable(forecast_model_path, forecast_model_name, forecast_season, forecast_postpp_path)

        # Run N06_cuwalid_HAD_get_areas_terciles code    
        get_areas_terciles(forecast_model_path, forecast_model_name, forecast_season, forecast_postpp_path)

        # Run N07_cuwalid_HAD_get_update_TWSA code    
        get_update_TWSA(forecast_model_path, forecast_model_name)

        # Run N08_cuwalid_HAD_get_updated_TWSA_ensamble code    
        get_updated_TWSA_ensamble(forecast_model_path, forecast_model_name)

        # Run N09_cuwalid_HAD_get_ensamble_forecasting code    
        get_ensamble_forecasting(forecast_model_path, forecast_model_name, forecast_variables, forecast_postpp_path)

        # Run N10a_cuwalid_HAD_get_probabilistic_tercile_forecast_ensamble code    
        get_probabilistic_tercile_forecast_ensamble(forecast_model_path, forecast_model_name, forecast_season, forecast_variables, forecast_postpp_path)

        # Run N10b_cuwalid_HAD_get_deterministic_forecast_ensamble code
        get_deterministic_forecast_ensamble(forecast_model_path, forecast_model_name, forecast_season, forecast_variables, forecast_postpp_path)


    # ----------------------PLOTTING-----------------------

    if include_plotting:

        print("Running plotting")

        # Getting plotting config
        plot_cuwalid_model_name = config['plot_cuwalid_model_name']
        plot_cuwalid_model_path = config['plot_cuwalid_model_path']
        plot_cuwalid_postpp_path = config['plot_cuwalid_postpp_path']
        plot_cuwalid_season = config['plot_cuwalid_season']
        plot_cuwalid_start_year = config['plot_cuwalid_start_year']
        plot_cuwalid_end_year = config['plot_cuwalid_end_year']
        plot_cuwalid_variables = config['plot_cuwalid_variables']

        # Run N11a_cuwalid_HAD_plot_tercile_probability_forecast code
        plot_tercile_probability_forecast(plot_cuwalid_model_path, plot_cuwalid_model_name, plot_cuwalid_season, plot_cuwalid_variables, plot_cuwalid_postpp_path)

        # Run N11b_cuwalid_HAD_plot_deterministic_forecast code
        plot_deterministic_forecast(plot_cuwalid_model_path, plot_cuwalid_model_name, plot_cuwalid_season, plot_cuwalid_variables, plot_cuwalid_postpp_path)


