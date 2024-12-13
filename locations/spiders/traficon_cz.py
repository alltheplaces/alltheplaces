import scrapy

from locations.categories import Categories
from locations.hours import DAYS_CZ, OpeningHours
from locations.items import Feature


class TraficonCZSpider(scrapy.Spider):
    name = "traficon_cz"
    allowed_domains = ["www.traficon.cz"]
    start_urls = ["https://www.traficon.cz/prodejny/"]
    item_attributes = {"brand": "TRAFICON", "brand_wikidata": "Q67807570", "extras": Categories.SHOP_TOBACCO.value}

    def parse(self, response):
        for branch in response.xpath("//div[@id='jq_branchMap']//span[@class='jq_mapMarker']"):
            alert = branch.xpath(".//p[@class='m-info m-info--alert d-block']/text()").get()
            if alert is not None and ("trvale uzavřena" in alert or "ukončen" in alert or "přestěhovala" in alert):
                # permanently closed
                continue

            url = branch.xpath(".//a[starts-with(@href, '/prodejny/')]/@href").get()

            item = Feature()
            item["ref"] = url.removeprefix("/prodejny/")
            item["name"] = branch.attrib["data-title"]
            item["website"] = "https://www.traficon.cz" + url
            item["lat"] = branch.attrib["data-lat"]
            item["lon"] = branch.attrib["data-lng"]
            address = branch.xpath(".//p[1]/text()[normalize-space()]").getall()
            item["street_address"] = address[0]
            item["city"] = address[1]

            oh = OpeningHours()
            days = branch.xpath(".//p[2]/span/text()[normalize-space()]").getall()
            hours = branch.xpath(
                ".//p[2]/strong[not(contains(text(), 'Otevírací doba'))]/text()[normalize-space()]"
            ).getall()
            for day, hrs in zip(days, hours):
                oh.add_ranges_from_string(day.strip() + " " + hrs.strip(), DAYS_CZ)
            item["opening_hours"] = oh.as_opening_hours()

            yield item
