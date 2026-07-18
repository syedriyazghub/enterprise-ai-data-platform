"""Cloud storage connectors: AWS S3, Azure Blob, GCP Storage."""
from typing import AsyncIterator
import io
import structlog

from app.connectors.base import BaseConnector, ConnectorConfig, IngestedRecord

logger = structlog.get_logger()


class S3Connector(BaseConnector):
    """Ingests files from AWS S3."""

    async def connect(self) -> None:
        import boto3
        params = self.config.connection_params
        self._s3 = boto3.client(
            "s3",
            aws_access_key_id=params.get("access_key_id"),
            aws_secret_access_key=params.get("secret_access_key"),
            region_name=params.get("region", "us-east-1"),
        )
        self._bucket = params["bucket"]
        self._prefix = params.get("prefix", "")

    async def disconnect(self) -> None:
        pass

    async def test_connection(self) -> bool:
        try:
            self._s3.head_bucket(Bucket=self._bucket)
            return True
        except Exception:
            return False

    async def fetch(self) -> AsyncIterator[IngestedRecord]:
        import pandas as pd

        paginator = self._s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self._bucket, Prefix=self._prefix):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                response = self._s3.get_object(Bucket=self._bucket, Key=key)
                content = response["Body"].read()

                if key.endswith(".csv"):
                    df = pd.read_csv(io.BytesIO(content), dtype=str)
                    df = df.where(pd.notna(df), None)
                    for _, row in df.iterrows():
                        yield IngestedRecord(
                            data=row.to_dict(),
                            source_metadata={"source_type": "aws_s3", "bucket": self._bucket, "key": key},
                            raw_content=content,
                        )
                elif key.endswith(".json"):
                    import json
                    data = json.loads(content)
                    records = data if isinstance(data, list) else [data]
                    for record in records:
                        yield IngestedRecord(
                            data=record,
                            source_metadata={"source_type": "aws_s3", "bucket": self._bucket, "key": key},
                        )


class AzureBlobConnector(BaseConnector):
    """Ingests files from Azure Blob Storage."""

    async def connect(self) -> None:
        from azure.storage.blob import BlobServiceClient
        params = self.config.connection_params
        self._service = BlobServiceClient.from_connection_string(
            params["connection_string"]
        )
        self._container = params["container"]

    async def disconnect(self) -> None:
        pass

    async def test_connection(self) -> bool:
        try:
            container_client = self._service.get_container_client(self._container)
            container_client.get_container_properties()
            return True
        except Exception:
            return False

    async def fetch(self) -> AsyncIterator[IngestedRecord]:
        import pandas as pd
        container_client = self._service.get_container_client(self._container)

        for blob in container_client.list_blobs():
            blob_client = container_client.get_blob_client(blob.name)
            content = blob_client.download_blob().readall()

            if blob.name.endswith(".csv"):
                df = pd.read_csv(io.BytesIO(content), dtype=str)
                df = df.where(pd.notna(df), None)
                for _, row in df.iterrows():
                    yield IngestedRecord(
                        data=row.to_dict(),
                        source_metadata={"source_type": "azure_blob", "container": self._container, "blob": blob.name},
                    )
