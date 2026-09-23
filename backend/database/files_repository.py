from bson import ObjectId
from gridfs import AsyncGridFSBucket, NoFile
from pymongo.asynchronous.database import AsyncDatabase

FILES_BUCKET_NAME = "files"


class FilesRepository:
    """Stores the raw uploaded bytes in GridFS."""

    def __init__(self, database: AsyncDatabase) -> None:
        self._bucket = AsyncGridFSBucket(database, bucket_name=FILES_BUCKET_NAME)

    async def upload(self, filename: str, content: bytes, mime_type: str) -> str:
        file_id = await self._bucket.upload_from_stream(filename, content, metadata={"contentType": mime_type})
        return str(file_id)

    async def download(self, file_id: str) -> bytes | None:
        try:
            stream = await self._bucket.open_download_stream(ObjectId(file_id))
        except NoFile:
            return None
        return await stream.read()

    async def delete(self, file_id: str) -> None:
        try:
            await self._bucket.delete(ObjectId(file_id))
        except NoFile:
            # Already gone; deleting the asset must still succeed.
            return
