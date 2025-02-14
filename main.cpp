#include <opencv2/core/mat.hpp>
#include <opencv2/highgui.hpp>
#include <opencv2/imgproc.hpp>
#include <iostream>
#include "library.h"
#include "callbacks.h"

class MyGazeSampleCallback : public IGazeSampleCallback {
public:
    MyGazeSampleCallback() = default;

    void onGaze(uint64_t timestamp, float x, float y,
                float left_openness, float right_openness,
                int tracking_state,
                int eye_movement_event) override {
        std::cout << "Timestamp: " << timestamp << std::endl;
        std::cout << "Gaze coordinates: (" << x << ", " << y << ")" << std::endl;
        std::cout << "Left Eye Openness: " << left_openness << std::endl;
        std::cout << "Right Eye Openness: " << right_openness << std::endl;
    }

    ~MyGazeSampleCallback() override = default;
};

class MyCalibrationCallback : public ICalibrationCallback {
public:
    MyCalibrationCallback() = default;

    ~MyCalibrationCallback() override = default;

    // Implement the onCalibrationProgress callback
    void onCalibrationProgress(int progress) override {
        std::cout << "Calibration progress: " << progress << "%" << std::endl;
    }

    // Implement the onCalibrationNextPoint callback
    void onCalibrationNextPoint(float x, float y) override {
        std::cout << "Next calibration point: (" << x << ", " << y << ")" << std::endl;
    }

    // Implement the onCalibrationFinish callback
    void onCalibrationFinish(int status, float fit_error) override {
        std::string status_str = (status == 1) ? "Valid" : "Invalid";
        std::cout << "Calibration finished. Status: " << status_str
                  << ", Fit Error: " << fit_error << " pixels" << std::endl;
    }
};

void onGaze(uint64_t timestamp, float x, float y,
            float left_openness, float right_openness,
            int tracking_state,
            int eye_movement_event) {
    std::cout << "Timestamp: " << timestamp << std::endl;
    std::cout << "Gaze coordinates: (" << x << ", " << y << ")" << std::endl;
    std::cout << "Left Eye Openness: " << left_openness << std::endl;
    std::cout << "Right Eye Openness: " << right_openness << std::endl;
}

void onCalibrationFinish(int status, float fit_error) {
    std::string status_str = (status == 1) ? "Valid" : "Invalid";
    std::cout << "Calibration finished. Status: " << status_str
              << ", Fit Error: " << fit_error << " pixels" << std::endl;
}

void onCalibrationNextPoint(float x, float y) {
    std::cout << "Next calibration point: (" << x << ", " << y << ")" << std::endl;
}

void onCalibrationProgress(int progress) {
    std::cout << "Calibration progress: " << progress << "%" << std::endl;
}

int main(int argc, char *argv[]) {
    std::cout << " start." << std::endl;
    // Create a buffer to store the image (640x480 resolution, 3 channels: RGB).
    unsigned char *image_buffer = new unsigned char[640 * 480 * 3]; // 640x480 resolution, 3 channels (RGB)

    // Initialize the eye-tracking system.
    eye_tracking_init();

//    auto *myGazeSampleCallback = new MyGazeSampleCallback();
//    auto *myCalibrationCallback = new MyCalibrationCallback();
//    set_gaze_sample_callback(myGazeSampleCallback);
//    set_calibration_callback(myCalibrationCallback);
//    set_calibration_callback_funcs(onCalibrationNextPoint, onCalibrationProgress, onCalibrationFinish);
//    set_gaze_sample_callback_func(onGaze);

    set_calibration_callback_funcs(onCalibrationNextPoint, onCalibrationProgress, onCalibrationFinish);
    set_gaze_sample_callback_func(onGaze);

    // Register the system with the provided license key.
    // The license key is passed as a command-line argument (argv[1]).
    eye_tracking_register("c8f076bc10dd43d6");

    // Output the remaining days of validity for the license.
//    std::cout << "License valid for " << eye_tracking_register(argv[1]) << " days." << std::endl;

    // Start the eye-tracking system's preview functionality.
    start_previewing();

    // Create an OpenCV window to display the previewed face image in full-screen mode.
    cv::namedWindow("Eye Tracking Preview", cv::WINDOW_NORMAL);
    cv::setWindowProperty("Eye Tracking Preview", cv::WND_PROP_FULLSCREEN, cv::WINDOW_FULLSCREEN);

    // Continuously capture and display images until 'q' is pressed to exit.
    while (true) {
        // Retrieve the latest face image into the image buffer (unsigned char pointer).
        get_previewer_image(image_buffer);

        // Convert the raw image buffer into an OpenCV Mat object for display.
        cv::Mat img(480, 640, CV_8UC3, image_buffer);
        cv::cvtColor(img, img, cv::COLOR_RGB2BGR);
        // Display the image in the created OpenCV window.
        cv::imshow("Eye Tracking Preview", img);

        // If the 'q' key is pressed, exit the loop and stop previewing.
        if (cv::waitKey(1) == 'q') {
            break;
        }
    }

    // Stop the previewing process once the loop exits.
    stop_previewing();

    // Start the calibration process.
    start_calibration();

    // Variables for holding calibration point position and progress.
    float cali_pos_x, cali_pos_y; // Calibration point position on the screen.
    int progress; // Progress of the calibration process.
    cv::Mat img(1080, 1920, CV_8UC3, cv::Scalar(255, 255, 255));
    // Continuously update and display the calibration points until the calibration is finished.
    while (1) {
        img.setTo(cv::Scalar(255, 255, 255));  // Restore white background
        // Retrieve the current calibration point info: position and progress.
        get_calibration_point_info(cali_pos_x, cali_pos_y, progress);

        // Convert progress to a percentage (e.g., 0-100).
        int percentage = progress; // Assuming 'progress' is between 0 and 100.

        // Draw a circle at the calibration point.
        cv::circle(img, cv::Point((int) cali_pos_x, (int) cali_pos_y), 20, cv::Scalar(0, 255, 0), 2);

        // Put the percentage text inside the circle.
        std::string progress_text = std::to_string(percentage) + "%";
        cv::putText(img, progress_text, cv::Point((int) cali_pos_x - 10, (int) cali_pos_y + 5),
                    cv::FONT_HERSHEY_SIMPLEX, 0.5, cv::Scalar(0, 0, 0), 2);

        // Display the image with the drawn circle and progress text.
        cv::imshow("Eye Tracking Preview", img);

        // Wait for a short period to update the display.
        cv::waitKey(1);

        // Check if the calibration process has been completed.
        if (is_calibration_finished()) {
            break;
        }
    }


    // Variables for storing calibration result information.
    int status;
    float fit_error;
    int sample_size;
    get_calibration_result(status, fit_error, sample_size);

    // Print the calibration result information
    std::cout << "Calibration Status: " << status << std::endl;
    std::cout << "Fit Error: " << fit_error << std::endl;
    std::cout << "Sample Size: " << sample_size << std::endl;

    // If calibration status is less than 1, the calibration is unsuccessful and needs to be retried.
    /**
     * If calibration status is less than 1, please recalibrate.
     * You may want to provide feedback to the user and restart calibration.
     */

    // Start the gaze tracking sampling process.
    start_sampling();

    // Continuously retrieve and display gaze tracking data until 'q' is pressed to exit.
    while (1) {
        img.setTo(cv::Scalar(255, 255, 255));  // Restore white background
        // Retrieve gaze tracking information: gaze coordinates and eye openness.
        int status;
        uint64_t timestamp;
        float gaze_x, gaze_y;
        float left_eye_openness, right_eye_openness;

        get_gaze_info(status, timestamp, gaze_x, gaze_y, left_eye_openness, right_eye_openness);

        // Add code here to display the gaze info or perform further processing.
        // You can display gaze coordinates or use them in other parts of your system.
        // ........................
        // ........................
        // Draw a circle at the calibration point.
        cv::circle(img, cv::Point((int) gaze_x, (int) gaze_y), 20, cv::Scalar(0, 255, 0), 2);
        // Display the image with the drawn circle and progress text.
        cv::imshow("Eye Tracking Preview", img);

        // If the 'q' key is pressed, exit the loop and stop sampling.
        if (cv::waitKey(1) == 'q') {
            break;
        }
    }

    // Stop the gaze tracking sampling process once the loop exits.
    stop_sampling();

    // Free the allocated memory for the image buffer.
    delete[] image_buffer;

    // Destroy the OpenCV window resources once the program is done.
    cv::destroyAllWindows();

    return 0;
}
