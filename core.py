# _*_ coding: utf-8 _*_
# Author: GC Zhu
# Email: zhugc2016@gmail.com

import ctypes
import logging
import os
import platform

import numpy as np


class CalibrationResult:
    def __init__(self, status=0, fitting_error=0, sample_size=0):
        self.status = status
        self.fitting_error = fitting_error
        self.sample_size = sample_size

    def __str__(self):
        return str({
            'status': self.status,
            'fitting_error': self.fitting_error,
            'sample_size': self.sample_size
        })


class CalibrationPoint:
    def __init__(self, x: float = 0.0, y: float = 0.0, progress: int = 0):
        self.x = x
        self.y = y
        self.progress = progress

    def __str__(self):
        return str({
            'x': self.x,
            'y': self.y,
            'progress': self.progress
        })

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y


class GazeInfo:
    def __init__(self, status=0, timestamp=0, gaze_x=0, gaze_y=0, left_openness=0.0, right_openness=0.0):
        self.status = status
        self.timestamp = timestamp
        self.gaze_x = gaze_x
        self.gaze_y = gaze_y
        self.left_openness = left_openness
        self.right_openness = right_openness

    def __str__(self):
        return str({
            'status': self.status,
            'timestamp': self.timestamp,
            'gaze_x': self.gaze_x,
            'gaze_y': self.gaze_y,
            'left_openness': self.left_openness,
            'right_openness': self.right_openness
        })


class TCCIDesktopET:
    """
    A class to interact with the tcci_desktop_et.dll for eye tracking functions.

    This class provides an interface to the C++ functions exposed by the tcci_desktop_et.dll library.
    """

    def __init__(self):
        """
        Initializes the TCCIDesktopET class, loads the DLL and sets up function prototypes.

        This constructor detects if the platform is Windows, sets up the library path, and loads the
        `tcci_desktop_et.dll` using ctypes. It also declares function prototypes with proper argument
        and return types.
        """
        if platform.system().lower() == 'windows':
            _lib_dir = os.path.abspath(os.path.dirname(__file__))
            os.add_dll_directory(_lib_dir)
            os.environ['PATH'] = os.environ['PATH'] + ';' + _lib_dir
            _dll_path = os.path.join(_lib_dir, 'libtccidesktopet.dll')
            self.native_lib = ctypes.CDLL(_dll_path, winmode=0x0)

        else:
            logging.warning("Not supported platform: %s" % platform.system())

        """
        Declare function prototypes
        """
        # Initializes the eye-tracking system
        self.native_lib.eye_tracking_init.restype = ctypes.c_int
        self.native_lib.get_version.restype = ctypes.c_char_p

        self.native_lib.eye_tracking_register.restype = ctypes.c_int
        self.native_lib.eye_tracking_register.argtypes = [ctypes.c_char_p]
        """
        // Sets camera and screen info
        // Parameters: camera_x_cm, camera_y_cm - camera position in centimeters
        //             screen_width_px, screen_height_px - screen size in pixel
        //             dpi_x, dpi_y - screen dpi
        """
        self.native_lib.set_camera_screen_info.argtypes = [ctypes.c_float, ctypes.c_float,
                                                           ctypes.c_float, ctypes.c_float]
        self.native_lib.set_camera_screen_info.restype = ctypes.c_int
        # Starts the eye-tracking calibration process
        self.native_lib.start_calibration.restype = ctypes.c_int
        # Checks if the calibration process is finished
        self.native_lib.is_calibration_finished.restype = ctypes.c_bool
        # Retrieves the calibration results
        self.native_lib.get_calibration_result.restype = ctypes.c_float
        """
        Parameters: status - Calibration status code
            fit_error - Calibration error in pixels
            sample_size - Number of samples used in calibration
            info - Additional information as a string
        """
        self.native_lib.get_calibration_result.argtypes = [
            ctypes.POINTER(ctypes.c_int),  # status
            ctypes.POINTER(ctypes.c_float),  # fit_error
            ctypes.POINTER(ctypes.c_int),  # sample_size
        ]
        # Retrieves information about the current calibration point
        self.native_lib.get_calibration_point_info.restype = ctypes.c_int
        """
        Parameters: x, y - Current calibration point in normalized screen coordinates (0-1)
            progress - Progress percentage of calibration
        """
        self.native_lib.get_calibration_point_info.argtypes = [ctypes.POINTER(ctypes.c_float),
                                                               ctypes.POINTER(ctypes.c_float),
                                                               ctypes.POINTER(ctypes.c_int)]

        # Starts previewing the camera feed for gaze tracking
        self.native_lib.start_previewing.restype = ctypes.c_int
        # Retrieves the current preview image
        self.native_lib.get_previewer_image.restype = ctypes.c_int
        self.native_lib.get_previewer_image.argtypes = [ctypes.POINTER(ctypes.c_ubyte)]
        # Stops the previewing process
        self.native_lib.stop_previewing.restype = ctypes.c_int
        # Starts sampling for gaze tracking data
        self.native_lib.start_sampling.restype = ctypes.c_int
        # Stops the gaze tracking sampling process
        self.native_lib.stop_sampling.restype = ctypes.c_int
        # Retrieves the gaze information
        self.native_lib.get_gaze_info.restype = ctypes.c_int
        # Saves the collected data to a file
        self.native_lib.save_data.restype = ctypes.c_int
        self.native_lib.save_data.argtypes = [ctypes.c_char_p]

        # configurate `load_calibration` function
        self.native_lib.load_calibration.argtypes = [ctypes.c_char_p]
        self.native_lib.load_calibration.restype = ctypes.c_int

        # configurate `export_calibration` function
        self.native_lib.export_calibration.argtypes = [ctypes.POINTER(ctypes.c_char_p)]
        self.native_lib.export_calibration.restype = ctypes.c_int

        self.native_lib.set_tracing_region.restype = ctypes.c_int
        self.native_lib.set_calibration_mode.restype = ctypes.c_int

        # Image size
        self.image_width = 640
        self.image_height = 480
        # Image ndarray
        self.image = np.zeros((self.image_height, self.image_width, 3), dtype=np.uint8)
        # Screen size
        self.screen_width, self.screen_height = 1920, 1080

    def set_tracing_region(self, x: int, y: int, width: int, height: int):
        self.native_lib.set_tracing_region(x, y, width, height)

    def set_cali_mode(self, cali_mode: int):
        if cali_mode not in [5, 9, 13]:
            raise ValueError(f"Invalid calibration mode: {cali_mode}, you need to choose from 5, 9, and 13.")
        else:
            self.native_lib.set_calibration_mode(cali_mode)

    def set_cam_screen_info(self, camera_position=(17.09, -0.65), screen_size=(1920, 1080),
                            screen_size_inch=(34.4 / 2.54, 19.4 / 2.54)):
        cam_pos_x, cam_pos_y = camera_position
        screen_width, screen_height = screen_size
        dpi_x, dpi_y = screen_width / screen_size_inch[0], screen_height / screen_size_inch[1]
        self.native_lib.set_camera_screen_info(cam_pos_x, cam_pos_y, screen_width, screen_height, dpi_x, dpi_y)

    def eye_tracking_register(self, license_key: str) -> int:
        """
        Eye tracking system authorization.
        :param license_key: license key string
        :return: how many days to expire
        """
        return self.native_lib.eye_tracking_register(license_key.encode("gbk"))

    def eye_tracking_init(self, cam_id: int = 0, look_ahead: int = 3, preprocessing_type: int = 1):
        """
        Initializes the eye tracking system.

        This function initializes the eye tracking system. It must be called before using any other
        eye tracking functionality.

        Returns:
            int: 0 if initialization is successful, a non-zero value if it fails.
        """
        self.native_lib.eye_tracking_init(cam_id, look_ahead, preprocessing_type)

    def set_camera_screen_info(self, x_cm, y_cm, screen_width_px, screen_height_px, dpi_x, dpi_y):
        """
        Sets camera and screen info
        Parameters:
            x_cm, y_cm - camera position in centimeters (float or int)
            screen_width_px, screen_height_px - screen size in pixels (int)
            dpi_x, dpi_y - screen dpi (int or float)

        Returns:
            int: 0 if successful, a non-zero value if it fails.
        """
        # 类型检查
        if not (isinstance(x_cm, (int, float)) and isinstance(y_cm, (int, float))):
            raise TypeError("x_cm and y_cm should be of type int or float.")

        if not (isinstance(screen_width_px, int) and isinstance(screen_height_px, int)):
            raise TypeError("screen_width_px and screen_height_px should be of type int.")

        if not (isinstance(dpi_x, (int, float)) and isinstance(dpi_y, (int, float))):
            raise TypeError("dpi_x and dpi_y should be of type int or float.")

        return self.native_lib.set_camera_screen_info(x_cm, y_cm, screen_width_px, screen_height_px, dpi_x, dpi_y)

    def start_calibration(self):
        """
        Starts the eye calibration process.

        This function begins the process of calibrating the eye tracker. Calibration is necessary to
        ensure accurate gaze tracking.

        Returns:
            int: 0 if calibration starts successfully, a non-zero value if it fails.
        """
        return self.native_lib.start_calibration()

    def is_calibration_finished(self):
        """
        Checks if the calibration process has finished.

        This function checks whether the eye tracking calibration process has been completed.

        Returns:
            bool: True if calibration is finished, False otherwise.
        """
        return self.native_lib.is_calibration_finished()

    def get_calibration_result(self) -> CalibrationResult:
        """
        Gets the result of the calibration.

        This function returns the calibration result as a float, where a lower value indicates better calibration.

        Returns:
            float: The calibration result value.
        """
        status = ctypes.c_int()
        fit_error = ctypes.c_float()
        sample_size = ctypes.c_int()

        self.native_lib.get_calibration_result(
            ctypes.byref(status),
            ctypes.byref(fit_error),
            ctypes.byref(sample_size),
        )

        return CalibrationResult(status=status.value,
                                 fitting_error=fit_error.value,
                                 sample_size=sample_size.value)

    def get_calibration_point_info(self) -> CalibrationPoint:
        """
        Gets the information of the current calibration point.

        This function retrieves the x, y coordinates and the progress of the calibration point.

        Returns:
            tuple: A tuple containing the x and y coordinates (float) and the progress (int).
        """
        x = ctypes.c_float()
        y = ctypes.c_float()
        progress = ctypes.c_int()
        self.native_lib.get_calibration_point_info(ctypes.byref(x), ctypes.byref(y), ctypes.byref(progress))
        return CalibrationPoint(x=x.value, y=y.value, progress=progress.value)

    def start_previewing(self):
        """
        Starts the video preview for the eye tracking system.

        This function starts the preview mode to display the video stream captured by the camera.

        Returns:
            int: 0 if successful, a non-zero value if it fails.
        """
        return self.native_lib.start_previewing()

    def get_previewer_image(self):
        """
        Retrieves the current preview image from the eye tracking system.
        """
        image_ptr = self.image.ctypes.data_as(ctypes.POINTER(ctypes.c_ubyte))
        self.native_lib.get_previewer_image(image_ptr)
        return self.image

    def stop_previewing(self):
        """
        Stops the video preview.

        This function stops the camera preview and releases the video resources.

        Returns:
            int: 0 if successful, a non-zero value if it fails.
        """
        return self.native_lib.stop_previewing()

    def start_sampling(self):
        """
        Starts sampling the gaze data.

        This function begins collecting the gaze data from the eye tracker.

        Returns:
            int: 0 if successful, a non-zero value if it fails.
        """
        return self.native_lib.start_sampling()

    def stop_sampling(self):
        """
        Stops sampling the gaze data.

        This function stops the collection of gaze data.

        Returns:
            int: 0 if successful, a non-zero value if it fails.
        """
        return self.native_lib.stop_sampling()

    def get_gaze_info(self) -> GazeInfo:
        """
        Retrieves the gaze information.

        This function returns the current gaze information from the eye tracker.

        Returns:
            int: A non-zero value indicating the result of the gaze information retrieval.
        """
        status = ctypes.c_int(0)
        timestamp = ctypes.c_uint64(0)
        x = ctypes.c_float(0.0)
        y = ctypes.c_float(0.0)
        left_openness = ctypes.c_float(0.0)
        right_openness = ctypes.c_float(0.0)

        self.native_lib.get_gaze_info(
            ctypes.byref(status),
            ctypes.byref(timestamp),
            ctypes.byref(x),
            ctypes.byref(y),
            ctypes.byref(left_openness),
            ctypes.byref(right_openness)
        )

        return GazeInfo(
            status=status.value,
            timestamp=timestamp,
            gaze_x=x.value,
            gaze_y=y.value,
            left_openness=left_openness.value,
            right_openness=right_openness.value)

    def save_data(self, path):
        """
        Saves the collected data to a file.

        This function saves the gaze tracking data to the specified file path.

        Args:
            path (str): The file path to save the data.

        Returns:
            int: 0 if successful, a non-zero value if it fails.
        """
        return self.native_lib.save_data(path.encode('gbk'))  # Ensure it's a byte string

    def load_calibration(self, cali_info):
        """
        调用 load_calibration 函数
        :param cali_info: 输入校准字符串
        :return: 执行状态码
        """
        if not isinstance(cali_info, str):
            raise ValueError("cali_info must be a string")

        status = self.native_lib.load_calibration(cali_info.encode('utf-8'))
        return status

    def export_calibration(self):
        """
        调用 export_calibration 函数
        :return: (状态码, 校准信息字符串)
        """
        cali_info_ptr = ctypes.c_char_p()
        status = self.native_lib.export_calibration(ctypes.byref(cali_info_ptr))

        if status == 1 and cali_info_ptr.value is not None:
            cali_info = cali_info_ptr.value.decode('utf-8')
            return status, cali_info
        return status, None

    def get_version(self):
        return self.native_lib.get_version().decode('utf-8')
