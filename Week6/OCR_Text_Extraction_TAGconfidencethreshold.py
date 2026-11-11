# Azure Computer Vision - OCR (Text Extraction)
# Modern API v4.0+ using READ feature

#mport the required libraries
import os
import logging
from dotenv import load_dotenv
from azure.ai.vision.imageanalysis import ImageAnalysisClient
from azure.ai.vision.imageanalysis.models import VisualFeatures
from azure.core.credentials import AzureKeyCredential

#Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()

# ============================================================
# Load credentials and define the tag threshold
# ============================================================

ENDPOINT = os.getenv("AZURE_VISION_ENDPOINT")
KEY = os.getenv("AZURE_VISION_KEY")

# Only show tags at or above this confidence (0.0 - 1.0)
TAG_CONFIDENCE_THRESHOLD = 0.7

# ============================================================
# Create the Azure client
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

# Select the remote image,Image with text and Stores the URL of the image to analyse.
read_image_url = "https://learn.microsoft.com/azure/ai-services/computer-vision/media/quickstarts/presentation.png"


print(f"\nExtracting text from: {read_image_url}\n")

try:
    logger.info("Sending request to Azure Computer Vision...")#Request OCR and image tags
    result = client.analyze_from_url( 
        image_url=read_image_url,
        visual_features=[VisualFeatures.READ,VisualFeatures.TAGS],
        language="en"
    )
    logger.info("Response received.")
    
    # Filter and display tags,Print tags above the confidence threshold
    if result.tags is not None:
        confident_tags = [t for t in result.tags.list if t.confidence >= TAG_CONFIDENCE_THRESHOLD]
        print(f"TAGS (confidence >= {TAG_CONFIDENCE_THRESHOLD:.0%}):")
        print("-"*80)
        for tag in sorted(confident_tags, key=lambda t: t.confidence, reverse=True):
            print(f"  {tag.name:25s} {tag.confidence:.2%}")
        print(f"  ({len(result.tags.list) - len(confident_tags)} low-confidence tags filtered out)")
        print()

    # Print extracted text
    if result.read and len(result.read.blocks) > 0:
        print("EXTRACTED TEXT:")
        print("-"*80)
        
        # Iterate through text blocks,Display each block and line
        for block_idx, block in enumerate(result.read.blocks, 1):
            print(f"\nText Block {block_idx}:")
            
            # Iterate through lines
            for line_idx, line in enumerate(block.lines, 1):
                print(f"  Line {line_idx}: {line.text}")
                print(f"  Bounding box: {line.bounding_polygon}")
                
                # Optional: Show individual words
                # Uncomment to see word-level details
                for word in line.words:
                    print(f"    Word: '{word.text}' (confidence: {word.confidence:.2%})")
        
        # Print all text together,Combine the extracted lines
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
#Handle errors and print the final message     
except Exception as e:
    logger.error("Failed to analyse image: %s", e)

print("\n" + "="*80)
print("OCR Complete!")
print("="*80)