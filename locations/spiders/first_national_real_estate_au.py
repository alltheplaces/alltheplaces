from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.items import Feature
from locations.spiders.vapestore_gb import clean_address


class FirstNationalRealEstateAUSpider(Spider):
    name = "first_national_real_estate_au"
    item_attributes = {"brand": "First National Real Estate", "brand_wikidata": "Q122888198"}
    allowed_domains = ["www.firstnational.com.au"]
    start_urls = ["https://www.firstnational.com.au/pages/real-estate/offices"]
    api_url_template = ""

    def make_request(self, page: int) -> JsonRequest:
        next_page_url = self.api_url_template.format(page)
        return JsonRequest(url=next_page_url, callback=self.parse_results_page)

    def parse(self, response):
        api_url_path = (
            response.xpath('//button[@hx-get and contains(@hx-target, "#load-offices-")]/@hx-get')
            .get()
            .replace("&pg=2", "&pg={}")
            .replace("&returnAs=markup", "")
        )
        self.api_url_template = f"https://{self.allowed_domains[0]}{api_url_path}"
        yield self.make_request(1)

    def parse_results_page(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["offices"]:
            item = Feature()
            item["ref"] = location["id"]
            item["name"] = location["office_name"]
            item["lat"] = location["latitude"]
            item["lon"] = location["longitude"]
            item["website"] = response.urljoin(location["office_link"])
            item["phone"] = location["office_phone"]
            item["email"] = location["office_email"]
            item["street_address"] = clean_address(
                [location["office_address_line_1"], location["office_address_line_2"]]
            )
            item["city"] = location["office_suburb"]
            item["postcode"] = location["office_post_code"]
            item["state"] = location["office_state"]

            yield item

        next_page = response.json()["pagination"]["offices"]["next_page"]
        if next_page != 0:
            yield self.make_request(next_page)
