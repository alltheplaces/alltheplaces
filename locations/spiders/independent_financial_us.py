import scrapy
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature


class IndependentFinancialUSSpider(scrapy.Spider):
    name = "independent_financial_us"
    item_attributes = {"brand": "Independent Bank", "brand_wikidata": "Q6016398"}
    start_urls = ["https://www.independentbank.com/find-a-location/"]

    def parse(self, response: Response, **kwargs):
        for location in response.xpath('//*[@class="locations-listings"]//article'):
            item = Feature()
            item["branch"] = location.xpath(".//@aria-label").get()
            item["name"] = self.item_attributes["brand"]
            item["ref"] = location.xpath(".//@id").get()
            item["lat"] = location.xpath(".//@data-lat").get()
            item["lon"] = location.xpath(".//@data-lng").get()
            item["addr_full"] = location.xpath(".//@data-address").get()
            item["website"] = response.urljoin(location.xpath(".//@data-url").get())
            location_type = location.xpath('.//div[@class="location-item-services-list"]/text()').get().split()

            apply_category(Categories.BANK, item)

            apply_yes_no(Extras.ATM, item, "UseanATM" in location_type)
            apply_yes_no(Extras.DRIVE_THROUGH, item, "UsetheDriveThru" in location_type)

            yield item
