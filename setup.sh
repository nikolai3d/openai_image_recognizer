ENV_PREFIX=".openai-venv/"
ENV_YAML="openai_environment.yaml"

# Check if the environment directory exists
if [ -d "$ENV_PREFIX" ]; then
    # Environment exists, so update it
    conda env update --file $ENV_YAML --prefix $ENV_PREFIX
else
    # Environment doesn't exist, so create it
    conda env create -f $ENV_YAML --prefix $ENV_PREFIX
fi
