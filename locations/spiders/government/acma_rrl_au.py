import csv
from io import StringIO
from math import ceil, floor
from typing import Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.archive_utils import unzip_file_from_archive
from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.user_agents import BROWSER_DEFAULT


class AcmaRrlAUSpider(Spider):
    name = "acma_rrl_au"
    allowed_domains = ["web.acma.gov.au"]
    start_urls = ["https://web.acma.gov.au/rrl-updates/spectra_rrl.zip"]
    custom_settings = {"ROBOTSTXT_OBEY": False, "DOWNLOAD_TIMEOUT": 120, "DOWNLOAD_WARNSIZE": 268435456}
    user_agent = BROWSER_DEFAULT

    _clients = {}
    _licences = {}
    _sites = {}
    _antenna_types = {}

    def parse(self, response: Response) -> Iterable[Feature]:
        self.parse_clients(response)
        self.parse_licences(response)
        self.parse_sites(response)
        self.parse_antenna_types(response)
        yield from self.parse_devices(response)

    def parse_clients(self, response: Response) -> None:
        clients_csv = unzip_file_from_archive(response.body, "client.csv")
        clients_list = csv.DictReader(StringIO(clients_csv.decode("utf-8")))
        for client in clients_list:
            self._clients[int(client["CLIENT_NO"])] = {
                "operator": client["LICENCEE"],
                "operator:ref:abn": client["ABN"],
                "operator:ref:acn": client["ACN"],
            }

    def parse_licences(self, response: Response) -> None:
        licences_csv = unzip_file_from_archive(response.body, "licence.csv")
        licences_list = csv.DictReader(StringIO(licences_csv.decode("utf-8")))
        for licence in licences_list:
            if licence["LICENCE_TYPE_NAME"] in ["Maritime Ship"]:
                # Ignore licences for ships (no associated client).
                continue
            self._licences[licence["LICENCE_NO"]] = {
                "_client_no": int(licence["CLIENT_NO"]),
                "_category": licence["LICENCE_CATEGORY_NAME"],
            }

    def parse_sites(self, response: Response) -> None:
        sites_csv = unzip_file_from_archive(response.body, "site.csv")
        sites_list = csv.DictReader(StringIO(sites_csv.decode("utf-8")))
        for site in sites_list:
            self._sites[int(site["SITE_ID"])] = {
                "name": site["NAME"],
                "lat": site["LATITUDE"],
                "lon": site["LONGITUDE"],
                "ele": site["ELEVATION"],
            }

    def parse_antenna_types(self, response: Response) -> None:
        antenna_types_csv = unzip_file_from_archive(response.body, "antenna.csv")
        antenna_types_list = csv.DictReader(StringIO(antenna_types_csv.decode("utf-8")))
        for antenna_type in antenna_types_list:
            self._antenna_types[int(antenna_type["ANTENNA_ID"])] = {
                "manufacturer": antenna_type["MANUFACTURER"],
                "model": antenna_type["MODEL"],
                "antenna:configuration": antenna_type["ANTENNA_TYPE"],
            }

    def parse_devices(self, response: Response) -> Iterable[Feature]:
        devices_csv = unzip_file_from_archive(response.body, "device_details.csv")
        devices_list = csv.DictReader(StringIO(devices_csv.decode("utf-8")))
        for device in devices_list:
            if device["AREA_AREA_ID"] or not device["SITE_ID"]:
                # Device has no fixed site and/or is a mobile device that is
                # authorised to be used in a particular region (or all of
                # Australia). An example is radios mounted to ships.
                continue
            properties = {
                "ref": str(device["SDD_ID"]),
                "extras": {},
            }
            self.extract_site_properties(properties, device)
            self.extract_client_properties(properties, device)
            self.extract_antenna_properties(properties, device)
            self.extract_device_properties(properties, device)
            self.extract_acma_reference_properties(properties, device)
            self.extract_category(properties, device)
            if device["DEVICE_REGISTRATION_IDENTIFIER"]:
                properties["website"] = "https://web.acma.gov.au/rrl/assignment_search.lookup?pDEVICE_REGISTRATION_ID=" + str(device["DEVICE_REGISTRATION_IDENTIFIER"])
            elif device["EFL_ID"]:
                properties["website"] = "https://web.acma.gov.au/rrl/assignment_search.lookup?pEFL_ID=" + str(device["EFL_ID"])
            yield Feature(**properties)

    def extract_site_properties(self, properties: dict, device_details: dict) -> None:
        if not device_details["SITE_ID"]:
            return
        site_id = int(device_details["SITE_ID"])
        if site_id not in self._sites.keys():
            return
        properties["name"] = self._sites[site_id]["name"]
        properties["lat"] = self._sites[site_id]["lat"]
        properties["lon"] = self._sites[site_id]["lon"]
        if elevation_m := self._sites[site_id]["ele"]:
            properties["extras"]["ele"] = f"{elevation_m}"

    def extract_client_properties(self, properties: dict, device_details: dict) -> None:
        if device_details["LICENCE_NO"] not in self._licences.keys():
            return
        client_id = int(self._licences[device_details["LICENCE_NO"]]["_client_no"])
        if client_id not in self._clients.keys():
            return
        properties["operator"] = self._clients[client_id]["operator"]
        properties["extras"]["operator:ref:abn"] = self._clients[client_id]["operator:ref:abn"]
        properties["extras"]["operator:ref:acn"] = self._clients[client_id]["operator:ref:acn"]

    def extract_antenna_properties(self, properties: dict, device_details: dict) -> None:
        if not device_details["ANTENNA_ID"]:
            return
        antenna_type_id = int(device_details["ANTENNA_ID"])
        if antenna_type_id not in self._antenna_types.keys():
            return
        properties["extras"]["manufacturer"] = self._antenna_types[antenna_type_id]["manufacturer"]
        properties["extras"]["model"] = self._antenna_types[antenna_type_id]["model"]
        properties["extras"]["antenna:configuration"] = self._antenna_types[antenna_type_id]["antenna:configuration"]

    def extract_device_properties(self, properties: dict, device_details: dict) -> None:
        if device_details["FREQUENCY"] and device_details["BANDWIDTH"]:
            frequency_band_low = floor(float(device_details["FREQUENCY"]) - float(device_details["BANDWIDTH"]) / 2)
            frequency_band_high = ceil(float(device_details["FREQUENCY"]) + float(device_details["BANDWIDTH"]) / 2)
            properties["extras"]["frequency"] = f"{frequency_band_low} - {frequency_band_high}"
        if height_m := device_details["HEIGHT"]:
            if float(height_m) > 0:
                properties["extras"]["height"] = f"{height_m}"
        if direction_degrees := device_details["AZIMUTH"]:
            if float(direction_degrees) >= -359 and float(direction_degrees) <= 359:
                properties["extras"]["direction"] = f"{direction_degrees}"
        if incline_degrees := device_details["TILT"]:
            if float(incline_degrees) >= -90 and float(incline_degrees) <= 90:
                properties["extras"]["incline"] = f"{incline_degrees}°"
        if rating_w := device_details["TRANSMITTER_POWER"]:
            if float(rating_w) > 0:
                properties["extras"]["rating"] = f"{rating_w} W"
        if eirp_w := device_details["EIRP"]:
            if float(eirp_w) > 0:
                properties["extras"]["antenna:eirp"] = f"{eirp_w} W"
        if directionality := device_details["DEVICE_TYPE"]:
            if directionality == "T":
                properties["extras"]["antenna:transmit"] = "yes"
            elif directionality == "R":
                properties["extras"]["antenna:receive"] = "yes"
        if polarisation := device_details["POLARISATION"]:
            match polarisation:
                case "CL":
                    properties["extras"]["antenna:polarisation"] = "left hand circular"
                case "CR":
                    properties["extras"]["antenna:polarisation"] = "right hand circular"
                case "D":
                    properties["extras"]["antenna:polarisation"] = "dual"
                case "H":
                    properties["extras"]["antenna:polarisation"] = "horizontal linear"
                case "L":
                    properties["extras"]["antenna:polarisation"] = "linear"
                case "M":
                    properties["extras"]["antenna:polarisation"] = "mixed"
                case "S":
                    properties["extras"]["antenna:polarisation"] = "slant"
                case "SL":
                    properties["extras"]["antenna:polarisation"] = "left hand slant"
                case "SR":
                    properties["extras"]["antenna:polarisation"] = "right hand slant"
                case "V":
                    properties["extras"]["antenna:polarisation"] = "vertical linear"

    def extract_acma_reference_properties(self, properties: dict, device_details: dict) -> None:
        properties["extras"]["ref:AU:ACMA:SDD_ID"] = device_details["SDD_ID"]
        if licence_no := device_details["LICENCE_NO"]:
            properties["extras"]["ref:AU:ACMA:LICENCE_NO"] = licence_no
        if device_registration_identifier := device_details["DEVICE_REGISTRATION_IDENTIFIER"]:
            properties["extras"]["ref:AU:ACMA:DEVICE_REGISTRATION_IDENTIFIER"] = device_registration_identifier
        if site_id := device_details["SITE_ID"]:
            properties["extras"]["ref:AU:ACMA:SITE_ID"] = site_id
        if antenna_type_id := device_details["ANTENNA_ID"]:
            properties["extras"]["ref:AU:ACMA:ANTENNA_ID"] = antenna_type_id
        if efl_id := device_details["EFL_ID"]:
            properties["extras"]["ref:AU:ACMA:EFL_ID"] = efl_id
        if related_efl_id := device_details["RELATED_EFL_ID"]:
            properties["extras"]["ref:AU:ACMA:RELATED_EFL_ID"] = related_efl_id
        if eqp_id := device_details["EQP_ID"]:
            properties["extras"]["ref:AU:ACMA:EQP_ID"] = eqp_id

    def extract_category(self, properties: dict, device_details: dict) -> None:
        apply_category(Categories.ANTENNA, properties)
        if device_details["LICENCE_NO"] not in self._licences.keys():
            return
        client_id = int(self._licences[device_details["LICENCE_NO"]]["_client_no"])
        if client_id in [20053843, 1149289, 1136980, 20009217]:
            # Telstra (20053843), Optus (1149289), Vodafone (1136980) and TPG
            # (20009217) are clients with only 4G/5G spectrum licenses. These
            # client identifiers will only be seen for 4G/5G devices.
            properties["extras"]["communication:mobile_phone"] = "yes"
        elif device_details["CLASS_OF_STATION_CODE"] == "BT":
            # Television broadcast antenna.
            properties["extras"]["communication:television"] = "yes"
        elif device_details["CLASS_OF_STATION_CODE"] == "BC":
            # AM/FM radio broadcast antenna.
            properties["extras"]["communication:radio"] = "yes"
