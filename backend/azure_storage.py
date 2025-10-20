"""
Azure Storage integration for S1000D QA application
Handles Azure Blob Storage and Azure Key Vault operations
"""
import os
from typing import Optional, Dict, Any
import io

try:
    from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
    from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
    from azure.keyvault.secrets import SecretClient
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False
    print("Azure SDK not available. Install with: pip install azure-storage-blob azure-keyvault-secrets azure-identity")

from config import AzureConfig


class AzureBlobStorage:
    """Azure Blob Storage client for PDF and index storage"""
    
    def __init__(self, connection_string: str = None, container_name: str = None):
        """
        Initialize Azure Blob Storage client
        
        Args:
            connection_string: Azure Storage connection string
            container_name: Blob container name
        """
        if not AZURE_AVAILABLE:
            raise ImportError("Azure SDK is not installed")
        
        self.connection_string = connection_string or AzureConfig.AZURE_STORAGE_CONNECTION_STRING
        self.container_name = container_name or AzureConfig.AZURE_BLOB_CONTAINER
        
        if not self.connection_string:
            raise ValueError("Azure Storage connection string not provided")
        
        # Initialize blob service client
        self.blob_service_client = BlobServiceClient.from_connection_string(
            self.connection_string
        )
        
        # Get or create container
        self.container_client = self._get_or_create_container()
    
    def _get_or_create_container(self) -> ContainerClient:
        """Get or create blob container"""
        try:
            container_client = self.blob_service_client.get_container_client(
                self.container_name
            )
            
            # Check if container exists
            if not container_client.exists():
                print(f"Creating container: {self.container_name}")
                container_client.create_container()
            
            return container_client
        
        except Exception as e:
            print(f"Error getting/creating container: {str(e)}")
            raise
    
    def upload_file(self, local_path: str, blob_name: str, overwrite: bool = False) -> str:
        """
        Upload file to Azure Blob Storage
        
        Args:
            local_path: Local file path
            blob_name: Name for blob in storage
            overwrite: Overwrite if exists
            
        Returns:
            Blob URL
        """
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            
            with open(local_path, "rb") as data:
                blob_client.upload_blob(data, overwrite=overwrite)
            
            print(f"Uploaded {local_path} to {blob_name}")
            return blob_client.url
        
        except Exception as e:
            print(f"Error uploading file: {str(e)}")
            raise
    
    def download_file(self, blob_name: str, local_path: str) -> str:
        """
        Download file from Azure Blob Storage
        
        Args:
            blob_name: Blob name in storage
            local_path: Local path to save file
            
        Returns:
            Local file path
        """
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            with open(local_path, "wb") as file:
                download_stream = blob_client.download_blob()
                file.write(download_stream.readall())
            
            print(f"Downloaded {blob_name} to {local_path}")
            return local_path
        
        except Exception as e:
            print(f"Error downloading file: {str(e)}")
            raise
    
    def download_to_stream(self, blob_name: str) -> bytes:
        """
        Download blob to memory stream
        
        Args:
            blob_name: Blob name in storage
            
        Returns:
            File content as bytes
        """
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            download_stream = blob_client.download_blob()
            return download_stream.readall()
        
        except Exception as e:
            print(f"Error downloading to stream: {str(e)}")
            raise
    
    def list_blobs(self, prefix: str = None) -> list:
        """
        List blobs in container
        
        Args:
            prefix: Filter by prefix
            
        Returns:
            List of blob names
        """
        try:
            blob_list = self.container_client.list_blobs(name_starts_with=prefix)
            return [blob.name for blob in blob_list]
        
        except Exception as e:
            print(f"Error listing blobs: {str(e)}")
            return []
    
    def delete_blob(self, blob_name: str):
        """
        Delete blob from storage
        
        Args:
            blob_name: Blob name to delete
        """
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            blob_client.delete_blob()
            print(f"Deleted blob: {blob_name}")
        
        except Exception as e:
            print(f"Error deleting blob: {str(e)}")
            raise
    
    def blob_exists(self, blob_name: str) -> bool:
        """
        Check if blob exists
        
        Args:
            blob_name: Blob name to check
            
        Returns:
            True if blob exists
        """
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            return blob_client.exists()
        
        except Exception as e:
            print(f"Error checking blob existence: {str(e)}")
            return False
    
    def get_blob_metadata(self, blob_name: str) -> Dict[str, Any]:
        """
        Get blob metadata
        
        Args:
            blob_name: Blob name
            
        Returns:
            Blob metadata dictionary
        """
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            properties = blob_client.get_blob_properties()
            
            return {
                "name": blob_name,
                "size": properties.size,
                "content_type": properties.content_settings.content_type,
                "last_modified": properties.last_modified,
                "metadata": properties.metadata
            }
        
        except Exception as e:
            print(f"Error getting blob metadata: {str(e)}")
            return {}


class AzureKeyVault:
    """Azure Key Vault client for secrets management"""
    
    def __init__(self, vault_url: str = None):
        """
        Initialize Azure Key Vault client
        
        Args:
            vault_url: Azure Key Vault URL
        """
        if not AZURE_AVAILABLE:
            raise ImportError("Azure SDK is not installed")
        
        self.vault_url = vault_url or AzureConfig.AZURE_KEYVAULT_URL
        
        if not self.vault_url:
            raise ValueError("Azure Key Vault URL not provided")
        
        # Use DefaultAzureCredential for authentication
        credential = DefaultAzureCredential()
        self.secret_client = SecretClient(vault_url=self.vault_url, credential=credential)
    
    def get_secret(self, secret_name: str) -> Optional[str]:
        """
        Get secret from Key Vault
        
        Args:
            secret_name: Name of secret
            
        Returns:
            Secret value or None
        """
        try:
            secret = self.secret_client.get_secret(secret_name)
            return secret.value
        
        except Exception as e:
            print(f"Error getting secret {secret_name}: {str(e)}")
            return None
    
    def set_secret(self, secret_name: str, secret_value: str):
        """
        Set secret in Key Vault
        
        Args:
            secret_name: Name of secret
            secret_value: Secret value
        """
        try:
            self.secret_client.set_secret(secret_name, secret_value)
            print(f"Set secret: {secret_name}")
        
        except Exception as e:
            print(f"Error setting secret {secret_name}: {str(e)}")
            raise
    
    def delete_secret(self, secret_name: str):
        """
        Delete secret from Key Vault
        
        Args:
            secret_name: Name of secret to delete
        """
        try:
            self.secret_client.begin_delete_secret(secret_name)
            print(f"Deleted secret: {secret_name}")
        
        except Exception as e:
            print(f"Error deleting secret {secret_name}: {str(e)}")
            raise
    
    def list_secrets(self) -> list:
        """
        List all secrets in Key Vault
        
        Returns:
            List of secret names
        """
        try:
            secrets = self.secret_client.list_properties_of_secrets()
            return [secret.name for secret in secrets]
        
        except Exception as e:
            print(f"Error listing secrets: {str(e)}")
            return []


def setup_azure_storage_for_pdf(pdf_blob_name: str = "S1000D_Issue_6.PDF") -> Optional[str]:
    """
    Setup function to download PDF from Azure Blob Storage
    
    Args:
        pdf_blob_name: Name of PDF blob in storage
        
    Returns:
        Local path to downloaded PDF or None
    """
    if not AZURE_AVAILABLE:
        print("Azure SDK not available")
        return None
    
    if not AzureConfig.is_azure():
        print("Not running in Azure environment")
        return None
    
    try:
        storage = AzureBlobStorage()
        
        # Check if PDF exists in blob storage
        if not storage.blob_exists(pdf_blob_name):
            print(f"PDF not found in blob storage: {pdf_blob_name}")
            return None
        
        # Download to local path
        local_path = os.path.join("/app/data", pdf_blob_name)
        storage.download_file(pdf_blob_name, local_path)
        
        return local_path
    
    except Exception as e:
        print(f"Error setting up Azure storage for PDF: {str(e)}")
        return None


# Test functions
if __name__ == "__main__":
    print("Testing Azure Storage Integration...")
    
    # Check if Azure is available
    if not AZURE_AVAILABLE:
        print("Azure SDK not installed. Skipping tests.")
        exit(0)
    
    # Check if running in Azure environment
    if not AzureConfig.is_azure():
        print("Not running in Azure environment. Skipping tests.")
        exit(0)
    
    print(f"Azure Config valid: {AzureConfig.validate_azure_config()}")


