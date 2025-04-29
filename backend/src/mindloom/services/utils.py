import re
import os
import logging
from typing import List, Optional, Dict, Any

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from langchain_core.documents import Document
from langchain_community.document_loaders import (
    TextLoader,
    PyPDFLoader,
    UnstructuredWordDocumentLoader,
    UnstructuredPowerPointLoader,
    UnstructuredCSVLoader,
)

from mindloom.core.config import settings

logger = logging.getLogger(__name__)

# Helper function to convert CamelCase to snake_case
def camel_to_snake(name):
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()

# --- Helper Function for S3 Client ---

def get_s3_client(storage_config: Optional[Dict[str, Any]] = None):
    """Creates and returns an S3 client configured for a compatible endpoint."""
    try:
        # Prefer bucket-specific config if provided
        if storage_config and storage_config.get('endpoint_url'):
            logger.debug("Using bucket-specific S3 configuration.")
            return boto3.client(
                's3',
                endpoint_url=storage_config.get('endpoint_url'),
                aws_access_key_id=storage_config.get('aws_access_key_id'),
                aws_secret_access_key=storage_config.get('aws_secret_access_key'),
                region_name=storage_config.get('region_name') # Optional
            )
        # Fallback to global settings if bucket config incomplete or absent
        elif settings.S3_ENDPOINT_URL:
            logger.debug("Using global S3 configuration from settings.")
            return boto3.client(
                's3',
                endpoint_url=settings.S3_ENDPOINT_URL,
                aws_access_key_id=settings.S3_ACCESS_KEY_ID,
                aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
                region_name=settings.S3_REGION_NAME # Optional
            )
        else:
            logger.error("No S3 endpoint configuration found in bucket config or global settings.")
            return None
    except NoCredentialsError:
        logger.error("AWS credentials not found. S3 client cannot be created.")
        return None
    except Exception as e:
        logger.error(f"Failed to create S3 client: {e}", exc_info=True)
        return None

# --- Helper Function for Document Loading ---

def load_document_from_file(file_path: str, original_filename: Optional[str], metadata_base: Optional[Dict] = None) -> List[Document]:
    """Loads documents from a local file path using appropriate Langchain loader."""
    if not original_filename:
        original_filename = os.path.basename(file_path)
    _, ext = os.path.splitext(original_filename)
    ext = ext.lower()
    loader = None
    documents = []
    base_metadata = metadata_base or {}

    try:
        if ext == '.pdf':
            loader = PyPDFLoader(file_path)
        elif ext == '.docx':
             loader = UnstructuredWordDocumentLoader(file_path)
        elif ext == '.pptx':
             loader = UnstructuredPowerPointLoader(file_path)
        elif ext == '.csv':
             loader = UnstructuredCSVLoader(file_path, mode="elements") # Or mode="single"
        elif ext in ['.txt', '.md', '.py', '.json', '.yaml', '.html', '.xml', '.js', '.ts']:
            try:
                 loader = TextLoader(file_path, encoding='utf-8')
            except Exception as text_load_error:
                 logger.warning(f"UTF-8 loading failed for {original_filename}, trying fallback encoding: {text_load_error}")
                 # Add fallback encodings if needed, e.g., 'latin-1'
                 try:
                     loader = TextLoader(file_path, encoding='latin-1')
                 except Exception as fallback_load_error:
                     logger.error(f"Fallback encoding failed for {original_filename}: {fallback_load_error}", exc_info=True)
                     return [] # Failed to load
        else:
            logger.warning(f"No specific Langchain loader for extension '{ext}' in file '{original_filename}'. Skipping.")
            return [] # Skip unsupported types

        if loader:
            logger.debug(f"Loading document: {original_filename} using {type(loader).__name__}")
            loaded_docs = loader.load() # Load documents
            # Merge base metadata with any metadata from the loader
            for doc in loaded_docs:
                doc.metadata = {**base_metadata, **doc.metadata}
            documents.extend(loaded_docs)
            logger.debug(f"Successfully loaded {len(documents)} document sections from {original_filename}.")

    except FileNotFoundError:
        logger.error(f"File not found during loading: {file_path}")
    except Exception as e:
        logger.error(f"Error loading document {original_filename} from {file_path}: {e}", exc_info=True)

    return documents
