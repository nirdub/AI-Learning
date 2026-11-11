# pip install azure-cognitiveservices-vision-customvision msrest
#The below code imports the necessary libraries and modules for working with Azure Custom Vision services, including training and prediction clients, as well as handling image uploads and authentication.
import os, time, uuid, logging
from dotenv import load_dotenv
from azure.cognitiveservices.vision.customvision.training import CustomVisionTrainingClient
from azure.cognitiveservices.vision.customvision.prediction import CustomVisionPredictionClient
from azure.cognitiveservices.vision.customvision.training.models import ImageFileCreateBatch, ImageFileCreateEntry
from msrest.authentication import ApiKeyCredentials
# The below code sets up logging configuration to display log messages with timestamps and severity levels. It also loads environment variables from a .env file, which contains sensitive information like API keys and endpoints for Azure Custom Vision services.
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

load_dotenv()

# ── Credentials from .env ─────────────────────────────────────────────────────
TRAINING_ENDPOINT      = os.getenv("CUSTOM_VISION_TRAINING_ENDPOINT")
training_key           = os.getenv("CUSTOM_VISION_TRAINING_KEY")
PREDICTION_ENDPOINT    = os.getenv("CUSTOM_VISION_PREDICTION_ENDPOINT")
prediction_key         = os.getenv("CUSTOM_VISION_PREDICTION_KEY")
prediction_resource_id = os.getenv("CUSTOM_VISION_PREDICTION_RESOURCE_ID")  

publish_iteration_name = "classifyModeltdai" #name of training project iteration to be published to the prediction resource



# ── Clients — each pointed at its own separate Azure resource ─────────────────
training_credentials   = ApiKeyCredentials(in_headers={"Training-key": training_key})
prediction_credentials = ApiKeyCredentials(in_headers={"Prediction-key": prediction_key})

with CustomVisionTrainingClient(TRAINING_ENDPOINT, training_credentials) as trainer, \
     CustomVisionPredictionClient(PREDICTION_ENDPOINT, prediction_credentials) as predictor:

    # ── Clean up existing projects ────────────────────────────────────────────
    for project in trainer.get_projects():
        for iteration in trainer.get_iterations(project.id):
            # The below if loop checks if the iteration has a publish name, and if so, it unpublishes the iteration from the project. After that, it deletes the project itself. This ensures that any existing projects and their iterations are cleaned up before creating a new project for training.
            if iteration.publish_name:
                trainer.unpublish_iteration(project.id, iteration.id)
        trainer.delete_project(project.id)
        logger.info("Deleted existing project: %s", project.name)

    # ── Create a new project training project ──────────────────────────────────────────────────
    logger.info("Creating new project...")
    project_name = str(uuid.uuid4())
    project = trainer.create_project(project_name)

    # ── Create tags for the images ────────────────────────────────────────────────────────────
    hemlock_tag = trainer.create_tag(project.id, "Hemlock") #will tag the images of Hemlock trees under hemlock folder as hemlock_tag and images of Japanese Cherry trees under Japanese_Cherry folder as cherry_tag
    cherry_tag  = trainer.create_tag(project.id, "Japanese Cherry")

    # ── Upload images ─────────────────────────────────────────────────────────
    base_image_location = os.path.join(os.path.dirname(__file__), "Images")
    logger.info("Uploading training images...")

    image_list = []

    for image_num in range(1, 11):
        file_name = f"hemlock_{image_num}.jpg"
        with open(os.path.join(base_image_location, "Hemlock", file_name), "rb") as f:
            image_list.append(
                ImageFileCreateEntry(name=file_name, contents=f.read(), tag_ids=[hemlock_tag.id]) #opening the images of Hemlock trees under hemlock folder and reading them as binary data and appending them to the image_list with the tag_id of hemlock_tag
            )

    for image_num in range(1, 11):
        file_name = f"japanese_cherry_{image_num}.jpg"
        with open(os.path.join(base_image_location, "Japanese_Cherry", file_name), "rb") as f:
            image_list.append(
                ImageFileCreateEntry(name=file_name, contents=f.read(), tag_ids=[cherry_tag.id])
            )
    # The below code uploads the images in batches to the Custom Vision project. It creates an ImageFileCreateBatch object containing the list of images and their associated tags, and then calls the create_images_from_files method of the trainer client to upload the images. If the upload is not successful, it logs an error message for each image and raises a SystemExit exception to terminate the program.
    upload_result = trainer.create_images_from_files(
        project.id, ImageFileCreateBatch(images=image_list)
    )
    if not upload_result.is_batch_successful:
        logger.error("Image batch upload failed.")
        for image in upload_result.images:
            logger.error("  Image status: %s", image.status)
        raise SystemExit(1)

    # ── Training the model we are interating only once here but can do multiple times ─────────────────────────────────────────────────────────────────
    # The below code 
    logger.info("Training model...")
    iteration = trainer.train_project(project.id)
    while iteration.status != "Completed":
        iteration = trainer.get_iteration(project.id, iteration.id)
        logger.info("Training status: %s — waiting 10 s...", iteration.status)
        time.sleep(10)

    # ── Publish iteration to the prediction resource ──────────────────────────
    trainer.publish_iteration(project.id, iteration.id, publish_iteration_name, prediction_resource_id)
    logger.info("Iteration published. Running test prediction...")

    # ── Predict (uses the separate Prediction resource endpoint) ──────────────
    # The below code performs a prediction on a test image using the trained model. It opens the test image file, reads its contents, and calls the classify_image method of the predictor client to get the prediction results. It then iterates through the predictions and prints the tag name along with its probability percentage.
    test_image_path = os.path.join(base_image_location, "Test", "test_image.jpg")
    with open(test_image_path, "rb") as image_contents:
        results = predictor.classify_image(project.id, publish_iteration_name, image_contents.read())

    for prediction in results.predictions:
        print(f"  {prediction.tag_name}: {prediction.probability * 100:.2f}%")