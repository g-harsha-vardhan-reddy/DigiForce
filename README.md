# DigiForensics

### Digital Image Forensics & Tampering Detection System

DigiForensics is a web-based digital image forensics application designed to analyze images for possible signs of manipulation or tampering.

The system combines multiple Digital Image Processing (DIP) and image-forensic techniques to generate visual analysis results and a heuristic forensic assessment.

## 🚀 Live Demo

**Live Application:**  
https://digiforce.onrender.com/

> The application is deployed on Render and uses Cloudinary for persistent image storage.

---

## 📌 Project Overview

Digital images can be manipulated using image editing software, AI-based tools, copy-move operations, compression, and other techniques.

DigiForensics provides a centralized web interface where users can:

1. Upload an image.
2. Validate the uploaded image.
3. Perform multiple image-processing operations.
4. Analyze forensic indicators.
5. Calculate individual forensic scores.
6. Generate an overall heuristic assessment.
7. View processed images and forensic results.
8. Download a forensic analysis report in PDF format.

The project is intended as an educational and experimental image-forensics system rather than a replacement for professional forensic investigation.

---

## ✨ Features

### 📤 Image Upload

- Upload JPG, JPEG, PNG, and WEBP images.
- Maximum upload size of 10 MB.
- Image validity verification.
- File-type validation.
- Persistent cloud-based image storage using Cloudinary.

### 🔬 Digital Image Processing

The application performs several image-processing operations:

- Grayscale conversion
- Gaussian filtering
- Median filtering
- Sobel edge detection
- Canny edge detection
- Morphological processing
- Histogram analysis

### 🕵️ Forensic Analysis

DigiForensics analyzes several indicators associated with possible image manipulation:

- Error Level Analysis (ELA)
- Frequency-domain analysis
- Edge analysis
- Noise analysis
- Histogram analysis
- Copy-move detection

### 📊 Forensic Scoring

The application calculates individual forensic scores and combines them into a heuristic assessment.

The baseline score uses weighted forensic indicators:

```text
Baseline Score =
(ELA × 0.35)
+ (Frequency × 0.25)
+ (Edge × 0.15)
+ (Noise × 0.15)
+ (Histogram × 0.10)
