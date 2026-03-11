import os
import sys
import argparse
import pytesseract
from PIL import Image
from trdg.generators import GeneratorFromStrings

def extract_sentences_from_image(image_path, lang='tam'):
    """Extracts text from an image and splits it into cleaned sentences."""
    if not os.path.exists(image_path):
        print(f"Error: Image file not found at {image_path}")
        sys.exit(1)
        
    try:
        # Load image
        img = Image.open(image_path)
        
        # Extract text using Tesseract
        print(f"Extracting text from {image_path} using Tesseract (lang={lang})...")
        # Explicitly set tesseract path for Windows
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        
        # Explicitly tell Tesseract where to find the language data files (tam.traineddata)
        os.environ['TESSDATA_PREFIX'] = r'C:\Program Files\Tesseract-OCR\tessdata'
        
        extracted_text = pytesseract.image_to_string(img, lang=lang)
        
        if not extracted_text.strip():
            print("Warning: No text could be extracted from the image.")
            return []
            
        print("\n--- Extracted Text ---")
        print(extracted_text)
        print("----------------------\n")
        
        # Parse into sentences (split by newlines and basic delimiters)
        # Tamil doesn't strongly use periods for sentences like English, so we rely on newlines and spacing
        lines = extracted_text.split('\n')
        cleaned_sentences = []
        for line in lines:
            line = line.strip()
            if line: # if not empty
                cleaned_sentences.append(line)
                
        return cleaned_sentences
        
    except Exception as e:
        import traceback
        print(f"An error occurred during text extraction: {e}")
        traceback.print_exc()
        print("\nNote: Please ensure Tesseract OCR is installed and added to your system PATH.")
        sys.exit(1)

def generate_dataset(sentences, output_dir, font_dir, num_images_per_line=5):
    """Generates an augmented OCR dataset progressively, word by word, from extracted lines."""
    if not sentences:
        print("No sentences to generate images for. Exiting.")
        return
        
    # Build progressive strings across the entire document
    progressive_strings = []
    all_words = []
    for sentence in sentences:
        all_words.extend(sentence.split())
        
    current_string = ""
    for word in all_words:
        if current_string:
            current_string += " " + word
        else:
            current_string = word
        progressive_strings.append(current_string)
            
    if not progressive_strings:
        print("No words found in sentences to generate images for. Exiting.")
        return
        
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    print(f"Found {len(sentences)} distinct sentences/lines, totaling {len(all_words)} words.")
    print(f"Broke down into {len(progressive_strings)} progressively built word strings representing the entire document.")
    
    # Check fonts
    if not os.path.exists(font_dir):
        print(f"Error: Font directory not found at {font_dir}")
        sys.exit(1)
        
    fonts = [os.path.join(font_dir, f) for f in os.listdir(font_dir) if f.endswith('.ttf')]
    if not fonts:
        print(f"Error: No .ttf fonts found in {font_dir}")
        sys.exit(1)
        
    total_images_to_generate = len(progressive_strings) * num_images_per_line
    print(f"Starting dataset generation. Generating ~{total_images_to_generate} images in '{output_dir}'")
    
    try:
        # Initialize the trdg generator
        # trdg handles font sizes automatically via random size variations internally if configured or varying string sizes
        generator = GeneratorFromStrings(
            strings=progressive_strings,
            fonts=fonts,
            language="ta",
            count=total_images_to_generate,
            size=64,                # Base font size parameter
            skewing_angle=3,        # Small rotations to mimic scanned documents
            blur=2,                 # Gaussian noise/blur equivalent
            random_blur=True,       # Variable blur across images
            background_type=0,      # 0: Gaussian Noise, 1: Plain white, 2: Quasicrystal, 3: Image
            distorsion_type=0,      # Small distortions
            word_split=True,        # Force Pillow to render full words so Tamil ligatures are shaped correctly via Raqm
        )
        
        # Save images and text labels
        for i, (img, lbl) in enumerate(generator):
            base_filename = f"extracted_data_{i}"
            img.save(os.path.join(output_dir, f"{base_filename}.png"))
            with open(os.path.join(output_dir, f"{base_filename}.txt"), "w", encoding="utf-8") as f:
                f.write(lbl)
                
            if (i+1) % 50 == 0:
                print(f"Generated {i+1} / {total_images_to_generate} items...")
                
        print("\nSuccess! Generated augmented OCR dataset.")
        print(f"Dataset saved to: {os.path.abspath(output_dir)}")
        
    except Exception as e:
         print(f"An error occurred during dataset generation: {e}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extracts text from a Tamil image and generates an augmented OCR dataset.')
    parser.add_argument('image_path', help='Path to the input image file (e.g., sample.png)')
    parser.add_argument('--out_dir', default='./dataset/extracted/', help='Directory to save output dataset (default: ./dataset/extracted/)')
    parser.add_argument('--fonts', default='./fonts/tamil/', help='Directory containing .ttf Tamil fonts (default: ./fonts/tamil/)')
    parser.add_argument('--count_per_line', type=int, default=5, help='Number of augmented images to generate per extracted text line (default: 5)')
    
    args = parser.parse_args()
    
    print(f"Processing image: {args.image_path}")
    
    # 1. Extract and clean text
    extracted_lines = extract_sentences_from_image(args.image_path, lang='tam')
    
    # 2. Generate augmented data
    generate_dataset(
        sentences=extracted_lines,
        output_dir=args.out_dir,
        font_dir=args.fonts,
        num_images_per_line=args.count_per_line
    )
