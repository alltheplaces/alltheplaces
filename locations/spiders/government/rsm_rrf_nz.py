from math import ceil, floor
from typing import AsyncIterator, Iterable

from pyproj import Transformer
from scrapy import Spider
from scrapy.http import JsonRequest, TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature


class RsmRrfNZSpider(Spider):
    name = "rsm_rrf_nz"
    allowed_domains = ["rrf.rsm.govt.nz"]
    start_urls = ["https://rrf.rsm.govt.nz/api/public_search/licence"]
    _frequency_ranges_mhz = [
        (0.000001, 199.999999),
        (200, 499.999999),
        (500, 999.999999),
        (1000, 1000000),
    ]
    # Individual antennas under a licence share identifiers. There is no
    # unique identifier or counter for individual antennas under the
    # same licence. If making an alternative API call to retrieve details of
    # an individual licence, a site ID is also available, and a unique
    # identifier of e.g. licence ID, site ID and reference frequency could
    # possibly be used to create a unique antenna ID. However, this would
    # require hundreds of thousands of API calls.
    no_refs = True
    _transformer = Transformer.from_crs(4167, 4326)

    @staticmethod
    def _make_request(page_number: int, frequency_low_mhz: float, frequency_high_mhz: float) -> JsonRequest:
        api_endpoint = "https://rrf.rsm.govt.nz/api/public_search/licence"
        data = {
            "isRelevanceSort": True,
            "isSearchVisible": False,
            "licenceStatus": ["Current"],
            "orderBy": "id desc",
            "page": page_number,
            "pageSize": 1000,
            "refFrequencyFrom": f"{frequency_low_mhz}",
            "refFrequencyTo": f"{frequency_high_mhz}",
            "searchText": "",
            "suppressed": False,
        }
        return JsonRequest(
            url=api_endpoint,
            data=data,
            meta={"f_low_mhz": frequency_low_mhz, "f_high_mhz": frequency_high_mhz},
            method="POST",
        )

    async def start(self) -> AsyncIterator[JsonRequest]:
        for frequency_range_mhz in self._frequency_ranges_mhz:
            # A maximum of 100000 results can be returned per query of the API
            # so the queries have to be split into batches (by frequency bands
            # is the easiest method to use).
            yield self._make_request(1, frequency_range_mhz[0], frequency_range_mhz[1])

    def parse(self, response: TextResponse) -> Iterable[Feature]:
        total_items = response.json()["totalItems"]
        if total_items >= 100000:
            f_low_mhz = response.meta["f_low_mhz"]
            f_high_mhz = response.meta["f_high_mhz"]
            error_message = "More than 100000 results returned from query of frequency range {}-{}MHz. Results have been truncated as only the first 100000 results are provided by the API.".format(
                f_low_mhz, f_high_mhz
            )
            raise RuntimeError(error_message)

        for licence in response.json()["results"]:
            if licence["licenceStatus"] != "Current":
                self.logger.warning(
                    "Unknown licence status '{}' for licence ID '{}'".format(licence["licenceStatus"], licence["id"])
                )
                continue

            if not licence["locationGeoReferences"]:
                # Licence is for antennas with no fixed location, for example,
                # it is a licence to transmit anywhere within a region or the
                # entire country with a portable transmitter.
                continue

            properties = {
                "name": licence["location"],
                "extras": {},
            }
            self.extract_operator_properties(properties, licence)
            self.extract_geographic_location(properties, licence)
            self.extract_radio_details(properties, licence)
            self.extract_rsm_reference_properties(properties, licence)
            self.extract_category(properties, licence)

            yield Feature(**properties)

        page_count = response.json()["totalPages"]
        if page_count > 1:
            for page_number in range(2, page_count + 1):
                yield self._make_request(page_number, response.meta["f_low_mhz"], response.meta["f_high_mhz"])

    def extract_operator_properties(self, properties: dict, licence_details: dict) -> None:
        properties["operator"] = licence_details["licensee"]
        if nzbn := licence_details["clientNzbn"]:
            properties["extras"]["operator:ref:nzbn"] = str(nzbn)

    def extract_geographic_location(self, properties: dict, licence_details: dict) -> None:
        for coordinates_crs in licence_details["locationGeoReferences"]:
            if coordinates_crs["type"] not in ["D2000", "D"]:
                continue
            lat_epsg4167 = float(coordinates_crs["gridReference"].split(" ", 1)[0].strip())
            lon_epsg4167 = float(coordinates_crs["gridReference"].split(" ", 1)[1].strip())
            properties["lat"], properties["lon"] = self._transformer.transform(lat_epsg4167, lon_epsg4167)
            break

    def extract_radio_details(self, properties: dict, licence_details: dict) -> None:
        frequency_band_low = floor(licence_details["lowerBound"] * 1000000)
        frequency_band_high = ceil(licence_details["upperBound"] * 1000000)
        properties["extras"]["frequency"] = f"{frequency_band_low} - {frequency_band_high}"
        if eirp_dbw := licence_details["power"]:
            properties["extras"]["antenna:eirp"] = f"{eirp_dbw} dBW"
        if polarisation := licence_details["polarisation"]:
            match polarisation:
                case "A":
                    properties["extras"]["antenna:polarisation"] = "left hand circular"
                case "C":
                    properties["extras"]["antenna:polarisation"] = "right hand circular"
                case "H":
                    properties["extras"]["antenna:polarisation"] = "horizontal linear"
                case "L":
                    properties["extras"]["antenna:polarisation"] = "linear;mixed"
                case "M":
                    properties["extras"]["antenna:polarisation"] = "mixed"
                case "N":
                    # Non-specific polarisation type -- ignore
                    # Used for general spectrum allocations where antennas are
                    # varied and a choice of the operator.
                    pass
                case "O":
                    # Other polarisation type -- ignore
                    pass
                case "P":
                    properties["extras"]["antenna:polarisation"] = "cross polar"
                case "R":
                    properties["extras"]["antenna:polarisation"] = "circular"
                case "S":
                    properties["extras"]["antenna:polarisation"] = "slant"
                case "V":
                    properties["extras"]["antenna:polarisation"] = "vertical linear"
                case "X":
                    properties["extras"]["antenna:polarisation"] = "dual slant"
                case _:
                    self.logger.warning(
                        "Unknown polarisation type '{}' for licence ID '{}'".format(polarisation, licence_details["id"])
                    )
        if directionality := licence_details["receiveTransmitDisplayType"]:
            if directionality == "TX":
                properties["extras"]["antenna:transmit"] = "yes"
            elif directionality == "RX":
                properties["extras"]["antenna:receive"] = "yes"

    def extract_rsm_reference_properties(self, properties: dict, licence_details: dict) -> None:
        if client_id := licence_details["clientId"]:
            properties["extras"]["ref:NZ:RSM:client_id"] = str(client_id)
        if licence_number := licence_details["licenceNo"]:
            properties["extras"]["ref:NZ:RSM:licence_no"] = str(licence_number)

    def extract_category(self, properties: dict, licence_details: dict) -> None:
        apply_category(Categories.ANTENNA, properties)
        if licence_details["clientId"] in [134563, 134726, 528522]:
            # Spark (134563), One NZ (134726) and 2degrees (528522) are clients
            # with 4G/5G spectrum licenses. These clients may have other types
            # of licensed antennas other than mobile phone antennas, so only
            # antennas with expected mobile frequencies should be counted.
            if ref_freq_mhz := licence_details["refFrequency"]:
                if (
                    (ref_freq_mhz > 700 and ref_freq_mhz < 1000)
                    or (ref_freq_mhz > 1700 and ref_freq_mhz < 2400)
                    or (ref_freq_mhz > 2500 and ref_freq_mhz < 2700)
                    or (ref_freq_mhz > 3400 and ref_freq_mhz < 3700)
                ):
                    # Approximate bounds of 4G/5G frequencies used in NZ. Good
                    # enough to exclude satellite communications (etc) of
                    # these mobile phone network operators.
                    properties["extras"]["communication:mobile_phone"] = "yes"
        else:
            if licence_type_id := licence_details["licenceTypeId"]:
                match licence_type_id:
                    case 32 | 157 | 162:
                        # 32 = HF AM, 157 = MF AM, 162 = UHF FM
                        properties["extras"]["communication:radio"] = "yes"
                    case 169:
                        properties["extras"]["communication:television"] = "yes"
