# Tamil Progressive OCR Dataset Generator

This tool allows you to automatically extract Tamil text from any document or image and generate a massive, high-quality augmented OCR dataset from it. 

It is specially designed to **progressively** build up the sentences it reads. For every single word it encounters, it generates heavily augmented (tilted, blurred, noisy) image variations that look like real, imperfect scanned documents.

---

## 🚀 How it Works

When you provide an image (e.g., `image.png`) containing Tamil text:

1. **Text Extraction:** Google's Tesseract Engine reads the image and extracts all the text.
2. **Progressive Breakdown:** The script breaks the text down word by word.
3. **Augmentation Generation:** It dynamically generates synthetic images containing the growing text sequences.

### Example
If your image contains the text: **உலகதீதில் ஏழு அதிசயங்கள்**

The script will automatically break it into these stages:
* **Stage 1:** `உலகதீதில்` (Generates 5 blurry/tilted images of this word)
* **Stage 2:** `உலகதீதில் ஏழு` (Generates 5 blurry/tilted images of these words)
* **Stage 3:** `உலகதீதில் ஏழு அதிசயங்கள்` (Generates 5 blurry/tilted images of the full phrase)

It also automatically saves perfectly matching `.txt` label files next to every image!

---

## 🛠️ Requirements & Setup

Before running the script, you must have the **Tesseract OCR Engine** installed on Windows.

1. **Install Tesseract:** Download and install Tesseract OCR for Windows (usually installs to `C:\Program Files\Tesseract-OCR`).
2. **Tamil Language Pack:** Ensure you have the `tam.traineddata` (Tamil language support file) placed inside Tesseract's `tessdata` folder (`C:\Program Files\Tesseract-OCR\tessdata`).
3. **Install Python Packages:** Open your terminal and install the required libraries:
   ```bash
   pip install pytesseract pillow
   ```

*(Note: The `trdg` engine is already included in this project folder for the synthetic generation).*

---

## 💻 How to Use

Save your input image (like `my_document.jpg`) inside the `uploaded_images` folder. 

Open your terminal (PowerShell/Command Prompt) here and run:

### Basic Command (Highly Recommended)
```bash
python generate_from_image.py uploaded_images/my_document.jpg 
```
*This will extract the text and generate 5 augmented image variations for every word stage across the document.*
*The output goes to `./dataset/extracted/` by default.*

### Advanced Customization
You can control the output directory and exactly how many variants are made for each stage:

```bash
python generate_from_image.py uploaded_images/my_document.jpg --out_dir ./my_custom_folder/ --count_per_line 10
```

### Script Arguments Details:
- `image_path`: (Required) The name/path of the image you want to extract text from.
- `--out_dir`: (Optional) The folder where the generated `.png` and `.txt` files will be saved.
- `--count_per_line`: (Optional) The number of augmented image variations you want to generate for exactly each stage. The default is `5`.
- `--fonts`: (Optional) The folder to pull `.ttf` Tamil fonts from. Default is `./fonts/tamil/`.
- `--no_palm_leaf`: (Optional) Disable the palm leaf manuscript variant generation.

---

## 🌿 Palm Leaf Manuscript Mode (ஓலைச்சுவடி)

By default, the script **automatically generates a historical palm leaf manuscript variant** for every single image! Each variant features:
* Aged **yellowish-brown palm leaf texture** background
* **Sepia-toned** color grading
* Dark brown **stylus-etched** text color
* Random **scratches and grain noise** for authenticity
* Subtle **vignette** (darkened edges)

This effectively **doubles your dataset** — every word stage gets both a modern scan AND a historical palm leaf version!

To disable this feature, use `--no_palm_leaf`:
```bash
python generate_from_image.py uploaded_images/my_document.jpg --no_palm_leaf
```

---

## 📂 Output Format
Inside the output directory you specify, you will find paired files like:

* `extracted_data_0.png` (The generated synthetic image)
* `extracted_data_0_palmleaf.png` (The palm leaf manuscript variant)
* `extracted_data_0.txt` (A text file containing the exact text inside the image)
* `extracted_data_0_palmleaf.txt` (Matching label for the palm leaf variant)

Enjoy effortlessly building automated OCR dataset pipelines!

