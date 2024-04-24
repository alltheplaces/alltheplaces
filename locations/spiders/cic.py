from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FR, OpeningHours
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class CiceSpider(CrawlSpider, StructuredDataSpider):
    name = "cic"
    item_attributes = {"brand_wikidata": "Q746525"}
    start_urls = ["https://www.cic.fr/fr/banques/entreprises/agences-et-distributeurs/BrowseSubdivision.aspx"]
    allowed_domains = ["cic.fr"]
    rules = [
        Rule(LinkExtractor(allow=r"SubdivisionId"), follow=True),
        Rule(LinkExtractor(allow=r"type=branch&loca"), follow=True),
        Rule(LinkExtractor(allow=r"/fr/agence/"), callback="parse", follow=True),
        Rule(LinkExtractor(allow=r"/fr/agences"), callback="parse", follow=True),
    ]

    def parse(self, response):
        item = Feature()
        item["website"] = response.url
        item["ref"] = response.url
        item["name"] = response.xpath('//*[@itemprop="name"]/a/text()').get()
        item["phone"] = response.xpath('//*[@itemprop="telephone"]/text()').get()
        item["street_address"] = response.xpath('//*[@itemprop="streetAddress"]/text()').get()
        item["postcode"] = response.xpath('//*[@itemprop="postalCode"]/text()').get()
        item["city"] = response.xpath('//*[@itemprop="addressLocality"]/text()').get()
        item["lat"] = response.xpath('//*[@itemprop="latitude"]/@content').get()
        item["lon"] = response.xpath('//*[@itemprop="longitude"]/@content').get()

        oh = OpeningHours()
        for day in response.xpath("//tbody/tr[@class]"):
            if day.xpath("./td[1]/text()").get().strip() == "Fermé":
                continue
            halfday = day.xpath("./td[2]/text()").get()
            for i in range(1, 3 if halfday and halfday.strip() != "Fermé" else 2):
                oh.add_range(
                    day=DAYS_FR[day.xpath("./th/text()").get().strip()[:2]],
                    open_time=day.xpath(f"./td[{i}]/text()").get().strip().replace("h", ":").split("-")[0],
                    close_time=day.xpath(f"./td[{i}]/text()").get().strip().replace("h", ":").split("-")[1],
                )
        item["opening_hours"] = oh.as_opening_hours()
        apply_category(Categories.BANK, item)

        yield item
