import json
import re
import scrapy

from locations.items import GeojsonPointItem


brand_name_override = {
    "Comfort Suites Suites": "Comfort Suites",
    "Econo Lodge Lodge": "Econo Lodge",
}


class ChoiceHotelsSpider(scrapy.Spider):
    name = "choicehotels"
    item_attributes = {"brand": "Choice Hotels", "brand_wikidata": "Q1075788"}
    allowed_domains = ["choicehotels.com"]
    download_delay = 0.2

    base_url = "https://www.choicehotels.com/cms/pages/choice-hotels"

    start_urls = [
        "https://www.choicehotels.com/cms/pages/comfort-inn/sitemap?d=DESKTOP&applocale=en-us",
        "https://www.choicehotels.com/cms/pages/comfort-suites/sitemap?d=DESKTOP&applocale=en-u",
        "https://www.choicehotels.com/cms/pages/quality-inn/sitemap?d=DESKTOP&applocale=en-u",
        "https://www.choicehotels.com/cms/pages/sleep-inn/sitemap?d=DESKTOP&applocale=en-u",
        "https://www.choicehotels.com/cms/pages/clarion/sitemap?d=DESKTOP&applocale=en-u",
        "https://www.choicehotels.com/cms/pages/cambria/sitemap?d=DESKTOP&applocale=en-u",
        "https://www.choicehotels.com/cms/pages/mainstay/sitemap?d=DESKTOP&applocale=en-u",
        "https://www.choicehotels.com/cms/pages/suburban/sitemap?d=DESKTOP&applocale=en-u",
        "https://www.choicehotels.com/cms/pages/econo-lodge/sitemap?d=DESKTOP&applocale=en-u",
        "https://www.choicehotels.com/cms/pages/rodeway-inn/sitemap?d=DESKTOP&applocale=en-u",
    ]

    def parse_hotel(self, response):
        script = "".join(response.xpath("//script/text()").extract())
        data = json.loads(re.search(r"window.hotelInfoData = (.*)?;", script).group(1))

        if data["hotel"]["status"] == "TERMINATED":
            return

        brand = (
            data["hotel"]["general"]["brandName"]
            + " "
            + data["hotel"]["general"]["productName"]
        )

        properties = {
            "ref": data["hotel"]["id"],
            "name": data["hotel"]["name"],
            "addr_full": data["hotel"]["address"]["line1"],
            "city": data["hotel"]["address"]["city"],
            "state": data["hotel"]["address"].get("subdivision"),
            "postcode": data["hotel"]["address"].get("postalCode"),
            "country": data["hotel"]["address"]["country"],
            "phone": data["hotel"]["general"]["phone"],
            "lat": float(data["hotel"]["general"]["lat"]),
            "lon": float(data["hotel"]["general"]["lon"]),
            "website": response.url,
            "brand": brand_name_override.get(brand, brand),
        }

        yield GeojsonPointItem(**properties)

    def parse_hotel_list(self, response):
        urls = response.xpath("//p/a/@href").extract()
        if not urls:
            urls = response.xpath("//div/a/@href").extract()

        for url in urls:
            yield scrapy.Request(response.urljoin(url), callback=self.parse_hotel)

    def parse(self, response):
        urls = response.xpath(
            '//h3[contains(text(), "Locations")]/following-sibling::div//h6/a/@href'
        ).extract()

        for url in urls:
            yield scrapy.Request(self.base_url + url, callback=self.parse_hotel_list)
