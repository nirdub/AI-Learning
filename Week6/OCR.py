# Azure Computer Vision - OCR (Text Extraction)
# Modern API v4.0+ using READ feature

import os
import logging #for logging creating req getting response etc, logs can be from python or from azure services, logging is used to log the information about the request and response, errors etc.
from dotenv import load_dotenv
from azure.ai.vision.imageanalysis import ImageAnalysisClient #to send request to azure computer vision service and get response, this is the main client class that is used to interact with the Azure Computer Vision service.
from azure.ai.vision.imageanalysis.models import VisualFeatures #azure.ai.vision.imageanalysis.models is a module that contains the VisualFeatures class, which is used to specify the visual features to analyze in an image, such as READ for text extraction.
from azure.core.credentials import AzureKeyCredential
#configure Logging to log the information about the request and response, errors etc. The logging level is set to INFO, which means that all messages at this level and above will be logged. The format specifies how the log messages will be displayed, including the timestamp, log level, and message.
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()

# ============================================================
# CONFIGURATION
# ============================================================

ENDPOINT = os.getenv("AZURE_VISION_ENDPOINT")
KEY = os.getenv("AZURE_VISION_KEY")

#TAG_THRESHOLD_CONFIDENCE = 0.7  # extract only tags with confidence >= 70%
# ============================================================
# Initialize Client
# ============================================================

client = ImageAnalysisClient(
    endpoint=ENDPOINT,
    credential=AzureKeyCredential(KEY)
)

# ============================================================
# OCR - READ FILE FROM URL
# ============================================================

print("="*80)
print("OCR: READ FILE - REMOTE IMAGE")
print("="*80)

# Image with text, a remote URL to an image containing text, stores the URL of the image to be analyzed. 
read_image_url = "https://learn.microsoft.com/azure/ai-services/computer-vision/media/quickstarts/presentation.png"

print(f"\nExtracting text from: {read_image_url}\n")
#sendind the request to the Azure Computer Vision service using the analyze_from_url method of the ImageAnalysisClient. The method takes the image URL, a list of visual features to analyze (in this case, VisualFeatures.READ for text extraction), and the language of the text to be extracted (English in this case). The response is stored in the result variable.
try:
    logger.info("Sending request to Azure Computer Vision...")
    result = client.analyze_from_url(
        image_url=read_image_url,
        visual_features=[VisualFeatures.READ], #read can extract printed and handwritten text from images, including text in different languages and orientations. It can also detect text in complex backgrounds and low-contrast images.
        language="en"
    )
    logger.info("Response received.")
    
    # Print extracted text
    if result.read and len(result.read.blocks) > 0:
        print("EXTRACTED TEXT:")
        print("-"*80)
        
        # Iterate through text blocks and extract lines. Blocks are groups of lines that are detected in the image. Each block can contain multiple lines of text, and each line can contain multiple words. The code iterates through each block and then through each line within the block, printing the text and bounding box information for each line.
        for block_idx, block in enumerate(result.read.blocks, 1): #starts reading from the first block and enumerates through the blocks, starting the index at 1. For each block, it prints the block index and then iterates through the lines within that block.
            print(f"\nText Block {block_idx}:")
            
            # Iterate through lines and print text and bounding box information
            for line_idx, line in enumerate(block.lines, 1):
                print(f"  Line {line_idx}: {line.text}")
                print(f"  Bounding box: {line.bounding_polygon}") #when lines are not straight but tilted or curved, the bounding box may not accurately represent the area of the text. In such cases, the bounding polygon provides a more accurate representation of the text's location in the image.
                #bounding boxes need not necessarily be rectangular. They can be polygons with any number of sides, depending on the shape of the text region. The bounding polygon is represented as a list of points, where each point is a tuple of (x, y) coordinates.
                # Optional: Show individual words
                # Uncomment to see word-level details
                # for word in line.words:
                #     print(f"    Word: '{word.text}' (confidence: {word.confidence:.2%})")
        
        # Print all text together
        print("\n" + "="*80)
        print("FULL TEXT (Combined):")
        print("="*80)
        all_text = []
        for block in result.read.blocks:
            for line in block.lines:
                all_text.append(line.text)
        
        print("\n".join(all_text))
        
    else:
        print("No text detected in the image.")
        
except Exception as e:
    logger.error("Failed to analyse image: %s", e)

print("\n" + "="*80)
print("OCR Complete!")
print("="*80)