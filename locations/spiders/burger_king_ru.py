import re
from typing import Any, Iterable

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.user_agents import BROWSER_DEFAULT


class BurgerKingRUSpider(Spider):
    name = "burger_king_ru"
    item_attributes = {"brand": "Бургер Кинг", "brand_wikidata": "Q177054"}
    allowed_domains = ["orderapp.burgerkingrus.ru"]
    user_agent = BROWSER_DEFAULT
    api_url = "https://orderapp.burgerkingrus.ru/api/v3/restaurant/list"
    requires_proxy = True  # Qrator bot blocking in use

    def start_requests(self) -> Iterable[Request]:
        yield JsonRequest(
            url=self.api_url,
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        if "RSA PRIVATE KEY" in response.text:  # set cookies using the response received if expected JSON is not there
            sp_id = ""
            rsa_key_pem = ""
            encrypted_text = ""
            if match := re.search(r"\"spid=(\w+)\"", response.text):
                sp_id = match.group(1)
            if match := re.search(r"(-+BEGIN RSA PRIVATE KEY-+.+?-+END RSA PRIVATE KEY-+)", response.text, re.DOTALL):
                rsa_key_pem = match.group(1)
            if match := re.search(r"crypto.Cipher.decrypt\(\"(\w+)\",", response.text):
                encrypted_text = match.group(1)

            private_key_pem = rsa_key_pem.encode("utf-8")

            # Encrypted ciphertext (as bytes)
            encrypted_text = bytes.fromhex(encrypted_text)

            # Load the private key
            private_key = serialization.load_pem_private_key(
                private_key_pem,
                password=None,
            )

            # Decrypt the ciphertext
            decrypted_text = private_key.decrypt(encrypted_text, padding.PKCS1v15())

            sp_sc = decrypted_text.decode("utf-8")

            yield JsonRequest(
                url=self.api_url,
                cookies={
                    "spid": sp_id,
                    "spsc": sp_sc,
                },
                callback=self.parse_locations,
                dont_filter=True,
            )

        else:
            yield from self.parse_locations(response)

    def parse_locations(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["response"]["list"]:
            if location["status"] != 1:
                continue
            address_info = location.pop("name")  # name contains address info
            item = DictParser.parse(location)
            item["street_address"] = item.pop("addr_full", None) or address_info
            item["opening_hours"] = OpeningHours()
            for day_number, day_name in enumerate(DAYS):
                day_hours = location["timetable"]["hall"][day_number]
                if not day_hours["isActive"]:
                    continue
                if day_hours["isAllTime"]:
                    start_time = "00:00"
                    end_time = "23:59"
                else:
                    start_time = day_hours["timeFrom"]
                    end_time = day_hours["timeTill"]
                item["opening_hours"].add_range(day_name, start_time, end_time)
            apply_yes_no(Extras.WIFI, item, location["wifi"], False)
            apply_yes_no(Extras.DRIVE_THROUGH, item, location["king_drive"] and location["king_drive_enabled"], False)
            yield item
