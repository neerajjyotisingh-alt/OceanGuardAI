# OceanGuard AI — Project Architecture

## 1. Project Goal
OceanGuard AI is a prototype for AI-assisted marine debris detection and pollution mapping.

## 2. Intended Workflow

1. **Image Input:** The user provides an image for analysis.
2. **AI Detection:** The ONNX-based detection pipeline identifies potential marine debris.
3. **GPS Extraction:** The GPS module attempts to extract coordinates from image EXIF metadata when available.
4. **Data Storage:** Detection results and available coordinates can be stored in a database.
5. **Pollution Mapping:** Geolocated observations can be displayed on an interactive map.
6. **Dashboard:** A dashboard can present saved observations, review status, and summary analytics.

## 3. Important Data Rules
- Images without embedded GPS metadata do not automatically provide their capture location.
- Missing coordinates must remain unknown until a reliable location source is provided.
- Test coordinates and demonstration data must be clearly distinguished from verified observations.
- Model predictions are potential detections, not proof of confirmed marine pollution.

## 4. Development Status
The repository contains detection, GPS-reading, and mapping components. Full integration of detection, location extraction, database persistence, and dashboard visualization remains under development.

## 5. Planned Improvements
- Connect the modules into a single workflow.
- Validate detections against labelled test images.
- Improve location handling and observation review.
- Test the integrated system from image upload to map visualization.
