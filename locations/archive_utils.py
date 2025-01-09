from io import BytesIO
from zipfile import ZipFile

def unzip_file_from_archive(compressed_data: bytes, file_path: str, password: str | None = None) -> bytes:
    """
    Extract and return a specified file from a ZIP archive.
    :param compressed_data: source archive as a bytes array
    :param file_path: path and name of the file within the archive to extract
    :param password: optional password required to extract from the archive
    :return: extracted file as a bytes array
    """
    with ZipFile(BytesIO(compressed_data)) as archive:
        with archive.open(file_path, mode="r", pwd=password) as file:
            return file.read()
