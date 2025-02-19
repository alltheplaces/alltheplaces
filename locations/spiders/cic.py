import re

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.categories import Categories, apply_category
from locations.hours import DAYS_FR, OpeningHours, sanitise_day
from locations.items import Feature


class CicSpider(CrawlSpider):
    name = "cic"
    item_attributes = {"brand_wikidata": "Q746525"}
    start_urls = ["https://www.cic.fr/fr/agences-et-distributeurs/Regions.aspx"]
    allowed_domains = ["cic.fr"]
    rules = [
        Rule(
            LinkExtractor(allow=r"/Departements\.aspx\?regionId="),
        ),
        Rule(
            LinkExtractor(allow=r"/Localites\.aspx\?regionId="),
        ),
        Rule(
            LinkExtractor(allow=r"/ResultatsRechercheGeographique\.aspx\?inseeCode="),
        ),
        Rule(
            LinkExtractor(allow=r"/fr/agence/"),
            callback="parse",
        ),
    ]

    def parse(self, response):
        item = Feature()
        item["name"] = response.xpath("//title/text()").get()
        item["website"] = item["ref"] = response.url
        item["phone"] = response.xpath('//*[@itemprop="telephone"]/text()').get()
        item["street_address"] = response.xpath('//*[@itemprop="streetAddress"]/text()').get()
        item["postcode"] = response.xpath('//*[@itemprop="postalCode"]/text()').get()
        item["city"] = response.xpath('//*[@itemprop="addressLocality"]/text()').get()
        item["lat"] = re.search(r"Data\$Value2:\s*\"(-?\d+.\d+)\",", response.text).group(1)
        item["lon"] = re.search(r"Data\$Value3:\s*\"(-?\d+.\d+)\"}", response.text).group(1)
        item["opening_hours"] = OpeningHours()
        for day_time in response.xpath('//*[@id="C:H1:D"]//tbody//tr'):
            raw_data = day_time.xpath(".//td").xpath("normalize-space()").getall()
            day = sanitise_day(raw_data[0], DAYS_FR)
            for time in raw_data[1:3]:
                if time in ["Ouvert sur RDV"]:
                    continue
                if "Fermé" in time:
                    item["opening_hours"].set_closed(day)
                else:
                    open_time, close_time = time.replace("h", ":").split(" - ")
                    item["opening_hours"].add_range(day=day, open_time=open_time, close_time=close_time)
        apply_category(Categories.BANK, item)
        yield item

