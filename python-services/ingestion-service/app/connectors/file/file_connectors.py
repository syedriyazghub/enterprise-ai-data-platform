"""File-based connectors: CSV, Excel, JSON, XML, Parquet, Avro, ORC."""
import io
import json
import xml.etree.ElementTree as ET
from typing import AsyncIterator
import aiofiles
import pandas as pd

from app.connectors.base import BaseConnector, ConnectorConfig, IngestedRecord
from app.core.logging import get_logger

logger = get_logger(__name__)


class CSVConnector(BaseConnector):
    """Ingests data from CSV files."""

    async def connect(self) -> None:
        self._file_path = self.config.connection_params["file_path"]

    async def disconnect(self) -> None:
        pass

    async def test_connection(self) -> bool:
        import os
        return os.path.exists(self._file_path)

    async def fetch(self) -> AsyncIterator[IngestedRecord]:
        options = self.config.options
        chunk_size = options.get("chunk_size", 1000)
        encoding = options.get("encoding", "utf-8")
        delimiter = options.get("delimiter", ",")

        async with aiofiles.open(self._file_path, mode="r", encoding=encoding) as f:
            content = await f.read()

        df_iter = pd.read_csv(
            io.StringIO(content),
            chunksize=chunk_size,
            sep=delimiter,
            dtype=str,
        )
        for chunk in df_iter:
            chunk = chunk.where(pd.notna(chunk), None)
            for _, row in chunk.iterrows():
                yield IngestedRecord(
                    data=row.to_dict(),
                    source_metadata={"source_type": "csv", "file": self._file_path},
                )


class ExcelConnector(BaseConnector):
    """Ingests data from Excel files (.xlsx, .xls)."""

    async def connect(self) -> None:
        self._file_path = self.config.connection_params["file_path"]
        self._sheet_name = self.config.connection_params.get("sheet_name", 0)

    async def disconnect(self) -> None:
        pass

    async def test_connection(self) -> bool:
        import os
        return os.path.exists(self._file_path)

    async def fetch(self) -> AsyncIterator[IngestedRecord]:
        df = pd.read_excel(self._file_path, sheet_name=self._sheet_name, dtype=str)
        df = df.where(pd.notna(df), None)
        for _, row in df.iterrows():
            yield IngestedRecord(
                data=row.to_dict(),
                source_metadata={"source_type": "excel", "file": self._file_path, "sheet": self._sheet_name},
            )


class JSONConnector(BaseConnector):
    """Ingests data from JSON files."""

    async def connect(self) -> None:
        self._file_path = self.config.connection_params["file_path"]

    async def disconnect(self) -> None:
        pass

    async def test_connection(self) -> bool:
        import os
        return os.path.exists(self._file_path)

    async def fetch(self) -> AsyncIterator[IngestedRecord]:
        async with aiofiles.open(self._file_path, mode="r") as f:
            content = await f.read()

        data = json.loads(content)
        records = data if isinstance(data, list) else [data]

        for record in records:
            yield IngestedRecord(
                data=record if isinstance(record, dict) else {"value": record},
                source_metadata={"source_type": "json", "file": self._file_path},
            )


class XMLConnector(BaseConnector):
    """Ingests data from XML files."""

    async def connect(self) -> None:
        self._file_path = self.config.connection_params["file_path"]
        self._record_tag = self.config.connection_params.get("record_tag", "record")

    async def disconnect(self) -> None:
        pass

    async def test_connection(self) -> bool:
        import os
        return os.path.exists(self._file_path)

    async def fetch(self) -> AsyncIterator[IngestedRecord]:
        tree = ET.parse(self._file_path)
        root = tree.getroot()

        for element in root.iter(self._record_tag):
            record = {child.tag: child.text for child in element}
            record.update(element.attrib)
            yield IngestedRecord(
                data=record,
                source_metadata={"source_type": "xml", "file": self._file_path},
            )


class ParquetConnector(BaseConnector):
    """Ingests data from Parquet files."""

    async def connect(self) -> None:
        self._file_path = self.config.connection_params["file_path"]

    async def disconnect(self) -> None:
        pass

    async def test_connection(self) -> bool:
        import os
        return os.path.exists(self._file_path)

    async def fetch(self) -> AsyncIterator[IngestedRecord]:
        df = pd.read_parquet(self._file_path)
        df = df.where(pd.notna(df), None)
        for _, row in df.iterrows():
            yield IngestedRecord(
                data=row.to_dict(),
                source_metadata={"source_type": "parquet", "file": self._file_path},
            )
