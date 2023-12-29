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
    """
    Holds information about an image, including remote and local URLs and original and revised prompts.

    Can be created with a remote image URL and original and revised prompts.

    Attributes:
        remote_image_url (str): The remote URL of the image.
        local_image_absolute_path (Path): The local absolute path of the image (initally empty), filled after download_image_sync is called.
        original_prompt (str): The original prompt used to generate the image.
        revised_prompt (str): The revised prompt used to generate the image.
    """

    def __init__(
        self, original_prompt: str
    ):
        self.original_prompt = original_prompt
        self.remote_image_url = ""
        self.local_image_absolute_path = ""
        self.revised_prompt = ""

    @deal.pre(lambda _: len(_.self.original_prompt) > 0) # Can't generate image without a prompt
    @deal.pre(lambda _: isinstance(_.self.original_prompt, str))
    @deal.pre(lambda _: len(_.self.remote_image_url) == 0) # Can't generate image if it's already been generated
    @deal.pre(lambda _: len(_.self.revised_prompt) == 0) # Can't generate image if it's already been generated
    @deal.pre(lambda _: len(_.self.local_image_absolute_path) == 0) # Can't generate image if it's already downloaded
    @deal.ensure(lambda _: len(_.self.remote_image_url) > 0)
    @deal.ensure(lambda _: len(_.self.revised_prompt) > 0)
    @deal.ensure(lambda _: isinstance(_.self.remote_image_url, str))
    @deal.ensure(lambda _: isinstance(_.self.revised_prompt, str))
    def generate_image_sync(self, openai_client: OpenAI):
        """
        Generates an image synchronously from a prompt.

        Args:
            openai_client (OpenAI): The OpenAI client to use for generating the image.
        """

        # https://platform.openai.com/docs/api-reference/images/create
        response = openai_client.images.generate(
            model="dall-e-3", prompt=self.original_prompt, size="1024x1024", quality="hd", n=1
        )

        if response.data is None:
            raise RuntimeError("OpenAI API returned an error: ", response.error)

        if len(response.data) != 1:
            raise RuntimeError("OpenAI API returned unexpected number of images.")

        # .data is expected to be an array of image objects
        # https://platform.openai.com/docs/api-reference/images/object
        image_url = response.data[0].url
        image_revised_prompt = response.data[0].revised_prompt

        self.remote_image_url = image_url
        self.revised_prompt = image_revised_prompt

        print(f"Image remote URL: {self.remote_image_url}")
        print(f"Image revised prompt: {self.revised_prompt}")

    @deal.pre(lambda _: isinstance(_.local_folder, Path))
    @deal.pre(lambda _: len(_.file_prefix) > 0)
    @deal.pre(lambda _: isinstance(_.file_prefix, str))
    @deal.pre(lambda _: _.self.remote_image_url.startswith("http"))
    @deal.pre(lambda _: isinstance(_.self.remote_image_url, str))
    @deal.pre(lambda _: len(_.self.local_image_absolute_path) == 0) # Can't download image if it's already downloaded
    @deal.ensure(lambda _: _.self.local_image_absolute_path.exists())
    def download_image_sync(self, local_folder: Path, file_prefix: str):
        """
        Downloads an image synchronously from a remote URL and saves it locally.

        Args:
            local_folder (Path): The local folder where the image will be saved.
            file_prefix (str): The prefix to be used for the saved image file.
        """
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


def generate_image_sync(
    i_openai_client, i_prompt: str, i_folder_path: Path, i_file_prefix: str
) -> ImageData:
    image_data = ImageData(i_prompt)
    image_data.generate_image_sync(i_openai_client)
    image_data.download_image_sync(i_folder_path, i_file_prefix)
    return image_data


def spin_styles_sync(i_prompt, i_folder_path: Path):
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
        "Art Deco",
        "Art Nouveau",
        "Bauhaus",
        "Bokeh Art",
        "Brutalism in design",
        "Byzantine Art",
        "Cartoon",
        "Celtic Art",
        "Charcoal",
        "Chinese Brush Painting",
        "Chiptune Visuals",
        "Concept Art",
        "Constructivism",
        "Cyber Folk",
        "Cybernetic Art",
        "Cyberpunk",
        "Dadaism",
        "Data Art",
        "Digital Collage",
        "Digital Cubism",
        "Digital Impressionism",
        "Digital Painting",
        "Double Exposure",
        "Dreamy Fantasy",
        "Dystopian Art",
        "Emoji",
        "Etching",
        "Expressionism",
        "Fauvism",
        "Flat Design",
        "Fractal Art",
        "Futurism",
        "Glitch Art",
        "Gothic Art",
        "Gouache",
        "Greco-Roman Art",
        "Impressionism",
        "Ink Wash",
        "Isometric Art",
        "Japanese Ukiyo-e",
        "Kinetic Typography",
        "Lithography",
        "Low Poly",
        "Macabre Art",
        "Magic Realism",
        "Minimalism",
        "Modernism",
        "Monogram",
        "Mosaic",
        "Neon Graffiti",
        "Neon Noir",
        "Origami",
        "Papercut",
        "Parallax Art",
        "Pastel Drawing",
        "Photorealism",
        "Pixel Art",
        "Pointillism",
        "Polyart",
        "Pop Art",
        "Psychedelic Art",
        "Rennaissance/Baroque",
        "Retro Wave",
        "Romanticism",
        "Sci-Fi Fantasy",
        "Scratchboard",
        "Sfomato",
        "Steampunk",
        "Stippling",
        "Surrealism",
        "Symbolism",
        "Trompe-l'eil",
        "Vaporwave",
        "Vector Art",
        "Voxel Art",
        "Watercolor",
        "Woodblock Printing",
        "Zen Doodle",
    ]

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
            new_generated_entry = generate_image_sync(
                client, styled_prompt, i_folder_path, file_prefix
            )

            print(f"Image {new_generated_entry.local_image_absolute_path} saved.")

        except Exception as e:
            print(f"Error generating image in style of {style}: {e}")


# spin_styles_sync("Christmas", "/home/nikolai3d/Dropbox/AdobeFirefly/Style Spin/christmas_sd")


ai_client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)

spin_styles_sync(
    "A humorous twist on the 'Woman yelling at a cat' meme: On the left, a long-haired, black-haired dwarf man is yelling and pointing finger, his expression showing frustration. On the right, instead of a cat, there's a small, dark-red dragon sitting at a dinner table, looking indifferent and slightly confused. Both characters are cartoonishly depicted.",
    Path("./meme_sd"),
)

# test_image_list = [test_image]

# html_table = generate_html_table(test_image_list)

# save_html_to_file(html_table, "./test_images/test.html")
