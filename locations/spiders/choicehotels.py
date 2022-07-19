import json
import re
from locations.items import GeojsonPointItem
from scrapy.spiders import SitemapSpider


class ChoiceHotelsSpider(SitemapSpider):
    name = "choicehotels"
    item_attributes = {"brand": "Choice Hotels", "brand_wikidata": "Q1075788"}
    allowed_domains = ["choicehotels.com"]
    download_delay = 0.2
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"
    sitemap_urls = [
        "https://www.choicehotels.com/propertysitemap.xml",
    ]

    def parse(self, response):
        script = "".join(response.xpath("//script/text()").extract())
        data = json.loads(
            re.search(r"window.PRELOADED_STATE = (.*)?;", script).group(1)
        )["page"]

        # Remove unused extra bits to get to the random key with the useful stuff in it
        data.pop("referrerState", None)
        data.pop("screenParams", None)
        data.pop("hasUserScrolled", None)
        data.pop("ready", None)
        data = list(data.values())[0]

        if "property" not in data:
            return

        properties = {
            "ref": data["property"]["id"],
            "name": data["property"]["name"],
            "addr_full": data["property"]["address"]["line1"],
            "city": data["property"]["address"]["city"],
            "state": data["property"]["address"].get("subdivision"),
            "postcode": data["property"]["address"].get("postalCode"),
            "country": data["property"]["address"]["country"],
            "phone": data["property"]["phone"],
            "lat": data["property"]["lat"],
            "lon": data["property"]["lon"],
            "website": response.url,
            "brand": " ".join(
                [data["property"]["brandName"], data["property"]["productName"]]
            ),
        }

        yield GeojsonPointItem(**properties)
