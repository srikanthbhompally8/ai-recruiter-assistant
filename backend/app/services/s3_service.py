"""AWS S3 Document Storage Service"""
import boto3
import logging
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)


class S3Service:
    """Service for S3 file operations"""

    def __init__(self):
        self.s3_client = boto3.client(
            "s3",
            region_name=settings.AWS_S3_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
        self.bucket = settings.AWS_S3_BUCKET

    def upload_file(
        self,
        file_key: str,
        file_content: bytes,
        content_type: str = "application/octet-stream",
        metadata: Optional[dict] = None,
    ) -> str:
        """
        Upload file to S3

        Args:
            file_key: S3 object key/path
            file_content: File content (bytes)
            content_type: MIME type
            metadata: Additional metadata

        Returns:
            S3 URL of uploaded file
        """
        try:
            extra_args = {
                "ContentType": content_type,
            }

            if metadata:
                extra_args["Metadata"] = metadata

            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=file_key,
                Body=file_content,
                **extra_args,
            )

            url = f"s3://{self.bucket}/{file_key}"
            logger.info(f"File uploaded to S3: {url}")
            return url

        except Exception as e:
            logger.error(f"S3 upload error: {e}")
            raise

    def download_file(self, file_key: str) -> bytes:
        """
        Download file from S3

        Args:
            file_key: S3 object key/path

        Returns:
            File content (bytes)
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket,
                Key=file_key,
            )
            content = response["Body"].read()
            logger.info(f"File downloaded from S3: {file_key}")
            return content

        except Exception as e:
            logger.error(f"S3 download error: {e}")
            raise

    def delete_file(self, file_key: str) -> bool:
        """
        Delete file from S3

        Args:
            file_key: S3 object key/path

        Returns:
            True if successful
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket,
                Key=file_key,
            )
            logger.info(f"File deleted from S3: {file_key}")
            return True

        except Exception as e:
            logger.error(f"S3 delete error: {e}")
            raise

    def generate_signed_url(
        self,
        file_key: str,
        expiration: int = 3600,
    ) -> str:
        """
        Generate signed URL for secure file access

        Args:
            file_key: S3 object key/path
            expiration: URL expiration time in seconds (default 1 hour)

        Returns:
            Signed URL string
        """
        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": file_key},
                ExpiresIn=expiration,
            )
            logger.info(f"Signed URL generated for: {file_key}")
            return url

        except Exception as e:
            logger.error(f"Error generating signed URL: {e}")
            raise

    def file_exists(self, file_key: str) -> bool:
        """
        Check if file exists in S3

        Args:
            file_key: S3 object key/path

        Returns:
            True if file exists
        """
        try:
            self.s3_client.head_object(
                Bucket=self.bucket,
                Key=file_key,
            )
            return True
        except self.s3_client.exceptions.NoSuchKey:
            return False
        except Exception as e:
            logger.error(f"Error checking file existence: {e}")
            raise


# Create singleton instance
s3_service = S3Service()
