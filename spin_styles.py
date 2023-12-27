
"""
spin_styles.py

This module contains utilities for handling images and image data.

Functions:
    save_image_from_url(url, save_path): Downloads an image from a given URL and saves it to a specified path.

Classes:
    ImageData: A class that holds information about an image, including remote and local URLs and original and revised prompts.

Imports:
    os, time, json, uuid, urllib: Standard library modules for various utility functions.
    BytesIO: A class for handling binary data in memory.
    Path: A class for handling filesystem paths.
    Image: A module for handling image data.
    requests: A module for making HTTP requests.
    OpenAI: A module for interacting with the OpenAI API.
"""

import os
import time
import uuid
import urllib
from io import BytesIO
from pathlib import Path
from PIL import Image
import requests
from openai import OpenAI
import deal


@deal.pre(lambda _: _.url.startswith("http"))
@deal.pre(lambda _: isinstance(_.url, str))
@deal.pre(lambda _: isinstance(_.save_path, Path))
@deal.ensure(lambda _: _.save_path.exists())
def save_image_from_url(url, save_path):
    """
    Downloads an image from the given URL and saves it to the specified path.

    Args:
        url (str): The URL of the image to download.
        save_path (Path): The path where the downloaded image will be saved.
    """
    response = requests.get(url, timeout=10)
    img = Image.open(BytesIO(response.content))
    img.save(save_path)


class ImageData:
    def __init__(
        self, remote_image_url: str, original_prompt: str, revised_prompt: str
    ):
        self.remote_image_url = remote_image_url
        self.local_image_absolute_path = ""
        self.original_prompt = original_prompt
        self.revised_prompt = revised_prompt

    def download_image_sync(self, local_folder: Path, file_prefix: str):

        local_path = local_folder / Path(f"{file_prefix}-{uuid.uuid4()}.png")

        local_absolute_path = local_path.resolve()

        save_image_from_url(self.remote_image_url, local_absolute_path)

        self.local_image_absolute_path = local_absolute_path

        print(f"Image local URL: {self.local_image_absolute_path}")


def generate_html_table(image_data_list):
    """
    Generate an HTML table with image data.

    Args:
        image_data_list (list): A list of ImageData objects.

    Returns:
        str: The HTML table as a string.
    """
    html = "<table>\n"
    html += "<tr><th>Image</th><th>Original Prompt</th><th>Revised Prompt</th></tr>\n"

    for image_data in image_data_list:
        html += "<tr>\n"

        image_url = urllib.parse.urljoin(
            "file:", urllib.parse.quote(str(image_data.local_image_absolute_path))
        )
        html += f"<td><img src='{image_url}' alt='Image'></td>\n"
        html += f"<td>{image_data.original_prompt}</td>\n"
        html += f"<td>{image_data.revised_prompt}</td>\n"
        html += "</tr>\n"

    html += "</table>"
    return html


def save_html_to_file(html_string, filename):
    """
    Save the given HTML string to a file.

    Args:
        html_string (str): The HTML string to be saved.
        filename (str): The name of the file to save the HTML to.

    Returns:
        None
    """
    with open(filename, "w", encoding="utf8") as file:
        file.write(html_string)


def generate_image_sync(i_openai_client, i_prompt:str, i_folder_path:Path, i_file_prefix:str) -> ImageData:
    response = i_openai_client.images.generate(
        model="dall-e-3", prompt=i_prompt, size="1024x1024", quality="standard", n=1
    )

    if response.data is None:
        raise RuntimeError("OpenAI API returned an error: ", response.error)

    if len(response.data) != 1:
        raise RuntimeError("OpenAI API returned unexpected number of images.")

    # .data is expected to be an array of image objects
    # https://platform.openai.com/docs/api-reference/images/object
    image_url = response.data[0].url
    image_revised_prompt = response.data[0].revised_prompt

    image_data = ImageData(image_url, i_prompt, image_revised_prompt)
    image_data.download_image_sync(i_folder_path, i_file_prefix)
    return image_data


def spin_styles_sync(i_prompt, i_folder_path:Path):
    # Create a folder if it does not exist
    print(f"Creating folder {i_folder_path}...")

    Path(i_folder_path).mkdir(parents=True, exist_ok=True)

    # Create an OpenAI client
    client = OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),
    )

    # List of styles
    styles = [
        "Abstract Art",
        "Abstract Geometry",
        "Photorealism",
    ]
    #     "Art Deco",
    #     "Art Nouveau",
    #     "Bauhaus",
    #     "Bokeh Art",
    #     "Brutalism in design",
    #     "Byzantine Art",
    #     "Celtic Art",
    #     "Charcoal",
    #     "Chinese Brush Painting",
    #     "Chiptune Visuals",
    #     "Concept Art",
    #     "Constructivism",
    #     "Cyber Folk",
    #     "Cybernetic Art",
    #     "Cyberpunk",
    #     "Dadaism",
    #     "Data Art",
    #     "Digital Collage",
    #     "Digital Cubism",
    #     "Digital Impressionism",
    #     "Digital Painting",
    #     "Double Exposure",
    #     "Dreamy Fantasy",
    #     "Dystopian Art",
    #     "Etching",
    #     "Expressionism",
    #     "Fauvism",
    #     "Flat Design",
    #     "Fractal Art",
    #     "Futurism",
    #     "Glitch Art",
    #     "Gothic Art",
    #     "Gouache",
    #     "Greco-Roman Art",
    #     "Impressionism",
    #     "Ink Wash",
    #     "Isometric Art",
    #     "Japanese Ukiyo-e",
    #     "Kinetic Typography",
    #     "Lithography",
    #     "Low Poly",
    #     "Macabre Art",
    #     "Magic Realism",
    #     "Minimalism",
    #     "Modernism",
    #     "Monogram",
    #     "Mosaic",
    #     "Neon Graffiti",
    #     "Neon Noir",
    #     "Origami",
    #     "Papercut",
    #     "Parallax Art",
    #     "Pastel Drawing",
    #     "Photorealism",
    #     "Pixel Art",
    #     "Pointillism",
    #     "Polyart",
    #     "Pop Art",
    #     "Psychedelic Art",
    #     "Rennaissance/Baroque",
    #     "Retro Wave",
    #     "Romanticism",
    #     "Sci-Fi Fantasy",
    #     "Scratchboard",
    #     "Steampunk",
    #     "Stippling",
    #     "Surrealism",
    #     "Symbolism",
    #     "Trompe-l'eil",
    #     "Vaporwave",
    #     "Vector Art",
    #     "Voxel Art",
    #     "Watercolor",
    #     "Woodblock Printing",
    #     "Zen Doodle",
    # ]

    # Loop through the styles
    rate_limit_delay_sec = 1
    for style in styles:
        # Wait 15 seconds:
        print(f"Waiting for {rate_limit_delay_sec} seconds to avoid rate limit...")

        time.sleep(rate_limit_delay_sec)

        print(f"Generating image in the style of {style}...")

        styled_prompt = i_prompt + ", in the style of " + style

        try:
            file_prefix = style.lower().replace(" ", "_")
            new_generated_entry = generate_image_sync(client, styled_prompt, i_folder_path, file_prefix)

            print(f"Image {new_generated_entry.local_image_absolute_path} saved.")

        except Exception as e:
            print(f"Error generating image in style of {style}: {e}")


# spin_styles_sync("Christmas", "/home/nikolai3d/Dropbox/AdobeFirefly/Style Spin/christmas_sd")


ai_client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

# test_image = generate_image_sync(
#     ai_client,
#     "Multiple Kittens of various breeds, playing in and around a Christmas tree",
# )


spin_styles_sync("2 cats and a dog celebrating a birthday", Path("/home/nikolai3d/Dropbox/AdobeFirefly/Style Spin/birthday_sd"))

# test_image_list = [test_image]

# html_table = generate_html_table(test_image_list)

# save_html_to_file(html_table, "./test_images/test.html")
