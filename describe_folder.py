from pathlib import Path
from openai import OpenAI
import os
import base64
import requests
import json

api_key = os.environ.get("OPENAI_API_KEY")


# Function to encode the image
def encode_image(image_path: Path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def pretty_print_json(json_string):
    parsed_json = json.loads(json_string)
    print(json.dumps(parsed_json, indent=4))

def generate_description_path(image_path: Path) -> Path:
    return image_path.with_stem(image_path.stem + "_desc").with_suffix(".txt")

def get_image_mime_type(image_path: Path) -> str:
    extension = image_path.suffix.lower()
    if extension == '.jpg' or extension == '.jpeg':
        return 'image/jpeg'
    elif extension == '.png':
        return 'image/png'
    
    raise Exception(f"Unknown image extension {extension}")


def describe_image(client, i_file_path: Path) -> str:
    """
    Generate a description for a single image.

    :param client: OpenAI client
    :param i_file_path: Path to the image
    :return: Description of the image
    """

    # Getting the base64 string
    print(f"Generating description for {i_file_path}")
    print("Encoding image...")
    base64_image = encode_image(i_file_path)

    image_mime_type = get_image_mime_type(i_file_path)

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

    payload = {
        "model": "gpt-4-vision-preview",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text", 
                        "text": "Describe this image"
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{image_mime_type};base64,{base64_image}"},
                    },
                ],
            }
        ],
        "max_tokens": 300,
    }

    print("Sending request to Open AI...")
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=50,
    )

    # pretty_print_json(str(response.json()))
    response_json = response.json()
    # print(json.dumps(response.json(), indent=4))
    
    response_string = response_json["choices"][0]["message"]["content"]
    # print(response_string)

    # Write the response to a file
    description_path = generate_description_path(i_file_path)
    print(f"Writing description to {description_path}")
    with open(description_path, "w", encoding="utf-8") as description_file:
        description_file.write(response_string)



def generate_image_descriptions(client, i_folder_path: Path):
    """
    Generate image descriptions for all images in a folder.

    :param client: OpenAI client
    :param i_folder_path: Path to the folder containing the images
    """
    for i_file_path in i_folder_path.glob("*"):
        if i_file_path.is_file():
            try:
                describe_image(client, i_file_path)
            except Exception as e:
                print(f"Failed to describe image {i_file_path}")
                print(e)


ai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

generate_image_descriptions(ai_client, Path("/home/nikolai3d/Dropbox/AdobeFirefly/Screenshots/PTR/"))


# describe_image(ai_client, Path("/home/nikolai3d/Dropbox/AdobeFirefly/Style Spin/AI Bug.png"))
