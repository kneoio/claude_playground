import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def classify_image(client, image_data):
    logger.info("Sending image data to classify_image")

    response = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": image_data}},
                    {"type": "text",
                     "text": "Please classify this image as 'fuel_pump', 'odometer', or 'undefined'. Respond only with a JSON object containing 'classification' and 'confidence' fields. If the image is not clearly a fuel pump or odometer, set 'classification' to 'undefined' with a confidence of 0.0."}
                ]
            }
        ]
    )

    # Parse JSON directly from text response
    raw_text = response.content[0].text
    logger.info(f"Raw JSON response text: {raw_text}")

    try:
        result = json.loads(raw_text)
        classification = result.get("classification")
        confidence = result.get("confidence")

        # Log and return only if classification is relevant
        logger.info(f"Classification: {classification}, Confidence: {confidence}")

        # Return undefined with error handling if relevant
        if classification == "undefined":
            logger.error("Image could not be classified as either fuel_pump or odometer.")
            return json.dumps({"classification": "undefined", "confidence": 0.0})

        return json.dumps({"classification": classification, "confidence": confidence})

    except (json.JSONDecodeError, TypeError, KeyError):
        logger.error("Failed to parse JSON from Claude's response")
        return json.dumps({"classification": "undefined", "confidence": 0.0})


def read_odometer(client, image_data):
    logger.info("Sending image data to read_odometer")

    response = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": image_data}},
                    {"type": "text",
                     "text": "Please read the odometer value from this image and respond only with a JSON object like {\"total_km\": <value>, \"confidence\": <value>}."}
                ]
            }
        ]
    )

    # Parse JSON directly from text response
    raw_text = response.content[0].text
    logger.info(f"Raw JSON response text: {raw_text}")

    try:
        result = json.loads(raw_text)
        total_km = result.get("total_km")
        confidence = result.get("confidence")
        logger.info(f"Total KM: {total_km}, Confidence: {confidence}")
        return json.dumps({"total_km": total_km, "confidence": confidence})
    except (json.JSONDecodeError, TypeError, KeyError):
        logger.error("Failed to parse JSON from Claude's response for odometer")
        return json.dumps({"total_km": 0.0, "confidence": 0.0})


def read_fuel_pump(client, image_data):
    logger.info("Sending image data to read_fuel_pump")

    response = client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": image_data}},
                    {"type": "text",
                     "text": "Please read the fuel volume, cost, and currency from this fuel pump image and respond only with a JSON object like {\"volume\": <value>, \"cost\": <value>, \"currency\": \"<currency>\", \"confidence\": <value>}."}
                ]
            }
        ]
    )

    # Parse JSON directly from text response
    raw_text = response.content[0].text
    logger.info(f"Raw JSON response text: {raw_text}")

    try:
        result = json.loads(raw_text)
        volume = result.get("volume")
        cost = result.get("cost")
        currency = result.get("currency")
        confidence = result.get("confidence")
        logger.info(f"Volume: {volume}, Cost: {cost}, Currency: {currency}, Confidence: {confidence}")
        return json.dumps({
            "volume": volume,
            "cost": cost,
            "currency": currency,
            "confidence": confidence
        })
    except (json.JSONDecodeError, TypeError, KeyError):
        logger.error("Failed to parse JSON from Claude's response for fuel pump")
        return json.dumps({
            "volume": 0.0,
            "cost": 0.0,
            "currency": "unknown",
            "confidence": 0.0
        })
