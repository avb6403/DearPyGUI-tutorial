import dearpygui.dearpygui as dpg
import dearpygui.demo as demo

dpg.create_context()
dpg.create_viewport(title='Custom Title', width=600, height=600)

# Set global font scale to increase element sizes
dpg.set_global_font_scale(4.0)  # Adjust this value (e.g., 1.5, 2.0) for larger fonts and elements

demo.show_demo()

dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
