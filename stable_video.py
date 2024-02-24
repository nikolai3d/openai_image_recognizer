import requests
import os
import time
from pathlib import Path
import deal
import random
from PIL import Image

stability_api_key = os.environ.get("STABILITY_API_KEY")


@deal.pre(lambda _: _.input_path.exists())
@deal.pre(lambda _: isinstance(_.input_path, Path))
@deal.pre(lambda _: isinstance(_.output_path, Path))
@deal.ensure(lambda _: _.output_path.exists())
def resize_square_image(input_path: Path, output_path: Path):
    with Image.open(input_path) as img:
        if img.width != img.height:
            raise ValueError("Image is not square")
        img_resized = img.resize((768, 768))
        img_resized.save(output_path, "PNG")


def random_seed():
    return random.randint(1, 4294967294)

@deal.pre(lambda _: _.square_image_path.exists())
@deal.pre(lambda _: isinstance(_.square_image_path, Path))
def start_video_generation(square_image_path: Path):
    with open(square_image_path, "rb") as image_file:
        response = requests.post(
            "https://api.stability.ai/v2alpha/generation/image-to-video",
            headers={"authorization": f"Bearer {stability_api_key}"},
            files={"image": image_file},
            data={
                "seed": random_seed(),
                "cfg_scale": 4,
                "motion_bucket_id": 200,
            },
            timeout=50,
        )

        print("Generation ID:", response.json().get("id"))
        return response.json().get("id")


def retrieve_video_generation_status(generation_id):
    print(f"Retrieving video for generation {generation_id}...")
    response = requests.request(
        "GET",
        f"https://api.stability.ai/v2alpha/generation/image-to-video/result/{generation_id}",
        headers={
            "Accept": "video/*",  # Use 'application/json' to receive base64 encoded JSON
            "authorization": f"Bearer {stability_api_key}",
        },
        timeout=50,
    )

    if response.status_code == 202:
        print("Generation in-progress, try again in 10 seconds.")
        return 202
    elif response.status_code == 200:
        print("Generation complete!")
        with open("video.mp4", "wb") as file:
            file.write(response.content)
            return 0
    else:
        raise Exception(str(response.json()))


input_path = Path("cat.png")
resized_path = Path("cat_resized_768.png")
print("Resizing image...")
resize_square_image(input_path, resized_path)

print("Starting video generation...")
gen_id = start_video_generation(resized_path)

while retrieve_video_generation_status(gen_id) == 202:
    print("Waiting 10 seconds...")
    time.sleep(10)
