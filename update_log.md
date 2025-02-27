# TCCI Desktop ET SDK Update Log

## Version 0.0.4 (Build 1) - 2025-02-26

- Added `set_tracing_region` function to configure the operational region of the eye tracker.
- Implemented `set_calibration_mode` function supporting 5-point, 9-point, and 13-point calibration patterns.
- Recommended setting `OPENCV_VIDEOIO_PRIORITY_MSMF=0` in environment variables for camera latency mitigation.

---

## Version 0.0.3 (Build 1) - 2025-02-18

- Revised camera handling to non-exclusive mode: Device opens on `start_xxx` invocation and closes via `stop_xxx`.
- Introduced callback class architecture for real-time eye-tracking data retrieval.

---

## Version 0.0.2 (Build 1) - 2025-01-22

- Add `load_calibration` and `export_calibration` example.
- Add calibration feedback audio.
- Update `library.h` file.

---