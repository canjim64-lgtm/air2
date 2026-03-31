"""Cloud Storage - AWS S3, GCP, Azure"""
import os
from typing import Optional, Dict, List, Any

class CloudStorage:
    PROVIDERS = ['aws', 'gcp', 'azure', 'dropbox']
    def __init__(self, provider: str, creds: Dict[str, str]):
        if provider not in self.PROVIDERS: raise ValueError(f'Bad provider: {provider}')
        self.provider = provider
        self.creds = creds
        self._connected = False
    def connect(self) -> bool:
        if self.provider == 'aws': return self._connect_aws()
        elif self.provider == 'gcp': return self._connect_gcp()
        elif self.provider == 'azure': return self._connect_azure()
        return False
    def _connect_aws(self) -> bool:
        try:
            import boto3
            self.client = boto3.client('s3', aws_access_key_id=self.creds.get('access_key'),
                aws_secret_access_key=self.creds.get('secret_key'),
                region_name=self.creds.get('region', 'us-east-1'))
            self._connected = True; return True
        except: return False
    def _connect_gcp(self) -> bool:
        try:
            from google.cloud import storage
            self.client = storage.Client.from_service_account_json(self.creds.get('credentials_file'))
            self._connected = True; return True
        except: return False
    def _connect_azure(self) -> bool:
        try:
            from azure.storage.blob import BlobServiceClient
            self.client = BlobServiceClient.from_connection_string(self.creds.get('connection_string'))
            self._connected = True; return True
        except: return False
    def upload_file(self, local: str, remote: str) -> bool:
        if not self._connected: return False
        try:
            if self.provider == 'aws':
                self.client.upload_file(local, self.creds.get('bucket'), remote)
            elif self.provider == 'gcp':
                bucket = self.client.bucket(self.creds.get('bucket'))
                bucket.blob(remote).upload_from_filename(local)
            elif self.provider == 'azure':
                c = self.client.get_container_client(self.creds.get('container'))
                with open(local, 'rb') as data: c.upload_blob(remote, data)
            return True
        except Exception as e: print(f'Upload fail: {e}'); return False
    def download_file(self, remote: str, local: str) -> bool:
        if not self._connected: return False
        try:
            if self.provider == 'aws': self.client.download_file(self.creds.get('bucket'), remote, local)
            elif self.provider == 'gcp':
                bucket = self.client.bucket(self.creds.get('bucket'))
                bucket.blob(remote).download_to_filename(local)
            elif self.provider == 'azure':
                c = self.client.get_container_client(self.creds.get('container'))
                with open(local, 'wb') as data: data.write(c.download_blob(remote).readall())
            return True
        except Exception as e: print(f'Download fail: {e}'); return False
    def list_files(self, prefix='') -> List[str]:
        if not self._connected: return []
        try:
            if self.provider == 'aws':
                r = self.client.list_objects_v2(Bucket=self.creds.get('bucket'), Prefix=prefix)
                return [o['Key'] for o in r.get('Contents', [])]
            return []
        except: return []
    def delete_file(self, remote: str) -> bool:
        if not self._connected: return False
        try:
            if self.provider == 'aws': self.client.delete_object(Bucket=self.creds.get('bucket'), Key=remote)
            return True
        except: return False
    def get_url(self, remote: str, expiry=3600) -> Optional[str]:
        if not self._connected: return None
        try:
            if self.provider == 'aws':
                return self.client.generate_presigned_url('get_object',
                    Params={'Bucket': self.creds.get('bucket'), 'Key': remote}, ExpiresIn=expiry)
        except: return None
    def sync_dir(self, local_dir: str, remote_dir: str) -> Dict[str, Any]:
        res = {'uploaded': [], 'failed': []}
        for r, ds, fs in os.walk(local_dir):
            for f in fs:
                lp = os.path.join(r, f); rp = os.path.join(remote_dir, os.path.relpath(lp, local_dir))
                if self.upload_file(lp, rp): res['uploaded'].append(lp)
                else: res['failed'].append(lp)
        return res
