import re
from typing import Iterable

from scrapy.http import FormRequest, Request, Response

from locations.categories import Categories, apply_category
from locations.hours import CLOSED_IT, DAYS_IT, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class SigmaITSpider(JSONBlobSpider):
    name = "sigma_it"
    item_attributes = {"brand": "Sigma", "brand_wikidata": "Q3977979"}
    allowed_domains = ["www.supersigma.com"]
    start_urls = ["https://www.supersigma.com/wp-admin/admin-ajax.php"]
    locations_key = ["map_args", "locations"]

    def start_requests(self) -> Iterable[FormRequest]:
        formdata = {
            "action": "gmw_form_ajax_submission",
            "submitted": "true",
            "form_id": "2",
            "form_values": "address%5B%5D=Napoli&distance=100000&units=metric&post%5B%5D=store&page=1&per_page=10000&lat=40.85177&lng=14.26812&swlatlng=&nelatlng=&form=2&action=fs",
        }
        yield FormRequest(url=self.start_urls[0], formdata=formdata)

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Request]:
        item["ref"] = feature["location_id"]
        branch_name = feature["location_name"]
        if " di " in branch_name:
            branch_name = branch_name.split(" di ", 1)[1]
        elif " DI" in branch_name:
            branch_name = branch_name.split(" DI ", 1)[1]
        if " (" in branch_name:
            branch_name = branch_name.split(" (", 1)[0]
        item["branch"] = branch_name
        item.pop("name", None)
        item["street_address"] = item.pop("street")
        item["website"] = "https://www.supersigma.com/?p=" + feature["object_id"]
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield Request(url=item["website"], meta={"item": item}, callback=self.parse_store_page)

    def parse_store_page(self, response: Response) -> Iterable[Feature]:
        item = response.meta["item"]
        item["website"] = response.url  # Capture redirect destination
        if m := re.findall(r"\b\d{10}\b", " ".join(response.xpath('//span[contains(@class, "littleaddress")]/span[3]/text()').getall())):
            item["phone"] = "; ".join(m)
        item["email"] = response.xpath('//span[contains(@class, "littleaddress")]/span[4]/text()').get()
        item["opening_hours"] = OpeningHours()
        if hours_text := " ".join(response.xpath('//span[contains(@class, "bkg_orari")]/span/span//text()').getall()):
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_text, days=DAYS_IT, closed=CLOSED_IT)
        yield item
