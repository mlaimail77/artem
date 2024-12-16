
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

def combine_images(urls, output_size=(1000, 1000)):
    """
    Combines multiple images from URLs into a single image in a grid layout with labels.
    
    Args:
        urls (list): List of dicts containing image URLs and names to combine
        output_size (tuple): Desired size of output image (width, height)
        
    Returns:
        PIL.Image: Combined image with labels
    """
    # Download and open all images
    images = []
    for url_data in urls:
        response = requests.get(url_data["url"])
        img = Image.open(BytesIO(response.content))
        images.append((img, url_data["name"]))
    
    # Calculate grid dimensions
    n = len(images)
    cols = int(n ** 0.5)  # Square root for grid layout
    rows = (n + cols - 1) // cols  # Ceiling division
    
    # Calculate cell size
    cell_width = output_size[0] // cols
    cell_height = output_size[1] // rows
    
    # Create blank output image
    combined = Image.new('RGB', output_size, 'white')
    
    # Create drawing object for text
    draw = ImageDraw.Draw(combined)
    
    # Try to load a font, fall back to default if not available
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        font = ImageFont.load_default()
    
    # Paste each image into grid
    for idx, (img, name) in enumerate(images):
        # Calculate position
        row = idx // cols
        col = idx % cols
        
        # Resize image to fit cell while maintaining aspect ratio
        img_aspect = img.width / img.height
        cell_aspect = cell_width / cell_height
        
        # Leave space for text at top of cell
        text_height = 30
        image_cell_height = cell_height - text_height
        
        if img_aspect > cell_aspect:
            # Image is wider than cell
            new_width = cell_width
            new_height = int(cell_width / img_aspect)
        else:
            # Image is taller than cell
            new_height = image_cell_height
            new_width = int(image_cell_height * img_aspect)
            
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Calculate centering position
        x = col * cell_width + (cell_width - new_width) // 2
        y = row * cell_height + text_height + (image_cell_height - new_height) // 2
        
        # Paste image
        combined.paste(img, (x, y))
        
        # Add text above image
        text_x = col * cell_width + (cell_width // 2)
        text_y = row * cell_height + 5
        text_bbox = draw.textbbox((text_x, text_y), name, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        # Center text horizontally
        draw.text((text_x - text_width//2, text_y), name, fill='black', font=font)
    
    return combined
