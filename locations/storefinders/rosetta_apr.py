import csv
import re
from base64 import b64decode
from itertools import pairwise
from json import loads
from typing import Iterable, NamedTuple, get_type_hints
from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import Request, Response

from locations.archive_utils import unzip_file_from_archive
from locations.crypto_utils import decrypt_aes256cbc_pkcs7
from locations.items import Feature


class RosettaAPRDataFile(NamedTuple):
    """
    A named tuple for a data file retrieved through the Rosetta APR spider.
    The following attributes exist:
      - `url`: a string containing the relative path/file name which is
        provided in URLs of `{start_urls[0]}/serve.php?file={file_name}`.
        Values of `file_name` can be observed in network requests in a browser
        when layers are enabled and disabled. Alternatively, data files can
        sometimes be hosted on external domains. If `url` is a full URL
        starting with `https://` or `http://`, this full URL is used for
        downloading the data file.
      - `file_type`: a string with the value of `"geojson"` or `"csv"`. Other
        file types may be supported in the future. Data files are normalised
        to a type of `list[dict]`. See also `archive_format` for data files
        that are compressed archives. If the data file is a compressed ZIP
        archive containing a single GeoJSON file, `archive_format="zip"` and
        `file_type="geojson"` both need to be specified.
      - `encrypted`: boolean value for whether the data file is encrypted. If
        `True`, the data file is automatically decrypted prior to the callback
        function being called. Decryption parameters are obtained
        from the `key` and `iv` attributes of the spider if provided, or are
        otherwise automatically detected from parsing `self.start_urls[0]`.
      - `callback_function_name`: a string with a value being the name of a
        function implemented by the spider which is called for each data file.
        Must have one of the following definitions:
          1. `def callback_function(self, features: list[dict]) -> list[Feature]
          2. `def callback_function(self, features: list[dict]) -> (list[dict], RosettaAPRDataFile)
          3. `def callback_function(self, features: list[dict], existing_features: list[dict]) -> list[Feature]
          4. `def callback_function(self, features: list[dict], existing_features: list[dict]) -> (list[dict], RosettaAPRDataFile)
        Definition (1) is the simplest and is used whenever all the fields of
        data required to describe a feature are included in a single data file
        which has been downloaded. There is no need to download additional
        data files to supplement/merge fields of data across two or more data
        files.
        Definition (2) is used when downloading the first data file, knowing
        that additional data files need to be subsequently downloaded and
        parsed to supplement/merge fields of data across two or more data
        files.
        Definition (3) is used for parsing an additional data file and
        supplementing/merging data fields across two or more data files. In
        this definition, there is no need to download a third (or any
        additional) data file.
        Definition (4) is used for parsing an additional data file and
        supplementing/merging data fields across two or more data files. In
        this definition, there is a need to download a third, or fourth, or
        any additional number of data files. The callback function for the
        last data file to be downloaded in succession should be definition
        (3).
      - `archive_format`: a string with the value of `"zip"`, or the default
        `None` value if the data file is not a compressed archive.
      - `archive_filename`: a string which is the name of a filename within
        a compressed archive. This `archive_filename` attribute is ignored if
        `archive_format` is the default value of `None`.
      - `column_headings`: a list of column headings to use if `file_type` is
        `"csv"`. This attribute is ignored for other values of `file_type`. An
        example is `column_headings = ["ID", "NAME", "LAT", "LON"]`. If this
        `column_headings` attribute is left undefined (default of `None`) then
        the first row of the CSV file will be used as headings.
    """

    url: str
    file_type: str
    encrypted: bool
    callback_function_name: str
    archive_format: str | None = None
    archive_filename: str | None = None
    column_headings: list[str] | None = None


class RosettaAPRSpider(Spider):
    """
    Rosetta Analytics APR Portal is used by Australian electricity network
    operators for providing public data on the electricity network and assets
    within. A list of users is provided at:
      https://rosettaanalytics.com.au/apr-portal/

    To use this spider, specify `start_urls[0]` as the APR Portal website for
    an electricity network operator. This `start_urls[0]` will probably be one
    of the URLs listed at https://rosettaanalytics.com.au/apr-portal/

    Also specify one or more data files in the `data_files` list. These data
    files will be downloaded from the selected APR Portal and then can be
    individually parsed. Each item in the `data_files` list is expected to be
    a named tuple of type `RosettaAPRDataFile`.

    By default, decryption parameters for encrypted data files are
    automatically extracted from parsing of `self.start_urls[0]`. Should this
    automatic extraction not work, decryption parameters can be specified
    manually with `key` and `iv` attributes. These attributes are expected to
    be strings in hexadecimal notation and are passed into a AES256-CBC
    function. `key` is expected to have a length of 64, and `iv` a length of
    32.

    There is no guarantee provided for the order in which data files are
    downloaded and the callback function called.
    """

    data_files: list[RosettaAPRDataFile] = []
    key: str | None = None
    iv: str | None = None

    def start_requests(self) -> Iterable[Request]:
        if (not self.key or not self.iv) and True in [x[2] for x in self.data_files]:
            yield Request(url=self.start_urls[0], callback=self.parse_decryption_params)
        else:
            yield from self.request_data_files()

    def parse_decryption_params(self, response: Response) -> Iterable[Request]:
        js_blob_candidates = response.xpath('//script[contains(text(), "var _0x")]/text()').getall()
        for js_blob_candidate in js_blob_candidates:
            if m := re.search(r"^\s*var _0x[0-9a-f]{4}\s*=\s*\[", js_blob_candidate, flags=re.MULTILINE):
                obfuscated_js_array = js_blob_candidate[m.start(0) :].split("[", 1)[1].split("];", 1)[0]
                obfuscated_js_array = list(
                    map(
                        lambda x: bytes.fromhex(x.strip('"').replace("\\x", " ")).decode(
                            "utf-8", errors="backslashreplace"
                        ),
                        obfuscated_js_array.split(","),
                    )
                )
                for pair in pairwise(obfuscated_js_array):
                    if re.fullmatch(r"[0-9a-f]{64}", pair[0]) and re.fullmatch("[0-9a-f]{32}", pair[1]):
                        self.key = pair[0]
                        self.iv = pair[1]
                        break
                if self.key and self.iv:
                    break
        if not self.key or not self.iv:
            raise Exception(
                "Could not automatically locate required AES256-CBC key and IV values for decrypting data files."
            )
            return
        yield from self.request_data_files()

    def request_data_files(self) -> Iterable[Request]:
        for data_file in self.data_files:
            yield from self.request_data_file(data_file=data_file)

    def request_data_file(self, data_file: RosettaAPRDataFile, meta: dict = {}) -> Iterable[Request]:
        new_meta = meta.copy()
        new_meta.update({"data_file": data_file})
        if data_file.url.startswith("https://") or data_file.url.startswith("http://"):
            # Data file hosted externally.
            yield Request(url=data_file.url, meta=new_meta, callback=self.parse_data_file)
        else:
            # Data file served directly from the same domain.
            yield Request(
                url=urljoin(self.start_urls[0], f"/serve.php?file={data_file[0]}"),
                meta=new_meta,
                callback=self.parse_data_file,
            )

    def parse_data_file(self, response: Response) -> Iterable[Feature | Request]:
        features = self.decode_data_file(
            raw_data_file=response.body,
            file_type=response.meta["data_file"].file_type,
            encrypted=response.meta["data_file"].encrypted,
            archive_format=response.meta["data_file"].archive_format,
            archive_filename=response.meta["data_file"].archive_filename,
            column_headings=response.meta["data_file"].column_headings,
        )

        callback_function = getattr(self, response.meta["data_file"].callback_function_name)
        type_hints = get_type_hints(callback_function)
        if (
            "features" in type_hints.keys()
            and str(type_hints["features"]) == "list[dict]"
            and "return" in type_hints.keys()
        ):
            if "existing_features" in type_hints.keys() and str(type_hints["existing_features"]) == "list[dict]":
                if str(type_hints["return"]) == "list[locations.items.Feature]":
                    # Handles callback functions of definition:
                    # def callback_function(self, features: list[dict], existing_features: list[dict]) -> list[Feature]
                    items = callback_function(features, response.meta["existing_features"])
                    for item in items:
                        yield item
                elif (
                    str(type_hints["return"])
                    == "(list[dict], <class 'locations.storefinders.rosetta_apr.RosettaAPRDataFile'>)"
                ):
                    # Handles callback functions of definition:
                    # def callback_function(self, features: list[dict], existing_features: list[dict]) -> (list[dict], RosettaAPRDataFile)
                    items, data_file = callback_function(features, response.meta["existing_features"])
                    yield from self.request_data_file(data_file=data_file, meta={"existing_features": items})
                else:
                    raise Exception(
                        'Invalid callback function signature for callback function "{}".'.format(callback_function_name)
                    )
            else:
                if str(type_hints["return"]) == "list[locations.items.Feature]":
                    # Handles callback functions of definition:
                    # def callback_function(self, features: list[dict]) -> list[Feature]
                    items = callback_function(features)
                    for item in items:
                        yield item
                elif (
                    str(type_hints["return"])
                    == "(list[dict], <class 'locations.storefinders.rosetta_apr.RosettaAPRDataFile'>)"
                ):
                    # Handles callback functions of definition:
                    # def callback_function(self, features: list[dict]) -> (list[dict], RosettaAPRDataFile)
                    items, data_file = callback_function(features)
                    yield from self.request_data_file(data_file=data_file, meta={"existing_features": items})
                else:
                    raise Exception(
                        'Invalid callback function signature for callback function "{}".'.format(callback_function_name)
                    )
        else:
            raise Exception(
                'Invalid callback function signature for callback function "{}".'.format(callback_function_name)
            )

    def decode_data_file(
        self,
        raw_data_file: bytes,
        file_type: str,
        encrypted: bool,
        archive_format: str | None = None,
        archive_filename: str | None = None,
        column_headings: list[str] | None = None,
    ) -> list[dict]:
        if encrypted:
            ciphertext = b64decode(raw_data_file.decode("utf-8"))
            unpadded_plaintext = decrypt_aes256cbc_pkcs7(ciphertext=ciphertext, key=self.key, iv=self.iv)
            if archive_format == "zip":
                data_file_bytes = unzip_file_from_archive(
                    compressed_data=unpadded_plaintext, file_path=archive_filename
                )
            else:
                data_file_bytes = unpadded_plaintext
        elif archive_format == "zip":
            data_file_bytes = unzip_file_from_archive(compressed_data=raw_data_file, file_path=archive_filename)
        elif archive_format:
            raise Exception("Unknown archive format for data file: {}.".format(archive_format))
            return
        else:
            data_file_bytes = raw_data_file

        features = []
        match file_type:
            case "csv":
                data_file_str = data_file_bytes.decode("utf-8")
                sniffed_dialect = csv.Sniffer().sniff(data_file_str[:1024])
                reader = csv.DictReader(data_file_str.splitlines(), fieldnames=column_headings, dialect=sniffed_dialect)
                for row in reader:
                    features.append(row)
            case "geojson":
                data_file_str = data_file_bytes.decode("utf-8")
                features = loads(data_file_str)["features"]
                for feature in features:
                    feature.update(feature["properties"])
                    del feature["properties"]
            case _:
                raise Exception("Unknown file type for data file: {}.".format(file_type))

        return features
