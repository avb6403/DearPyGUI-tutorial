import dearpygui.dearpygui as dpg
import json
import yaml
import tkinter as tk
import os
from datetime import datetime
import socket
import threading

# Socket settings
HOST = '127.0.0.1'  # Localhost
PORT = 65432        # Port of the server

# Flag to control live data fetching
stop_flag = False

# Detect screen resolution
def get_screen_resolution():
    """Retrieve the screen resolution for cross-platform systems."""
    root = tk.Tk()
    root.withdraw()  # Hide the Tkinter window
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    return screen_width, screen_height

# Function to receive data from the server
def fetch_live_data(fake_data_storage):
    global stop_flag
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((HOST, PORT))
        while not stop_flag:
            data = client_socket.recv(1024)  # Receive data from server
            if data:
                try:
                    # Decode JSON and re-serialize to ensure proper format
                    decoded_data = json.loads(data.decode('utf-8'))  # Decode JSON from server
                    serialized_data = json.dumps(decoded_data)  # Re-serialize the data
                    dpg.set_value(fake_data_storage, serialized_data)  # Store the serialized data
                    print(f"Received and stored data: {serialized_data}")  # Debug output
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON from server: {e}")
                
# Debugging: Add print statements to check data flow
def write_file(path, data, data_type):
    print(f"Writing {data_type.upper()} file to: {path}")
    print(f"Data: {data}")  # Debug: Print data to ensure it's not empty

    with open(path, "w") as f:
        if data_type == "json":
            json.dump(data, f, indent=4)
        elif data_type == "yaml":
            yaml.dump(data, f, default_flow_style=False)

    print(f"{data_type.upper()} file saved to: {path}")

# Save to a default folder with a timestamp
def save_to_default(data, data_type):
    default_folder = os.path.join(os.getcwd(), "data")
    os.makedirs(default_folder, exist_ok=True)  # Ensure the folder exists

    # Create a filename with a timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"output_{timestamp}.{data_type}"
    save_path = os.path.join(default_folder, file_name)

    # Write the file
    write_file(save_path, data, data_type)

# Export function
def export_data(data_type, use_default):
    # Retrieve serialized data stored in DearPyGUI
    raw_data_json = dpg.get_value("fake_data_storage")
    if not raw_data_json:
        print("Error: No data found in 'fake_data_storage'.")
        return

    # Deserialize the JSON string into Python objects
    raw_data = json.loads(raw_data_json)

    # Convert raw data to a structured format (list of dictionaries)
    example_data = {"regions": [{"x": x, "y": y} for x, y in raw_data]}

    if use_default:
        # Save to default folder with timestamp
        save_to_default(example_data, data_type)
    else:
        # Show DearPyGUI file dialog
        dpg.show_item(f"file_dialog_{data_type}")

# Callback to handle file dialog selection
def file_dialog_callback(sender, app_data, user_data):
    selected_path = app_data["file_path_name"]
    data_type = user_data

    # Retrieve serialized data stored in DearPyGUI
    raw_data_json = dpg.get_value("fake_data_storage")
    if not raw_data_json:
        print("Error: No data found in 'fake_data_storage'.")
        return

    # Deserialize the JSON string into Python objects
    raw_data = json.loads(raw_data_json)
    example_data = {"regions": [{"x": x, "y": y} for x, y in raw_data]}

    # Write the file
    write_file(selected_path, example_data, data_type)


# Callback to dynamically update the plot width
def update_plot_width(sender, app_data, user_data):
    dpg.set_item_width(user_data, app_data)
    update_button_positions(user_data)

# Callback to dynamically update the plot height
def update_plot_height(sender, app_data, user_data):
    dpg.set_item_height(user_data, app_data)
    update_button_positions(user_data)

# Dynamically update button positions based on plot position
def update_button_positions(plot_id):
    plot_pos = dpg.get_item_pos(plot_id)
    plot_left = plot_pos[0]  # Left edge of the plot
    plot_bottom = plot_pos[1] + dpg.get_item_height(plot_id)  # Bottom edge of the plot

    button_y_offset = 20  # Gap between plot and buttons
    button_y = plot_bottom + button_y_offset

    # Position buttons on the left
    dpg.set_item_pos("export_json_button", (plot_left, button_y))
    dpg.set_item_pos("export_yaml_button", (plot_left, button_y + 40))  # Offset below the first button

# Periodically update the plot
def periodic_update_plot(plot_id, fake_data_storage, interval=1.0):
    global update_flag
    while update_flag:
        time.sleep(interval)  # Wait for the specified interval
        # Call update_plot within the loop
        update_plot(None, None, (plot_id, fake_data_storage))

# Start periodic updates
def start_periodic_update(plot_id, fake_data_storage):
    global update_flag
    if not update_flag:  # Prevent multiple threads
        update_flag = True
        threading.Thread(
            target=periodic_update_plot,
            args=(plot_id, fake_data_storage),
            daemon=True
        ).start()
        print("Started periodic updates.")

# Stop periodic updates
def stop_periodic_update():
    global update_flag
    update_flag = False
    print("Stopped periodic updates.")

# Update plot function
def update_plot(sender, app_data, user_data):
    plot_id, fake_data_storage = user_data
    raw_data_json = dpg.get_value(fake_data_storage)  # Retrieve serialized JSON
    try:
        # Deserialize JSON string into Python objects
        data = json.loads(raw_data_json)
        x_data = [point["x"] for point in data]
        y_data = [point["y"] for point in data]
        dpg.configure_item(plot_id, x=x_data, y=y_data)
        print(f"Updated plot with data: {data}")  # Debug: Print the updated data
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
    except (KeyError, TypeError) as e:
        print(f"Error processing data: {e}")

# Main GUI
def main_gui(screen_width, screen_height):
    global stop_flag

    # Use a percentage of the screen for the window size
    window_width = int(screen_width * 1)
    window_height = int(screen_height * 1)

    # Add a value registry for storing data
    with dpg.value_registry():
        dpg.add_string_value(tag="fake_data_storage", default_value="[]")  # Initialize with an empty list

    # Create the main window
    with dpg.window(label="Main Window", width=window_width, height=window_height):
        # Use a percentage of the window size for the plot
        plot_width = int(window_width * 0.8)
        plot_height = int(window_height * 0.6)

        # Shift the plot to the left by reducing its x-coordinate
        plot_x_offset = 100  # Fixed offset to shift the plot left
        plot_x = max((window_width - plot_width) // 2 - plot_x_offset, 0)  # Ensure it doesn't go off-screen
        plot_y = (window_height - plot_height) // 3

        # Create a plot for displaying live data
        with dpg.plot(label="2D Plot", height=plot_height, width=plot_width, pos=(plot_x, plot_y), tag="main_plot") as plot_id:
            x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Battery Voltage (V)")
            y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="Temperature (°C)")
            scatter_series = dpg.add_scatter_series([], [], label="Live Data", parent=y_axis)

            # Set axis limits
            dpg.set_axis_limits(x_axis, 0, 5)
            dpg.set_axis_limits(y_axis, -20, 80)

        # Add buttons for exporting data
        dpg.add_button(label="Export to JSON", callback=lambda: export_data("json", False),
                       pos=(plot_x, plot_y + plot_height + 20), tag="export_json_button")
        dpg.add_button(label="Export to YAML", callback=lambda: export_data("yaml", False),
                       pos=(plot_x, plot_y + plot_height + 60), tag="export_yaml_button")

        # File dialogs
        with dpg.file_dialog(directory_selector=False, show=False, callback=file_dialog_callback, user_data="json", tag="file_dialog_json"):
            dpg.add_file_extension(".json", color=(255, 255, 0, 255))
            dpg.add_file_extension(".*")

        with dpg.file_dialog(directory_selector=False, show=False, callback=file_dialog_callback, user_data="yaml", tag="file_dialog_yaml"):
            dpg.add_file_extension(".yaml", color=(0, 255, 0, 255))
            dpg.add_file_extension(".*")

        # Add sliders for dynamic resizing to the left of the plot
        slider_x = plot_x - 300  # Position sliders 250px to the left of the plot
        slider_y = plot_y + 20  # Align sliders with the top of the plot

        # dpg.add_slider_int(label="Width", default_value=plot_width, min_value=400, max_value=3000,
        #                    callback=update_plot_width, user_data=plot_id, pos=(slider_x, slider_y), width=200)
        # dpg.add_slider_int(label="Height", default_value=plot_height, min_value=400, max_value=1500,
        #                    callback=update_plot_height, user_data=plot_id, pos=(slider_x, slider_y + 60), width=200)

        # # Add a button to start fetching live data
        # dpg.add_button(label="Start Live Data", callback=lambda: threading.Thread(
        #     target=fetch_live_data, args=("fake_data_storage",), daemon=True).start(),
        #                pos=(slider_x, slider_y + 120))

        # # Add a button to stop fetching live data
        # dpg.add_button(label="Stop Live Data", callback=stop_fetching_live_data, pos=(slider_x, slider_y + 160))

        # # # Add a button to manually refresh the plot
        # # dpg.add_button(label="Update Plot", callback=lambda: update_plot(None, None, (scatter_series, "fake_data_storage")),
        # #                pos=(slider_x, slider_y + 200))
        
        # # Add buttons to control updates
        # dpg.add_button(
        #     label="Start Periodic Update",
        #     callback=lambda: start_periodic_update(scatter_series, "fake_data_storage"),
        #     pos=(slider_x - 300, slider_y + 20)
        # )

        # dpg.add_button(
        #     label="Stop Periodic Update",
        #     callback=stop_periodic_update,
        #     pos=(slider_x - 300, slider_y + 60)
        # )
                # Add a group for layout organization
        with dpg.group(horizontal=False, pos=(slider_x, slider_y)):
            # Add sliders for dynamic resizing
            dpg.add_slider_int(
                label="Width",
                default_value=plot_width,
                min_value=400,
                max_value=3000,
                callback=update_plot_width,
                user_data=plot_id,
                width=200
            )
            dpg.add_slider_int(
                label="Height",
                default_value=plot_height,
                min_value=400,
                max_value=1500,
                callback=update_plot_height,
                user_data=plot_id,
                width=200
            )

            # Add buttons for live data
            dpg.add_button(
                label="Start Live Data",
                callback=lambda: threading.Thread(
                    target=fetch_live_data, args=("fake_data_storage",), daemon=True
                ).start()
            )
            dpg.add_button(
                label="Stop Live Data",
                callback=stop_fetching_live_data
            )

            # Add buttons to control updates
            dpg.add_button(
                label="Start Periodic Update",
                callback=lambda: start_periodic_update(scatter_series, "fake_data_storage")
            )
            dpg.add_button(
                label="Stop Periodic Update",
                callback=stop_periodic_update
            )

# Stop fetching live data
def stop_fetching_live_data():
    global stop_flag
    stop_flag = True
    print("Stopped fetching live data.")

# Entry Point
if __name__ == "__main__":
    # Get screen resolution dynamically
    screen_width, screen_height = get_screen_resolution()

    dpg.create_context()  # Initialize DearPyGUI context
    dpg.create_viewport(title="Example GUI", width=screen_width, height=screen_height)  # Match viewport to screen size
    dpg.setup_dearpygui()  # Setup DearPyGUI

    # Set global font scale for high-DPI screens
    scale_factor = screen_height / 1080  # Assuming 1080p is baseline
    dpg.set_global_font_scale(scale_factor)

    main_gui(screen_width, screen_height)

    dpg.show_viewport()
    dpg.start_dearpygui()  # Start the GUI loop
    dpg.destroy_context()  # Cleanup DearPyGUI resources
