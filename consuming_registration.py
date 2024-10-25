import base64
import json
import anthropic
import os
import requests
import logging
from dotenv import load_dotenv
from models import VehicleData
from PIL import Image
import io

from tool_handler import classify_image, read_odometer, read_fuel_pump

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
API_BASE_URL = os.getenv('API_BASE_URL')
APP_NAME = os.getenv('APP_NAME')
JWT_TOKEN = os.getenv('JWT_TOKEN')

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def resize_image_data(base64_data, max_width):
    img_data = base64.b64decode(base64_data)
    with Image.open(io.BytesIO(img_data)) as img:
        img.thumbnail((max_width, int((img.height / img.width) * max_width)), Image.LANCZOS)
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        return base64.b64encode(buffer.getvalue()).decode('utf-8')


def load_tool_definitions(directory):
    tools = []
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            with open(os.path.join(directory, filename), 'r') as file:
                tools.append(json.load(file))
    return tools


tools = load_tool_definitions('tools')


def load_image(file_path):
    with open(file_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


image_data_tuple = (
    load_image("C:/Users/justa/tmp/q_tracker/display-on-a-filling-station-fuel-pump-DXM851.jpg"),
    load_image("C:/Users/justa/tmp/q_tracker/vehicle-odometer.jpg")
)

vehicle_data = VehicleData(
    vehicleId="7ea1d394-c739-4c77-9428-8b93e6535981",
    totalKm=0,
    lastLiters=0,
    lastCost=0,
    addInfo={"service": "Image processing", "location": "Automated"}
)

all_results = []
for image_data in image_data_tuple:
    response = classify_image(client, image_data)
    classification = json.loads(response).get("classification")

    if classification == "undefined":
        logger.error("Skipping image due to undefined classification.")
        continue
    if classification == "odometer":
        odometer_result = read_odometer(client, image_data)
        result = json.loads(odometer_result)
        vehicle_data.totalKm = result["total_km"]
        print(f"Odometer data: {odometer_result}")
        all_results.append(odometer_result)
        vehicle_data.add_image(
            image_data=resize_image_data(image_data, 400),
            image_type="odometer",
            confidence=result["confidence"],
            description="Odometer reading",
            add_info={}
        )
    elif classification == "fuel_pump":
        fuel_pump_result = read_fuel_pump(client, image_data)
        result = json.loads(fuel_pump_result)
        vehicle_data.lastLiters = result["volume"]
        print(f"Fuel Pump data: {fuel_pump_result}")
        all_results.append(fuel_pump_result)
        vehicle_data.add_image(
            image_data=resize_image_data(image_data, 400),
            image_type="fuel_pump",
            confidence=result["confidence"],
            description="Fuel pump reading",
            add_info={}
        )

print("All results:")
print(json.dumps(all_results, indent=2))

headers = {
    'Authorization': f'Bearer {JWT_TOKEN}',
    'Content-Type': 'application/json'
}

payload = vehicle_data.to_dict()
response = requests.post(f"{API_BASE_URL}/api/{APP_NAME}/consumings/", json=payload, headers=headers)
