import dearpygui.dearpygui as dpg
import json
import yaml
import tkinter as tk
import os
from datetime import datetime
import socket
import threading
import time

# Socket settings
HOST = '127.0.0.1'  # Localhost
PORT = 65432        # Port of the server

# Flags for control
stop_flag = False
update_flag = False

# Detect screen resolution
def get_screen_resolution():
    """Retrieve the screen resolution for cross-platform systems."""
    root = tk.Tk()
    root.withdraw()  # Hide the Tkinter window
    return root.winfo_screenwidth(), root.winfo_screenheight()

# Fetch live data from the server
def fetch_live_data(fake_data_storage):
    global stop_flag
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        try:
            client_socket.connect((HOST, PORT))
            print(f"Connected to server at {HOST}:{PORT}")
            while not stop_flag:
                data = client_socket.recv(1024)  # Receive data from server
                if data:
                    try:
                        # Decode the received data
                        new_data = json.loads(data.decode('utf-8'))

                        # Retrieve existing data from fake_data_storage
                        existing_data_json = dpg.get_value(fake_data_storage)
                        existing_data = json.loads(existing_data_json)

                        # Append new data points
                        existing_data.extend(new_data)

                        # Save the updated list back to fake_data_storage
                        dpg.set_value(fake_data_storage, json.dumps(existing_data))

                        print(f"Received and accumulated data: {new_data}")
                    except json.JSONDecodeError as e:
                        print(f"Error decoding JSON: {e}")
        except Exception as e:
            print(f"Error fetching live data: {e}")

# Write data to a file
def write_file(path, data, data_type):
    with open(path, "w") as f:
        if data_type == "json":
            json.dump(data, f, indent=4)
        elif data_type == "yaml":
            yaml.dump(data, f, default_flow_style=False)
    print(f"{data_type.upper()} file saved to: {path}")

# Save to a default folder with a timestamp
def save_to_default(data, data_type):
    default_folder = os.path.join(os.getcwd(), "data")
    os.makedirs(default_folder, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_path = os.path.join(default_folder, f"output_{timestamp}.{data_type}")
    write_file(save_path, data, data_type)

# Export function
def export_data(data_type, use_default):
    raw_data_json = dpg.get_value("fake_data_storage")
    if not raw_data_json:
        print("Error: No data found in 'fake_data_storage'.")
        return
    try:
        raw_data = json.loads(raw_data_json)
        structured_data = {
            "metadata": {
                "export_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "source": "Live Data Feed"
            },
            "regions": [{"x": point["x"], "y": point["y"]} for point in raw_data]
        }
        if use_default:
            save_to_default(structured_data, data_type)
        else:
            dpg.show_item(f"file_dialog_{data_type}")
    except Exception as e:
        print(f"Error exporting data: {e}")

# File dialog callback
def file_dialog_callback(sender, app_data, user_data):
    selected_path = app_data["file_path_name"]
    data_type = user_data
    raw_data_json = dpg.get_value("fake_data_storage")
    try:
        raw_data = json.loads(raw_data_json)
        structured_data = {
            "metadata": {
                "export_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "source": "Live Data Feed"
            },
            "regions": [{"x": point["x"], "y": point["y"]} for point in raw_data]
        }
        write_file(selected_path, structured_data, data_type)
    except Exception as e:
        print(f"Error processing export: {e}")

# Periodically update the plot
def periodic_update_plot(plot_id, fake_data_storage, interval=1.0):
    global update_flag
    while update_flag:
        raw_data_json = dpg.get_value(fake_data_storage)
        if raw_data_json:
            data = json.loads(raw_data_json)
            x_data = [point["x"] for point in data]
            y_data = [point["y"] for point in data]
            dpg.configure_item(plot_id, x=x_data, y=y_data)
        time.sleep(interval)

# Start periodic updates
def start_periodic_update(plot_id, fake_data_storage):
    global update_flag
    if not update_flag:
        update_flag = True
        threading.Thread(target=periodic_update_plot, args=(plot_id, fake_data_storage), daemon=True).start()
        print("Started periodic updates.")

# Stop periodic updates
def stop_periodic_update():
    global update_flag
    update_flag = False
    print("Stopped periodic updates.")

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

# Main GUI
# def main_gui(screen_width, screen_height):
#     global stop_flag
#     window_width = int(screen_width * 1)
#     window_height = int(screen_height * 1)

#     # Add a value registry for storing data
#     with dpg.value_registry():
#         dpg.add_string_value(tag="fake_data_storage", default_value="[]")

#     # Create the main window
#     with dpg.window(label="Main Window", width=window_width, height=window_height):
#         plot_width = int(window_width * 0.8)
#         plot_height = int(window_height * 0.6)
#         plot_x = max((window_width - plot_width) // 2 - 100, 0)
#         plot_y = (window_height - plot_height) // 3

#         # Plot configuration
#         with dpg.plot(label="2D Plot", height=plot_height, width=plot_width, pos=(plot_x, plot_y), tag="main_plot") as plot_id:
#             x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Battery Voltage (V)")
#             y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="Temperature (°C)")
#             scatter_series = dpg.add_scatter_series([], [], label="Live Data", parent=y_axis)
#             dpg.set_axis_limits(x_axis, 0, 5)
#             dpg.set_axis_limits(y_axis, -20, 80)

#         slider_x = plot_x - 300
#         slider_y = plot_y + 20

#         # Layout for sliders and buttons
#     button_x_offset = 50  # Additional offset for buttons to move them left
#     with dpg.child_window(width=220, autosize_y=True, pos=(slider_x - button_x_offset, slider_y)):
#         dpg.add_slider_int(
#             label="Width",
#             default_value=plot_width,
#             min_value=400,
#             max_value=3000,
#             callback=update_plot_width,
#             user_data=plot_id,
#             width=200
#         )
#         dpg.add_slider_int(
#             label="Height",
#             default_value=plot_height,
#             min_value=400,
#             max_value=1500,
#             callback=update_plot_height,
#             user_data=plot_id,
#             width=200
#         )
#         dpg.add_button(
#             label="Start Live Data",
#             callback=lambda: threading.Thread(
#                 target=fetch_live_data, args=("fake_data_storage",), daemon=True
#             ).start()
#         )
#         dpg.add_button(
#             label="Stop Live Data",
#             callback=stop_fetching_live_data
#         )
#         dpg.add_button(
#             label="Start Periodic Update",
#             callback=lambda: start_periodic_update(scatter_series, "fake_data_storage")
#         )
#         dpg.add_button(
#             label="Stop Periodic Update",
#             callback=stop_periodic_update
#         )

#         # Add export buttons
#         dpg.add_button(label="Export to JSON", callback=lambda: export_data("json", False),
#                        pos=(plot_x, plot_y + plot_height + 20))
#         dpg.add_button(label="Export to YAML", callback=lambda: export_data("yaml", False),
#                        pos=(plot_x, plot_y + plot_height + 60))

#         # File dialogs
#         with dpg.file_dialog(directory_selector=False, show=False, callback=file_dialog_callback, user_data="json", tag="file_dialog_json"):
#             dpg.add_file_extension(".json", color=(255, 255, 0, 255))
#             dpg.add_file_extension(".*")

#         with dpg.file_dialog(directory_selector=False, show=False, callback=file_dialog_callback, user_data="yaml", tag="file_dialog_yaml"):
#             dpg.add_file_extension(".yaml", color=(0, 255, 0, 255))
#             dpg.add_file_extension(".*")

def main_gui(screen_width, screen_height):
    global stop_flag
    window_width = int(screen_width * 1)
    window_height = int(screen_height * 1)

    # Add a value registry for storing data
    with dpg.value_registry():
        dpg.add_string_value(tag="fake_data_storage", default_value="[]")

    # Create the main window
    with dpg.window(label="Main Window", width=window_width, height=window_height):
        plot_width = int(window_width * 0.8)
        plot_height = int(window_height * 0.6)
        plot_x = max((window_width - plot_width) // 2 - 100, 0)
        plot_y = (window_height - plot_height) // 3

        # Plot configuration
        with dpg.plot(label="2D Plot", height=plot_height, width=plot_width, pos=(plot_x, plot_y), tag="main_plot") as plot_id:
            x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="Battery Voltage (V)")
            y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="Temperature (°C)")
            scatter_series = dpg.add_scatter_series([], [], label="Live Data", parent=y_axis)
            dpg.set_axis_limits(x_axis, 0, 5)
            dpg.set_axis_limits(y_axis, -20, 80)

        # Adjusted layout for sliders and buttons
        slider_x = plot_x - 350
        slider_y = plot_y + 20
        button_x_offset = 100  # Additional offset for buttons to move them left

        # Add sliders and buttons in a child window for better layout control
        with dpg.child_window(width=400, autosize_y=True, pos=(slider_x - button_x_offset, slider_y), border=False):
            dpg.add_slider_int(
                label="Width",
                default_value=plot_width,
                min_value=400,
                max_value=3000,
                callback=update_plot_width,
                user_data=plot_id,
                width=300  # Ensure consistent width
            )
            dpg.add_spacer(height=10)  # Add space between widgets
            dpg.add_slider_int(
                label="Height",
                default_value=plot_height,
                min_value=400,
                max_value=1500,
                callback=update_plot_height,
                user_data=plot_id,
                width=300
            )
            dpg.add_spacer(height=20)  # Add more space for better separation
            dpg.add_button(
                label="Start Live Data",
                callback=lambda: threading.Thread(
                    target=fetch_live_data, args=("fake_data_storage",), daemon=True
                ).start(),
                width=300
            )
            dpg.add_spacer(height=10)  # Add space between buttons
            dpg.add_button(
                label="Stop Live Data",
                callback=stop_fetching_live_data,
                width=300
            )
            dpg.add_spacer(height=20)  # Larger space for grouping
            dpg.add_button(
                label="Start Periodic Update",
                callback=lambda: start_periodic_update(scatter_series, "fake_data_storage"),
                width=350
            )
            dpg.add_spacer(height=10)
            dpg.add_button(
                label="Stop Periodic Update",
                callback=stop_periodic_update,
                width=300
            )


        # Add export buttons, dynamically positioned below the plot
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

# Stop live data fetching
def stop_fetching_live_data():
    global stop_flag
    stop_flag = True
    print("Stopped fetching live data.")

# Entry point
if __name__ == "__main__":
    screen_width, screen_height = get_screen_resolution()
    dpg.create_context()
    dpg.create_viewport(title="Example GUI", width=screen_width, height=screen_height)
    dpg.setup_dearpygui()
    scale_factor = screen_height / 1080
    dpg.set_global_font_scale(scale_factor)
    main_gui(screen_width, screen_height)
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()
