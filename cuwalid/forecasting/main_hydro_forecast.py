import argparse
import json
from cuwalid.forecasting.components.helper_functions import load_config
from cuwalid.forecasting.components.hindcast import *
from cuwalid.forecasting.components.forecast import *
from cuwalid.forecasting.components.plot_hydro_forecast import *

def run_hydro_forecast(config_file):
    """
    This function run the forecasting analysis, if historical analyais has
    not been activated, the forecasting will use results specified in the
    model path files.
    """

    # Load configuration file
    if type(config_path) == str:
        config = load_config(config_path)
    else:
        config = config_path

    ## Load JSON data from the config_path
    #with open(config_path, 'r') as file:
    #    config = json.load(file)

    include_hincast = config["run_historical"]
    include_forecast = config["run_forecast"]
    include_plotting = config["run_plotting"]
    multi_files = config["multi_files"]

    # read historical paths
    historical_model_name = config["historical"]['model_name']
    historical_model_path = config["historical"]['model_path']
    historical_postpp_path = config["historical"]['postpp_path']
    
    # read forecasting parameters
    forecast_model_name = config["forecasting"]['model_name']
    forecast_model_path = config["forecasting"]['model_path']
    forecast_postpp_path = config["forecasting"]['postpp_path']
    
    #/home/cuwalid/training/historical/regional/postpp/netcdf/HAD_IMERGcv_sim83_MAM_extremes_quantiles.nc
    #/home/cuwalid/training/historical/regional/postpp/netcdf/HAD_IMERGcv_sim83_OND_mean.nc
    #/home/cuwalid/training/historical/regional/postpp/netcdf/HAD_IMERGcv_sim83_OND_quantiles.nc

    #threshold_path = config["threshold_path"]
    threshold_path = os.path.join(historical_postpp_path, "netcdf", historical_model_name + "_SSS_extremes_quantiles.nc")
    season = config['season']
    start_year = config['start_year']
    end_year = config['end_year']
    variables = config['variables']
    iyear = config["year"]
    nsim = config["nsim"]


    # ----------------------HINDCAST-----------------------

    if include_hincast:

        print("========================== Processing historical simulation ==========================")
        print("WARNING: A new folder will '/netcdf/' will be created inside '/postpp/'")
        print("to store new variables if it does not exist")
              
        # check if folder exist postpp/netcdf
        # print("to store new variables if it does not exist")

        # Getting hindcast configuration
        #hindcast_model_name = config['run_historical']
        
        if multi_files is True:
            print("******Processing yearly-files of model outputs******")

            print("Step 1: Concatenate multiple csv historical files")
            get_csv_TS_files_from_multi_CSV(historical_model_path,
                                            historical_model_name, start_year, end_year)

            print("Step 2: Processing TWSA from storage change")
            get_TWSA_from_mult_files(historical_model_path,
                                     historical_model_name, start_year, end_year)

            print("Step 3: Processing WRSI")
            get_additional_variables_multi_netcdf(historical_model_path,
                                                  historical_model_name, start_year, end_year)

            print("Step 4: Getting monthly mean values for all variables")
            get_monthly_average_multi_netcdf(historical_model_path,
                                             historical_model_name,
                                             start_year, end_year, variables,
                                             historical_postpp_path)

            print("Step 5: Getting terciles from historical simulations")
            get_percentiles_multi_files(historical_model_path,
                                        historical_model_name,
                                        start_year, end_year, season, variables,
                                        historical_postpp_path)

            #print("Step 6: Getting quatiles 05, 33, 50, 66, 95 form historical simulations")
            #get_extremes_quantiles_multi_netcdf(historical_model_path,
            #                                    historical_model_name,
            #                                    start_year, end_year, season, variables,
            #                                    historical_postpp_path)

            print("Step 6: Getting average values from historical simualations")
            get_average_multi_netcdf(historical_model_path,
                                     historical_model_name,
                                     start_year, end_year, season, variables,
                                     historical_postpp_path)

            #print("Step 7: Getting anomalies from historical simulations")
            #get_anomalies_multi_netcdf(historical_model_path,
            #                           historical_model_name,
            #                           start_year, end_year, season, variables,
            #                           historical_postpp_path)


    # ----------------------FORECASTING-----------------------    

    if include_forecast:

        print("================================ Running forecasting ================================")
        print("WARINING! before runing the forecast make sure the historical analysis has been")
        print("performed before. There is no need to perform the historical analysis if there ")
        print("is not updates on the historical simulations")
        # check if folder exist postpp/netcdf
        # print("to store new variables if it does not exist")

        # Getting forecast config
        #forecast_model_name = config['forecast_model_name']

        #print("Step 9")
        #get_tercile_hindcast_fluxes(model_path, forecast_model_name, season, variables, postpp_path)

        #print("Step 10")
        #get_tercile_hindcast_extreme_values(model_path, forecast_model_name, season, variables, postpp_path)

        # this function will be moved to another file, this ones corresponds
        # to the impact forecasting not to the hydrological forecasting
        #print("Step 11")
        # function to get netcdf files from regional files at each selected place
        #extract_forecasting_variable(model_path, forecast_model_name, season, variables, postpp_path)

        #print("Step 12")
        # funtion to calculate areas for county provided in the list
        #get_areas_terciles(model_path, forecast_model_name, season, variables, postpp_path)

        #print("Step 1: Update TWSA") 
        #get_update_TWSA(historical_model_path, historical_model_name, iyear=iyear)
        print("Step 1: Processing hydrological realizations") 
        get_postprocessed_variables_forecast(forecast_model_path, forecast_model_name)

        print("Step 2: Update TWSA of hydrological realizations") 
        for iseason in season:
            get_updated_TWSA_ensamble(forecast_model_path, forecast_model_name,
                                  historical_model_name,
                                  historical_postpp_path,
                                  season=iseason, iyear=iyear)
        
        print("Step 3: Creating ensamble of hydrological realizations")   
        get_ensamble_forecasting(forecast_model_path,
                                 forecast_model_name, variables, season,
                                 forecast_postpp_path)

        # Forecasting estimation
        print("Step 4: Processing probabilistic forecasting")  
        get_probabilistic_tercile_forecast_ensamble(forecast_model_path,
                                                    forecast_model_name, season, variables,
                                                    forecast_postpp_path,
                                                    threshold_path, iyear=iyear)

        print("Step 5: Processing deterministic forecasting")
        get_deterministic_forecast_ensamble(forecast_model_path,
                                            forecast_model_name, season, variables,
                                            forecast_postpp_path,
                                            threshold_path, iyear=iyear)


    # ----------------------PLOTTING-----------------------

    if include_plotting:

        print("============================== Ploting forecasting outputs ==============================")

        print("Step 1: Plot probabilistic tercile forecasting")
        plot_tercile_probability_forecast(forecast_model_path,
                                          forecast_model_name, season, variables,
                                          forecast_postpp_path,
                                          iyear=iyear
                                          )

        #print("Step 2: Plot deterministic forecasting")
        #plot_deterministic_forecast(forecast_model_path,
        #                            forecast_model_name, season, variables,
        #                            forecast_postpp_path
        #                            )


# Main function to handle command-line arguments
if __name__ == '__main__':
	# Set up argument parser to get the JSON config file from command line
	parser = argparse.ArgumentParser(description="Plot hydrological forecast based on JSON configuration.")
	parser.add_argument('config_file', type=str, help='Path to the JSON configuration file')

	# Parse command line arguments
	args = parser.parse_args()

	# Run the plot_maps_json function with the config file provided by the user
	run_hydro_forecast(args.config_file)