import re

from scrapy.spiders import Rule, CrawlSpider
from scrapy.linkextractors import LinkExtractor

from locations.categories import apply_category, Categories
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
        item["name"] = response.xpath('//section//h1/text()').get()
        table = response.xpath('//div[@class="pge"]/table/tbody')
        item["phone"] = table.xpath('./tr[./th[contains(text(), "Telefon")]]/td/text()').get()
        item["street_address"] = table.xpath('./tr[./th[contains(text(), "Sídlo")]]/td/text()').getall()[0]
        item["postcode"] = table.xpath('./tr[./th[contains(text(), "Sídlo")]]/td/text()').getall()[1].split(" ")[0]
        item["city"] = table.xpath('./tr[./th[contains(text(), "Sídlo")]]/td/text()').getall()[1].split(" ", 1)[1]
        item["website"] = response.url
        matches = re.search(r"google\.maps\.LatLng\(([.\d]+),([.\d]+)\)", response.text)
        item["lat"], item["lon"] = matches.groups()
        extract_email(item, table)
        apply_category(Categories.SHOP_CHARITY, item)

        yield item
