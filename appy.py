from shiny import reactive, render
from shiny.express import ui, input
import random
from datetime import datetime
from collections import deque
import pandas as pd
import plotly.express as px
from shinywidgets import render_plotly
from scipy import stats
from faicons import icon_svg

UPDATE_INTERVAL_SECS: int = 3

DEQUE_SIZE: int = 5
reactive_value_wrapper = reactive.value(deque(maxlen=DEQUE_SIZE))

@reactive.calc()
def reactive_calc_combined():
    # Invalidate this calculation every UPDATE_INTERVAL_SECS to trigger updates
    reactive.invalidate_later(UPDATE_INTERVAL_SECS)

    # Data generation logic
    temp_celsius = round(random.uniform(-18, -16), 1)
    temp_fahrenheit = round((temp_celsius * 9/5) + 32, 1) # Convert to Fahrenheit
    temp_kelvin = round(temp_celsius + 273.15, 1) # Convert to Kelvin
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    new_dictionary_entry = {
        "temp_celsius": temp_celsius,
        "temp_fahrenheit": temp_fahrenheit,
        "temp_kelvin": temp_kelvin,
        "timestamp": timestamp
    }

    # get the deque and append the new entry
    reactive_value_wrapper.get().append(new_dictionary_entry)

    # Get a snapshot of the current deque for any further processing
    deque_snapshot = reactive_value_wrapper.get()

    # For Display: Convert deque to DataFrame for display
    df = pd.DataFrame(deque_snapshot)

    # For Display: Get the latest dictionary entry
    latest_dictionary_entry = new_dictionary_entry

    # Return a tuple with everything we need
    return deque_snapshot, df, latest_dictionary_entry


# Define the Shiny UI Page layout
ui.page_opts(title="PyShiny Express: Live Data Example", fillable=True)

# Define the sidebar
with ui.sidebar(open="open"):

    ui.h2("Antarctic Explorer", class_="text-center")
    ui.p(
        "A demonstration of real-time temperature readings in Antarctica.",
        class_="text-center",
    )

    # Use input_radio_buttons for temperature unit selection, adding Kelvin as an option
    ui.input_radio_buttons("temp_unit", 
                            label="Choose temperature unit", 
                            choices=["Celsius", "Fahrenheit", "Kelvin"], 
                            selected="Celsius")
    ui.hr()
    ui.h6("Links:")
ui.a(
        "GitHub Source",
        href="https://github.com/Thilde02/cintel-05-cintel",
        target="_blank",
    )
ui.a("PyShiny", href="https://shiny.posit.co/py/", target="_blank")
ui.a(
        "PyShiny Express",
        href="https://shiny.posit.co/blog/posts/shiny-express/",
        target="_blank",
    )

# Main content

with ui.navset_card_tab(id="tab"):
    with ui.nav_panel("Live Data"):
        with ui.value_box(
            showcase=icon_svg("thermometer"),
            theme="bg-gradient-purple-yellow"
        ): 
            "Current Temperature"

            @render.text
            def display_temp():
                """Get the latest reading and return temperature in Celsius, Fahrenheit, and Kelvin with dynamic message"""
                deque_snapshot, df, latest_dictionary_entry = reactive_calc_combined()

                # Get the selected temperature unit
                selected_unit = input.temp_unit()

                # Fetch the temperature in each unit
                celsius = latest_dictionary_entry['temp_celsius']
                fahrenheit = latest_dictionary_entry['temp_fahrenheit']
                kelvin = latest_dictionary_entry['temp_kelvin']

                # Logic to display the selected temperature unit
                if selected_unit == "Celsius":
                    temp_value = celsius
                    unit = "°C"
                elif selected_unit == "Fahrenheit":
                    temp_value = fahrenheit
                    unit = "°F"
                else:  # "Kelvin"
                    temp_value = kelvin
                    unit = "K"

                # Define the threshold temperature in Celsius (e.g., -17°C is the threshold for "warmer")
                threshold = -17

                # Determine if the temperature is warmer than usual
                if celsius > threshold:
                    temp_message = "It is warmer than usual"
                else:
                    temp_message = "It is colder than usual"

                # Return the formatted temperature display
                return f"{temp_value}{unit}. {temp_message}"


        with ui.value_box( 
            showcase=icon_svg("clock"),
            theme="bg-gradient-yellow-purple"
        ):
            "Current Date and Time"

            @render.text
            def display_time():
                """Get the latest reading and return a timestamp string"""
                deque_snapshot, df, latest_dictionary_entry = reactive_calc_combined()
                return f"{latest_dictionary_entry['timestamp']}"

        with ui.card(width="48%", height=500):
            ui.card_header("Most Recent Readings")

            @render.data_frame
            def display_df():
                """Get the latest reading and return a dataframe with current readings"""
                deque_snapshot, df, latest_dictionary_entry = reactive_calc_combined()
                pd.set_option('display.width', None)        # Use maximum width

                # Add the temperature columns
                df['temp_fahrenheit'] = df['temp_celsius'] * 9 / 5 + 32
                df['temp_kelvin'] = df['temp_celsius'] + 273.15

                # Round the values
                df['temp_celsius'] = df['temp_celsius'].round(1)
                df['temp_fahrenheit'] = df['temp_fahrenheit'].round(1)
                df['temp_kelvin'] = df['temp_kelvin'].round(1)

                return render.DataGrid(df,width="100%")

    with ui.nav_panel("Temperature Readings Plot"):
        # The function and decorator should be indented correctly within the block
        @render_plotly
        def display_plot():
            # Fetch from the reactive calc function
            deque_snapshot, df, latest_dictionary_entry = reactive_calc_combined()

            # Ensure the DataFrame is not empty before plotting
            if not df.empty:
                # Convert the 'timestamp' column to datetime for better plotting
                df["timestamp"] = pd.to_datetime(df["timestamp"])

                fig = px.scatter(df,
                                 x="timestamp",
                                 y="temp_celsius",
                                 title="Temperature Readings with Regression Line",
                                 labels={"temp_celsius": "Temperature (°C)", "timestamp": "Time"},
                                 color_discrete_sequence=["blue"])

                # For x, let's generate a sequence of integers from 0 to len(df)
                sequence = range(len(df))
                x_vals = list(sequence)
                y_vals = df["temp_celsius"]

                slope, intercept, r_value, p_value, std_err = stats.linregress(x_vals, y_vals)
                df['best_fit_line'] = [slope * x + intercept for x in x_vals]

                # Add the regression line to the figure
                fig.add_scatter(x=df["timestamp"], y=df['best_fit_line'], mode='lines', name='Regression Line')

                # Update layout as needed to customize further
                fig.update_layout(title="Temperature Readings with Regression Line",
                                  xaxis_title="Time", 
                                  yaxis_title="Temperature (°C, °F, K)",
                                  )

            return fig
