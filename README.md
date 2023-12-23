# Simple OpenAI API Example

Describes an image, then plays back the audio synthesis of the description.

## Installation

Create/update conda environment:

```
sh setup.sh
```


## Running

Activate the conda environment:

```
conda activate ./.openai-venv/
```

Run the script:

```
python describe.py
```

You need to have an OpenAI key in your environment variables. You can get one from [here](https://platform.openai.com/api-keys by creating a new OpenAI app.

Once you have the key, set it in your environment variables:

```
export OPENAI_API_KEY=<your key>
```

If you have a webcam attached, it will open the webcam window and you can capture an image using `C` key. Once you have capture an image, it will be uploaded to OpenAI API and the description will return. Then the audio synthesis will then upload the description text to the OpenAI API and play back the audio synthesis result (an mp3 file).
