import boto3
from typing import Optional
from app.config import settings

class StorageService:
    def __init__(self):
        # Initialize boto3 client for S3-compatible API (Supabase Storage)
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.SUPABASE_STORAGE_URL,
            aws_access_key_id=settings.SUPABASE_STORAGE_KEY,
            aws_secret_access_key=settings.SUPABASE_STORAGE_SECRET,
            region_name="auto" # Default for Supabase Storage/R2
        )
        self.bucket = settings.SUPABASE_STORAGE_BUCKET

    def upload(self, file_obj, object_name: str, content_type: str = "application/pdf") -> str:
        """
        Upload a file to the configured object storage bucket.
        Returns the object key.
        """
        self.client.upload_fileobj(
            file_obj,
            self.bucket,
            object_name,
            ExtraArgs={"ContentType": content_type}
        )
        return object_name

    def get_url(self, object_name: str, expires_in: int = 3600) -> str:
        """
        Generate a presigned URL for downloading/viewing an object.
        """
        url = self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": object_name},
            ExpiresIn=expires_in
        )
        return url

    def delete(self, object_name: str) -> bool:
        """
        Delete an object from the bucket.
        """
        try:
            self.client.delete_object(Bucket=self.bucket, Key=object_name)
            return True
        except Exception:
            return False

# Global instance
storage_service = StorageService()
