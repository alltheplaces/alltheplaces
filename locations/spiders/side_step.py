import random
import time
from typing import Any

from chompjs import parse_js_object
from scrapy import Spider
from scrapy.http import FormRequest, Response

from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class SideStepSpider(Spider):
    name = "side_step"
    allowed_domains = ["www.side-step.co.za"]
    item_attributes = {"brand": "Side Step", "brand_wikidata": "Q116894527"}
    requires_proxy = "ZA"

    def start_requests(self):
        form_key = self.get_form_key()
        req_time = str(int(time.time() * 1000))
        yield FormRequest(
            f"https://www.side-step.co.za/store_locator/location/updatemainpage?_={req_time}",
            formdata={"form_key": form_key},
            headers={"x-requested-with": "XMLHttpRequest"},
            callback=self.parse_stores,
        )

    def get_form_key(self):
        # Not 100% sure if this is necessary, but replicates what the page does
        allowedCharacters = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        formKey = ""
        for i in range(16):
            formKey += allowedCharacters[int(random.random() * 16)]
        return formKey

    def parse_stores(self, response: Response, **kwargs: Any) -> Any:
        store_positions = {}
        markers = response.xpath('.//script[contains(text(), "var locationsDefault = [];")]/text()').get()
        for line in markers.split("\n"):
            if "locations['" in line:
                id = parse_js_object(line.split("=")[0])[0]
                coords = parse_js_object(line.split("=")[1])
                store_positions[id] = coords

        for location in response.xpath('.//li[contains(@class, "location-info")]'):
            item = Feature()
            item["ref"] = (
                location.xpath('.//div[contains(@x-ref, "mw-location_details_")]/@x-ref')
                .get()
                .replace("mw-location_details_", "")
            )
            item["lat"] = store_positions[item["ref"]]["lat"]
            item["lon"] = store_positions[item["ref"]]["lng"]
            branch_raw = location.xpath('.//address/span[@class="font-bold"]/text()').get()
            item["branch"] = branch_raw.strip()
            addr_all = location.xpath(".//address/span//text()").getall()
            addr_all.remove(branch_raw)
            addr_all = [i.replace("\\n", ",") for i in addr_all]
            item["addr_full"] = clean_address(addr_all)
            yield item
            # Could now hit https://www.side-step.co.za/store_locator/location/locationdetail?_={new_req_time}&id={item['ref']}&current_page=cms_page_view
            # but only extra info appears to be a phone number
