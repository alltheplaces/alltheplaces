import re
from typing import Iterable

from scrapy import Request
from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider
from twisted.python.failure import Failure

from locations.items import Feature
from locations.linked_data_parser import LinkedDataParser
from locations.spiders.ixina_fr import IxinaFRSpider
from locations.structured_data_spider import StructuredDataSpider

# Dutch is the local language in Flanders, French in Wallonia and in majority
# French-speaking Brussels. The French pages translate Flemish place names
# (Gand for Gent, Malines for Mechelen), so the Dutch page of each store is
# fetched as well and the local language wins. Both are kept as extras.
DUTCH_POSTCODES = [range(1500, 4000), range(8000, 10000)]

BRANCH_PREFIX = re.compile(r"^(?:magasin de cuisine ixina|ixina keukenwinkel)\s+", re.IGNORECASE)


class IxinaBESpider(SitemapSpider, StructuredDataSpider):
    name = "ixina_be"
    item_attributes = IxinaFRSpider.item_attributes
    sitemap_urls = ["https://ixina.be/fr/pages/sitemap.xml"]
    sitemap_rules = [
        (r"/trouvez-votre-magasin/magasin-de-cuisine-ixina-", "parse_sd"),
    ]

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable:
        self.clean_item(item)
        if nl_url := response.xpath('//link[@rel="alternate"][@hreflang="nl-BE"]/@href').get():
            yield Request(nl_url, callback=self.parse_nl, errback=self.parse_nl_error, cb_kwargs={"item": item})
        else:
            # Without its Dutch page the store is still worth keeping, in French.
            self.logger.warning("No Dutch page for %s", response.url)
            yield item

    def parse_nl_error(self, failure: Failure) -> Iterable[Feature]:
        self.logger.warning("Dutch page failed for %s", failure.request.url)
        yield failure.request.cb_kwargs["item"]

    def parse_nl(self, response: TextResponse, item: Feature) -> Iterable[Feature]:
        if (ld_data := next(self.iter_linked_data(response), None)) is None:
            self.logger.warning("No linked data on %s", response.url)
            yield item
            return

        nl_item = LinkedDataParser.parse_ld(ld_data)
        self.clean_item(nl_item)
        nl_item["website"] = response.url
        localised = {"fr": item.copy(), "nl": nl_item}

        postcode = int(item.get("postcode") or 0)
        language = "nl" if any(postcode in r for r in DUTCH_POSTCODES) else "fr"
        for field in ("branch", "city", "street_address", "website"):
            item[field] = localised[language][field]

        for code in ("fr", "nl"):
            item["extras"][f"website:{code}"] = localised[code]["website"]
            # A translation is only worth recording where it differs from the local name.
            for field, key in (
                ("branch", "branch"),
                ("city", "addr:city"),
                ("street_address", "addr:street_address"),
            ):
                if localised["fr"][field] != localised["nl"][field]:
                    item["extras"][f"{key}:{code}"] = localised[code][field]

        yield item

    @staticmethod
    def clean_item(item: Feature) -> None:
        item["branch"] = BRANCH_PREFIX.sub("", item.pop("name"))
        item["street_address"] = item["street_address"].strip()
        # Lochristi gives its town name as the postcode.
        postcode = (item.get("postcode") or "").strip()
        item["postcode"] = postcode if re.fullmatch(r"\d{4}", postcode) else None
        # A few stores carry the whole address in streetAddress, e.g. "Oscar Van Kesbeeckstraat 45\r\n2800 Mechelen".
        if not item["postcode"] and (m := re.fullmatch(r"(.+?)[,\s]+(\d{4}) (.+)", item["street_address"], re.DOTALL)):
            item["street_address"], item["postcode"], item["city"] = m.groups()
