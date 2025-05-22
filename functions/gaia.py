import os
import requests
from datasets import load_dataset
from pathlib import Path
import logging

# Configure logging
# logging.basicConfig(level=logging.DEBUG)

def get_gaia_attachment(attachment_id):
    """
    Download and process an attachment from the GAIA benchmark dataset.

    Args:
        attachment_id (str): The attachment ID/hash (e.g., '7bd855d8-463d-4ed5-93ca-5fe35145f733')

    Returns:
        str: Content or information about the attachment
    """
    logging.info(f"Fetching GAIA attachment with ID: {attachment_id}")

    try:
        # Create a directory to store attachments if it doesn't exist
        attachment_dir = Path("gaia_attachments")
        attachment_dir.mkdir(exist_ok=True)

        # Check if we've already downloaded this attachment
        attachment_path = attachment_dir / f"{attachment_id}"
        if attachment_path.exists():
            logging.info(f"Using cached attachment: {attachment_id}")
            with open(attachment_path, "r", encoding="utf-8") as f:
                content = f.read()
            return f"Attachment content (cached):\n{content[:1000]}..." if len(content) > 1000 else content

        # If not cached, download from Hugging Face
        logging.info("Downloading attachment from Hugging Face...")

        # First try direct file download if it looks like a file ID
        if attachment_id.endswith(('.xlsx', '.csv', '.json', '.txt', '.pdf')) or '-' in attachment_id:
            # Try both validation and test directories
            for split in ['validation', 'test']:
                file_url = f"https://huggingface.co/datasets/gaia-benchmark/GAIA/resolve/main/2023/{split}/{attachment_id}"
                if not attachment_id.endswith(('.xlsx', '.csv', '.json', '.txt', '.pdf')):
                    # Try with common extensions if no extension in ID
                    for ext in ['.xlsx', '.csv', '.json', '.txt', '.pdf']:
                        ext_url = f"{file_url}{ext}"
                        logging.info(f"Trying direct file download from: {ext_url}")
                        try:
                            hf_token = os.getenv("HF_TOKEN")
                            headers = {"Authorization": f"Bearer {hf_token}"} if hf_token else {}
                            response = requests.get(ext_url, headers=headers)
                            if response.status_code == 200:
                                # For binary files like Excel
                                with open(attachment_path, "wb") as f:
                                    f.write(response.content)
                                return f"Successfully downloaded file {attachment_id}{ext} from {split} directory. File saved to {attachment_path}"
                        except Exception as e:
                            logging.warning(f"Failed to download with extension {ext}: {str(e)}")
                else:
                    # If ID already has extension
                    logging.info(f"Trying direct file download from: {file_url}")
                    try:
                        hf_token = os.getenv("HF_TOKEN")
                        headers = {"Authorization": f"Bearer {hf_token}"} if hf_token else {}
                        response = requests.get(file_url, headers=headers)
                        if response.status_code == 200:
                            # For binary files like Excel
                            with open(attachment_path, "wb") as f:
                                f.write(response.content)
                            return f"Successfully downloaded file {attachment_id} from {split} directory. File saved to {attachment_path}"
                    except Exception as e:
                        logging.warning(f"Failed to download from {split}: {str(e)}")

        # If direct file download fails, try loading the dataset
        logging.info("Trying to load dataset with specific configuration...")
        dataset = load_dataset(
            "gaia-benchmark/GAIA",
            "2023_all",
            data_dir="2023",
            split="validation",
            trust_remote_code=True,
            streaming=True
        )

        # Debugging: Print the type and keys of the dataset
        logging.debug(f"Dataset type: {type(dataset)}")
        if isinstance(dataset, dict):
            logging.debug(f"Dataset keys: {list(dataset.keys())}")

        # Get the first split from the dataset (likely 'test' or 'validation')
        if "test" in dataset:
            dataset_iter = dataset["test"]
            logging.info("Using 'test' split")
        elif "validation" in dataset:
            dataset_iter = dataset["validation"]
            logging.info("Using 'validation' split")
        else:
            dataset_iter = next(iter(dataset.values()))
            logging.info(f"Using first available split: {next(iter(dataset.keys()))}")

        # Search for the attachment in the dataset
        attachment_info = None
        for i, example in enumerate(dataset_iter):
            if i > 1000:  # Limit search to avoid processing the entire dataset
                break

            # Check if this example contains our attachment ID
            if "task_id" in example and example["task_id"] == attachment_id:
                logging.info(f"Found task with matching ID: {attachment_id}")
                return f"Found task with ID {attachment_id}: {example}"

            # Check attachments if present
            if "attachments" in example and example["attachments"]:
                for attachment in example["attachments"]:
                    if attachment["id"] == attachment_id:
                        attachment_info = attachment
                        break

            if attachment_info:
                break

        if attachment_info:
            logging.info(f"Found attachment metadata: {attachment_info}")

            # Try to get the attachment content using the metadata
            if "url" in attachment_info:
                attachment_url = attachment_info["url"]
            else:
                attachment_url = f"https://huggingface.co/datasets/gaia-benchmark/GAIA/resolve/main/attachments/{attachment_id}{ext}"

            # Download the attachment
            hf_token = os.getenv("HF_TOKEN")
            headers = {"Authorization": f"Bearer {hf_token}"} if hf_token else {}
            response = requests.get(attachment_url, headers=headers)

            if response.status_code == 200:
                content = response.text

                # Save to cache
                with open(attachment_path, "w", encoding="utf-8") as f:
                    f.write(content)

                return f"Attachment content:\n{content[:1000]}..." if len(content) > 1000 else content
            else:
                return f"Failed to download attachment. Status code: {response.status_code}"
        else:
            # Try alternative dataset configuration
            logging.info("Trying alternative dataset configuration...")
            try:
                alt_dataset = load_dataset(
                    "gaia-benchmark/GAIA",
                    trust_remote_code=True,
                    streaming=False  # Try non-streaming mode
                )

                logging.debug(f"Alternative dataset type: {type(alt_dataset)}")
                if isinstance(alt_dataset, dict):
                    logging.debug(f"Alternative dataset keys: {list(alt_dataset.keys())}")

                # Check if attachments are directly accessible
                if "attachments" in alt_dataset:
                    if attachment_id in alt_dataset["attachments"]:
                        content = alt_dataset["attachments"][attachment_id]

                        # Save to cache
                        with open(attachment_path, "w", encoding="utf-8") as f:
                            f.write(content)

                        return f"Attachment content (from attachments dataset):\n{content[:1000]}..." if len(content) > 1000 else content

            except Exception as alt_error:
                logging.error(f"Error with alternative dataset: {str(alt_error)}")

            return f"Attachment with ID {attachment_id} not found in the dataset metadata. Try setting the HF_TOKEN environment variable with a valid Hugging Face token."

    except Exception as e:
        import traceback
        logging.error(f"Error processing GAIA attachment: {str(e)}")
        logging.error(traceback.format_exc())
        return f"Error processing attachment {attachment_id}: {str(e)}"
