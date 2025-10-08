import re

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import extract_email


class CervenyKrizCZSpider(CrawlSpider):
    name = "cerveny_kriz_cz"
    item_attributes = {"brand_wikidata": "Q4515418", "brand": "Český červený kříž"}
    allowed_domains = ["www.cervenykriz.eu"]
    start_urls = ["https://www.cervenykriz.eu/kde-pusobime"]
    rules = [Rule(LinkExtractor(allow=r"\/oblastnispolky\/\d+\/[-\w]+$"), callback="parse")]

    def parse(self, response, **kwargs):
        item = Feature()
        item["ref"] = response.url.split("/")[-2]
        item["name"] = response.xpath("//section//h1/text()").get()
        table = response.xpath('//div[@class="pge"]/table/tbody')
        item["phone"] = table.xpath('./tr[./th[contains(text(), "Telefon")]]/td/text()').get()
        item["street_address"] = table.xpath('./tr[./th[contains(text(), "Sídlo")]]/td/text()').getall()[0]
        line2 = table.xpath('./tr[./th[contains(text(), "Sídlo")]]/td/text()').getall()[1]
        item["postcode"], item["city"] = re.search(r"([\d\s]{5,})\s(.+)", line2).groups()
        item["website"] = table.xpath('./tr[./th[contains(text(), "Web")]]/td/a/@href').get() or response.url
        if not item["website"].startswith("http"):
            item["website"] = "https://" + item["website"]
        item["lat"], item["lon"] = re.search(r"google\.maps\.LatLng\(([.\d]+),([.\d]+)\)", response.text).groups()
        extract_email(item, table)
        apply_category(Categories.SOCIAL_FACILITY, item)

        yield item
