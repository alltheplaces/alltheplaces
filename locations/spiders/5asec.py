import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature


class FiveAsecSpider(SitemapSpider):
    name = "5asec"
    item_attributes = {"brand": "5àsec", "brand_wikidata": "Q2817899"}
    sitemap_urls = ["https://www.5asec.fr/sitemap.xml"]
    sitemap_rules = [(r"fr/fr/trouvez-votre-pressing-5asec/[^/]+/[^/]+/([^/]+)$", "parse")]
    skip_auto_cc_domain = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        item = Feature()
        item["ref"] = item["website"] = response.url

        item["street_address"] = response.xpath(
            '//div[contains(@class, "field-name-field-address ")]/div/div/text()'
        ).get()
        item["city"] = response.xpath('//div[contains(@class, "field-name-field-city")]/div/div/text()').get()
        item["phone"] = response.xpath('//div[contains(@class, "field-name-field-phone")]/div/div/text()').get()

        if m := re.search(r"var geofield_lat = '(-?\d+\.\d+)';", response.text):
            item["lat"] = m.group(1)
        if m := re.search(r"var geofield_lon = '(-?\d+\.\d+)';", response.text):
            item["lon"] = m.group(1)

        yield item
