from typing import Any

from scrapy import FormRequest
from scrapy.exceptions import CloseSpider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address
from locations.structured_data_spider import StructuredDataSpider
from locations.user_agents import BROWSER_DEFAULT


class MyDentistGBSpider(StructuredDataSpider):
    MYDENTIST = {"brand": "My Dentist", "brand_wikidata": "Q65118035"}
    name = "my_dentist_gb"
    allowed_domains = ["mydentist.co.uk"]
    start_urls = ["https://www.mydentist.co.uk/practice-directory"]
    custom_settings = {
        "USER_AGENT": BROWSER_DEFAULT,
        "CONCURRENT_REQUESTS": 1,
        "DOWNLOAD_DELAY": 3,
        "DOWNLOAD_TIMEOUT": 180,
        "RETRY_TIMES": 5,
    }
    seen_refs = set()
    total_count = 0

    def make_request(self, page: int) -> FormRequest:
        return FormRequest(
            url="https://www.mydentist.co.uk/Workflow/PracticeList/_SearchResult",
            formdata={
                "searchData": "",
                "searchName": "",
                "widgetName": "Default",
                "page": str(page),
                "ItemsPerPage": "Default",
                "searchOption": "",
            },
            cb_kwargs=dict(page=page),
            callback=self.parse_locations,
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        # Find the total_count
        self.total_count = len(response.xpath('//*[@class="practice-list"]/li').getall())

        # We'll use the total_count value later, to stop making requests to POST API which keeps on responding
        yield self.make_request(1)

    def parse_locations(self, response: Response, **kwargs: Any) -> Any:
        for location in response.xpath('//*[@class="practice-details-container"]'):
            url = location.xpath('.//*[contains(@class, "practice-name")]//a/@href').get("")
            # Collect coordinates, not present on the location page
            location_info = {
                "ref": url.split("pid=")[1],
                "lat": location.xpath(".//@data-latitude").get(),
                "lon": location.xpath(".//@data-longitude").get(),
            }
            self.seen_refs.add(location_info["ref"])

            # Fetch more location details like address, opening hours etc. from  the location page
            yield response.follow(url, callback=self.parse_sd, meta=dict(location_info=location_info))

        if len(self.seen_refs) == self.total_count:
            raise CloseSpider()
        else:
            yield self.make_request(kwargs["page"] + 1)

    def pre_process_data(self, ld_data: dict, **kwargs):
        if isinstance(ld_data["address"], list):
            ld_data["openingHours"] = ld_data["address"][-1].pop("openingHours", None)

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item.update(response.meta["location_info"])
        item["website"] = response.url
        item["addr_full"] = clean_address(response.xpath('//*[@itemprop="address"]//p/text()').get(""))
        if item["name"].startswith("mydentist") or item["name"].startswith("{my}dentist"):
            item.update(self.MYDENTIST)
            item["name"] = "{my}dentist"
        apply_category(Categories.DENTIST, item)
        yield item
