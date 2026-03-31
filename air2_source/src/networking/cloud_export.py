"""
Cloud Data Export for AirOne Professional v4.0
Integrated AWS S3 and Azure Blob Storage capability using standard SDKs.
"""
import os
import json
import logging
import threading
import queue
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class CloudDataExporter:
    def __init__(self, provider: str = "AWS", bucket_name: str = "airone-telemetry"):
        self.logger = logging.getLogger(f"{__name__}.CloudDataExporter")
        self.provider = provider.upper()
        self.bucket_name = bucket_name
        self.client = None
        self.upload_queue = queue.Queue()
        self.worker_thread = None
        self.is_connected = False
        
        self.logger.info(f"Initializing {self.provider} Cloud Export to '{self.bucket_name}'...")
        self._initialize_client()

    def _initialize_client(self):
        """Attempts to initialize the real cloud provider SDK client."""
        try:
            if self.provider == "AWS":
                import boto3
                from botocore.config import Config
                # Using a 2-second timeout for rapid failover if no credentials
                config = Config(connect_timeout=2, retries={'max_attempts': 1})
                self.client = boto3.client('s3', config=config)
                self.logger.info("Boto3 (AWS) Client Initialized.")
            elif self.provider == "AZURE":
                from azure.storage.blob import BlobServiceClient
                self.client = BlobServiceClient.from_connection_string(os.getenv('AZURE_STORAGE_CONNECTION_STRING'))
                self.logger.info("Azure Blob Storage Client Initialized.")
            
            # Start background uploader
            self.worker_thread = threading.Thread(target=self._upload_worker, daemon=True)
            self.worker_thread.start()
            self.is_connected = True
        except ImportError:
            self.logger.warning(f"Cloud SDK for {self.provider} not found. Using fallback log storage.")
            self.is_connected = False
        except Exception as e:
            self.logger.error(f"Cloud Connection Failed: {e}")
            self.is_connected = False

    def upload_telemetry(self, data: List[Dict[str, Any]], mission_id: str = "default_mission"):
        """Enqueues telemetry for asynchronous upload."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"telemetry/{mission_id}/batch_{timestamp}.json"
        
        payload = {
            "key": filename,
            "body": json.dumps(data, indent=2, default=str),
            "mission_id": mission_id
        }
        self.upload_queue.put(payload)
        self.logger.debug(f"Telemetry batch enqueued for upload: {filename}")

    def _upload_worker(self):
        """Background worker that pulls from queue and performs real uploads."""
        while True:
            item = self.upload_queue.get()
            if item is None: break
            
            try:
                if self.provider == "AWS" and self.client:
                    self.client.put_object(
                        Bucket=self.bucket_name,
                        Key=item['key'],
                        Body=item['body'],
                        ContentType='application/json'
                    )
                    self.logger.info(f"Successfully uploaded to S3: {item['key']}")
                elif self.provider == "AZURE" and self.client:
                    blob_client = self.client.get_blob_client(container=self.bucket_name, blob=item['key'])
                    blob_client.upload_blob(item['body'], overwrite=True)
                    self.logger.info(f"Successfully uploaded to Azure Blob: {item['key']}")
            except Exception as e:
                self.logger.error(f"Upload task failed for {item['key']}: {e}")
                # Save locally on failure
                self._save_local_fallback(item['key'], item['body'])
            
            self.upload_queue.task_done()

    def _save_local_fallback(self, key: str, body: str):
        path = os.path.join("logs", "cloud_fallback", key.replace("/", "_"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            f.write(body)
        self.logger.info(f"Fallback: Telemetry saved to {path}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    exporter = CloudDataExporter()
    exporter.upload_telemetry([{"alt": 100}], mission_id="hil_test")
