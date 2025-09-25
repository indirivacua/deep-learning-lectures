import os
import base64

def convert_image_to_base64(image_path):
    """Convert an image to a base64-encoded string."""
    try:
        image_path = os.path.abspath(image_path)
        if not os.path.exists(image_path):
            print(f"Image not found: {image_path}")
            return None
        
        with open(image_path, "rb") as img:
            base64_string = base64.b64encode(img.read()).decode()
            return f'<div style="text-align: center;"><img src="data:image/png;base64,{base64_string}" alt="image" /></div>'

    except Exception as e:
        print(f"Error converting {image_path}: {e}")
        return None

def process_md(file_path):
    """Process the markdown file and embed base64 images."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        output_file = file_path.replace(".md", "_embed.md")
        with open(output_file, "w", encoding="utf-8") as f_out:
            for line in lines:
                # Find image paths within backticks
                if '`' in line:
                    image_path = line.split('`')[1].strip()  # Take text between backticks
                    base64_image = convert_image_to_base64(image_path)
                    if base64_image:
                        line = base64_image + '\n'  # Add base64 image and a newline
                f_out.write(line)

        print(f"Processed file saved as {output_file}")

    except Exception as e:
        print(f"Error processing {file_path}: {e}")

file_path = 'index.md'
process_md(file_path)
