import csv
from io import BytesIO, TextIOWrapper
from typing import Iterable
from zipfile import ZipFile

from scrapy.http import Request, Response

from locations.address_spider import AddressSpider
from locations.items import Feature
from locations.licenses import Licenses


class KartverketAddressesNOSpider(AddressSpider):
    """
    Spider to collect addresses from Norway's official address registry (Matrikkelen).

    Data is provided by Kartverket (Norwegian Mapping Authority) via CSV downloads.
    """

    name = "kartverket_addresses_no"
    allowed_domains = ["nedlasting.geonorge.no"]
    dataset_attributes = Licenses.CC4.value | {
        "attribution:website": "https://kartkatalog.geonorge.no/metadata/matrikkelen-adresse/f7df7a18-b30f-4745-bd64-d0863812350c",
        "attribution:name": "Contains data from Matrikkelen - Adresse distributed by Kartverket"
    }
    custom_settings = {"DOWNLOAD_TIMEOUT": 300, "CONCURRENT_REQUESTS": 4}

    # File format: Basisdata_<areaCode>_<areaName>_<projection>_MatrikkelenAdresse_CSV.zip
    csv_url = "https://nedlasting.geonorge.no/geonorge/Basisdata/MatrikkelenAdresse/CSV/Basisdata_0000_Norge_4258_MatrikkelenAdresse_CSV.zip"

    def start_requests(self) -> Iterable[Request]:
        yield Request(url=self.csv_url, callback=self.parse_zip)

    def parse_zip(self, response: Response) -> Iterable[Feature]:
        with ZipFile(BytesIO(response.body)) as zip_file:
            csv_name = None
            for name in zip_file.namelist():
                if name.lower().endswith("matrikkelenadresse.csv"):
                    csv_name = name
                    break
            if not csv_name:
                for name in zip_file.namelist():
                    if name.lower().endswith(".csv"):
                        csv_name = name
                        break
            if not csv_name:
                self.logger.warning("No CSV found in %s", response.url)
                return

            with zip_file.open(csv_name) as csv_file:
                reader = csv.DictReader(TextIOWrapper(csv_file, encoding="utf-8"), delimiter=";")
                for row in reader:
                    yield self.parse_address(row)

    def parse_address(self, row: dict) -> Feature:
        """Parse a single address from the CSV row into a Feature item."""
        item = Feature()

        # Unique reference (adresseId)
        item["ref"] = self._strip_value(row.get("adresseId"))

        # Coordinates
        item["lat"] = self._parse_float(row.get("Nord"))
        item["lon"] = self._parse_float(row.get("\u00d8st"))

        # Address components
        item["street"] = self._strip_value(row.get("adressenavn"))
        item["housenumber"] = self._format_housenumber(row)
        item["city"] = self._strip_value(row.get("poststed"))
        item["postcode"] = self._strip_value(row.get("postnummer"))
        item["country"] = "NO"

        # Municipality information
        item["extras"] = {
            "ref:NO:kommunenummer": self._strip_value(row.get("kommunenummer")),
            "addr:municipality": self._strip_value(row.get("kommunenavn")),
        }

        # Additional address name (farm name, institution name, etc.)
        if tilleggsnavn := self._strip_value(row.get("adressetilleggsnavn")):
            item["extras"]["addr:place"] = tilleggsnavn

        # Address type (Vegadresse or Matrikkeladresse)
        if objtype := self._strip_value(row.get("objtype")):
            item["extras"]["addr:type"] = objtype

        # Matrikkel references for cadastral addresses
        if gardsnummer := self._strip_value(row.get("gardsnummer")):
            item["extras"]["ref:NO:gardsnummer"] = gardsnummer
        if bruksnummer := self._strip_value(row.get("bruksnummer")):
            item["extras"]["ref:NO:bruksnummer"] = bruksnummer
        if festenummer := self._strip_value(row.get("festenummer")):
            item["extras"]["ref:NO:festenummer"] = festenummer
        if undernummer := self._strip_value(row.get("undernummer")):
            item["extras"]["ref:NO:undernummer"] = undernummer

        # Unit numbers (apartments)
        if bruksenhetsnummer := self._strip_value(row.get("bruksenhetsnummer")):
            item["extras"]["addr:unit"] = bruksenhetsnummer

        return item

    def _format_housenumber(self, row: dict) -> str | None:
        """Format the house number from nummer and bokstav fields."""
        nummer = row.get("nummer")
        bokstav = row.get("bokstav")

        if nummer is None:
            return None

        if bokstav:
            return f"{nummer}{bokstav}"
        return str(nummer)

    def _strip_value(self, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    def _parse_float(self, value: str | None) -> float | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            return None
        try:
            return float(value)
        except ValueError:
            return None
