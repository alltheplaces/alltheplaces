import re

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.hours import DAYS_DE, OpeningHours
from locations.items import Feature


class CombiDESpider(CrawlSpider):
    name = "combi_de"
    item_attributes = {"brand": "Combi", "brand_wikidata": "Q1113618"}

    start_urls = ["https://www.combi.de/unseremaerkte/marktsuche"]
    rules = [Rule(LinkExtractor(allow="/marktauswahl/"), follow=False, callback="parse")]

    address_pattern = r"\W*?^(\w.+\w)\W*,\W*(\d{5})\W*(\w.+\w)\W*?$"

    def parse(self, response: Response):
        address = response.xpath("//address/text()").get().strip()
        street_address, postcode, city = re.findall(self.address_pattern, address)[0]
        opening_hours = OpeningHours()
        opening_hours.add_ranges_from_string(
            response.xpath('string(//table[@class="opening-hours__table"])').get(), days=DAYS_DE
        )
        image_link = response.xpath('//img[contains(@src, "Marktbilder")]/@src').get()
        image_link = "https://www.combi.de" + image_link if image_link else None
        yield Feature(
            ref=response.url.split("/")[-1],
            website=response.url,
            street_address=street_address,
            lat=re.findall(r"var lat = Number\('(.+?)'\)", response.text, re.DOTALL)[0],
            lon=re.findall(r"var lon = Number\('(.+?)'\)", response.text, re.DOTALL)[0],
            postcode=postcode,
            city=city,
            addr_full=address,
            opening_hours=opening_hours,
            phone=response.xpath('string(//div[contains(@class, "contact__entry--phone")])')
            .get()
            .strip()
            .replace("/", ""),
            image=image_link,
        )
