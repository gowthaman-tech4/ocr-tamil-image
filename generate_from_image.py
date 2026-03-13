import os
import sys
import argparse
import random
import numpy as np
import pytesseract
from PIL import Image, ImageFilter, ImageEnhance, ImageDraw
from trdg.generators import GeneratorFromStrings

# --- Palm Leaf Manuscript Effect ---
BG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backgrounds')
PALM_LEAF_BG = os.path.join(BG_DIR, 'palm_leaf_bg.png')

def apply_palm_leaf_effect(text_image):
    """Takes a generated text image and composites it onto a palm leaf
    manuscript background with aging effects to simulate an ola chuvadi."""
    
    # Load the palm leaf background
    bg = Image.open(PALM_LEAF_BG).convert('RGBA')
    txt = text_image.convert('RGBA')
    
    # Resize background to fit the text image with some padding
    pad_x, pad_y = 40, 30
    target_w = txt.width + pad_x * 2
    target_h = txt.height + pad_y * 2
    bg = bg.resize((target_w, target_h), Image.LANCZOS)
    
    # Convert text to dark brown ink color (simulate stylus etching)
    txt_data = np.array(txt)
    # Where text pixels exist (non-transparent), make them dark brown
    alpha = txt_data[:, :, 3]
    mask = alpha > 30
    txt_data[mask, 0] = 25   # R - dark
    txt_data[mask, 1] = 15   # G - very dark
    txt_data[mask, 2] = 0    # B - no blue
    txt_colored = Image.fromarray(txt_data)
    
    # Paste the dark text onto the palm leaf background
    bg.paste(txt_colored, (pad_x, pad_y), txt_colored)
    
    # Convert to RGB for final processing
    result = bg.convert('RGB')
    
    # Apply sepia/aged tone
    result_arr = np.array(result, dtype=np.float32)
    sepia_r = result_arr[:,:,0] * 0.85 + result_arr[:,:,1] * 0.25 + result_arr[:,:,2] * 0.08
    sepia_g = result_arr[:,:,0] * 0.55 + result_arr[:,:,1] * 0.35 + result_arr[:,:,2] * 0.08
    sepia_b = result_arr[:,:,0] * 0.30 + result_arr[:,:,1] * 0.18 + result_arr[:,:,2] * 0.05
    result_arr[:,:,0] = np.clip(sepia_r, 0, 255)
    result_arr[:,:,1] = np.clip(sepia_g, 0, 255)
    result_arr[:,:,2] = np.clip(sepia_b, 0, 255)
    result = Image.fromarray(result_arr.astype(np.uint8))
    
    # Add random grain noise for aged paper feel
    noise = np.random.randint(-15, 15, (target_h, target_w, 3), dtype=np.int16)
    noisy = np.clip(np.array(result, dtype=np.int16) + noise, 0, 255).astype(np.uint8)
    result = Image.fromarray(noisy)
    
    # Add random thin scratch lines
    draw = ImageDraw.Draw(result)
    for _ in range(random.randint(2, 6)):
        y = random.randint(0, target_h - 1)
        x1 = random.randint(0, target_w // 3)
        x2 = random.randint(target_w // 2, target_w - 1)
        scratch_color = (random.randint(80, 120), random.randint(60, 90), random.randint(30, 50))
        draw.line([(x1, y), (x2, y + random.randint(-3, 3))], fill=scratch_color, width=1)
    
    # Add subtle vignette (darken edges)
    vignette = Image.new('L', (target_w, target_h), 0)
    vdraw = ImageDraw.Draw(vignette)
    for i in range(30):
        opacity = int(255 * (i / 30))
        vdraw.rectangle([i, i, target_w - i, target_h - i], outline=opacity)
    vignette = vignette.filter(ImageFilter.GaussianBlur(radius=15))
    result_arr = np.array(result, dtype=np.float32)
    vig_arr = np.array(vignette, dtype=np.float32) / 255.0
    for c in range(3):
        result_arr[:,:,c] = result_arr[:,:,c] * vig_arr
    result = Image.fromarray(result_arr.astype(np.uint8))
    
    # Slight blur for aged feel
    if random.random() > 0.5:
        result = result.filter(ImageFilter.GaussianBlur(radius=0.5))
    
    # Random slight brightness/contrast variation
    enhancer = ImageEnhance.Brightness(result)
    result = enhancer.enhance(random.uniform(0.85, 1.05))
    enhancer = ImageEnhance.Contrast(result)
    result = enhancer.enhance(random.uniform(0.9, 1.1))
    
    return result

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

def generate_dataset(sentences, output_dir, font_dir, num_images_per_line=5, palm_leaf=True):
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
        palm_leaf_enabled = palm_leaf and os.path.exists(PALM_LEAF_BG)
        if palm_leaf_enabled:
            print("Palm leaf manuscript (ஓலைச்சுவடி) mode: ON — generating historical variants too!")
        
        for i, (img, lbl) in enumerate(generator):
            base_filename = f"extracted_data_{i}"
            # Save normal variant
            img.save(os.path.join(output_dir, f"{base_filename}.png"))
            with open(os.path.join(output_dir, f"{base_filename}.txt"), "w", encoding="utf-8") as f:
                f.write(lbl)
            
            # Save palm leaf variant
            if palm_leaf_enabled:
                palm_img = apply_palm_leaf_effect(img)
                palm_img.save(os.path.join(output_dir, f"{base_filename}_palmleaf.png"))
                with open(os.path.join(output_dir, f"{base_filename}_palmleaf.txt"), "w", encoding="utf-8") as f:
                    f.write(lbl)
                
            if (i+1) % 50 == 0:
                print(f"Generated {i+1} / {total_images_to_generate} items...")
                
        print("\nSuccess! Generated augmented OCR dataset.")
        if palm_leaf_enabled:
            print(f"Total output: {total_images_to_generate} normal + {total_images_to_generate} palm leaf = {total_images_to_generate * 2} images")
        print(f"Dataset saved to: {os.path.abspath(output_dir)}")
        
    except Exception as e:
         import traceback
         print(f"An error occurred during dataset generation: {e}")
         traceback.print_exc()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extracts text from a Tamil image and generates an augmented OCR dataset.')
    parser.add_argument('image_path', help='Path to the input image file (e.g., sample.png)')
    parser.add_argument('--out_dir', default='./dataset/extracted/', help='Directory to save output dataset (default: ./dataset/extracted/)')
    parser.add_argument('--fonts', default='./fonts/tamil/', help='Directory containing .ttf Tamil fonts (default: ./fonts/tamil/)')
    parser.add_argument('--count_per_line', type=int, default=5, help='Number of augmented images to generate per extracted text line (default: 5)')
    parser.add_argument('--palm_leaf', action='store_true', default=True, help='Generate palm leaf manuscript (allasuvadi) variants (default: enabled)')
    parser.add_argument('--no_palm_leaf', action='store_true', help='Disable palm leaf manuscript variant generation')
    
    args = parser.parse_args()
    
    palm_leaf_mode = args.palm_leaf and not args.no_palm_leaf
    
    print(f"Processing image: {args.image_path}")
    
    # 1. Extract and clean text
    extracted_lines = extract_sentences_from_image(args.image_path, lang='tam')
    
    # 2. Generate augmented data
    generate_dataset(
        sentences=extracted_lines,
        output_dir=args.out_dir,
        font_dir=args.fonts,
        num_images_per_line=args.count_per_line,
        palm_leaf=palm_leaf_mode
    )
