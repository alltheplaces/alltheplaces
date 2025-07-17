from typing import Any, Iterable

from scrapy import FormRequest, Selector, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import clean_address


class FultonBankUSSpider(Spider):
    name = "fulton_bank_us"
    item_attributes = {"brand": "Fulton Bank", "brand_wikidata": "Q16976594"}

    def start_requests(self) -> Iterable[FormRequest]:
        yield FormRequest(
            url="https://www.fultonbank.com/api/Branches/Search",
            formdata={
                "QueryModel.SearchTerm": "kansas",
                "QueryModel.Radius": "5000",
            },  # center location with search radius
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        branch_popups = Selector(text=response.json()["branchFlyouts"])  # contains extra info

        for location in Selector(text=response.json()["branchResults"]).xpath("//*[@data-lat]"):
            item = Feature()
            item["ref"] = location.xpath("./@data-id").get()
            item["lat"] = location.xpath("./@data-lat").get()
            item["lon"] = location.xpath("./@data-long").get()
            item["branch"] = location.xpath("./@data-name").get()
            item["addr_full"] = clean_address(location.xpath('.//*[@class="location-address"]/text()').get(""))

            # Use data-id to extract phone, opening hours etc. from branch_popups
            location_details = branch_popups.xpath(f'.//*[@data-id="{item["ref"]}"]')
            item["phone"] = location_details.xpath('.//a[contains(@href, "tel:")]/@href').get()
            apply_category(Categories.BANK, item)
            yield item
