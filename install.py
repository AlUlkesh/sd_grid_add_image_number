import launch

if not launch.is_installed("font-roboto"):
    launch.run_pip("install font-roboto", "font-roboto requirement for grid_add_image_number")

if not launch.is_installed("fonts"):
    launch.run_pip("install fonts", "fonts requirement for grid_add_image_number")
