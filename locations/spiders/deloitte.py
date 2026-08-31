from typing import Any, Iterable

from scrapy.http import TextResponse
from scrapy.spiders import SitemapSpider

from locations.google_url import extract_google_position
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class DeloitteSpider(SitemapSpider, StructuredDataSpider):
    name = "deloitte"
    item_attributes = {"brand": "Deloitte", "brand_wikidata": "Q491748"}
    allowed_domains = ["deloitte.com"]
    sitemap_urls = [
        "https://www.deloitte.com/sitemap_index.xml",
    ]
    sitemap_rules = [(r"/offices/[^/]+/[^/]+\.html$", "parse_sd")]

    def sitemap_filter(self, entries: Iterable[dict[str, Any]]) -> Iterable[dict[str, Any]]:
        for entry in entries:
            for sitemap_url in [
                "tr_tr",
                "global_en",
                "nl_nl",
                "ch_de",
                "ch_fr",
                "ro_ro",
                "hu_hu",
                "cz-sk_sk",
                "cz-sk_cs",
                "az_az",
                "ca_fr",
                "kz_ru",
                "il_he",
                "cn_zh",
                "tw_tc",
            ]:
                if sitemap_url in entry:
                    continue
                else:
                    yield entry

    def post_process_item(self, item: Feature, response: TextResponse, ld_data: dict, **kwargs) -> Iterable[Feature]:
        if ld_data.get("address").get("streetAddress"):
            item["website"] = response.url
            try:
                if not ld_data.get("geo"):
                    extract_google_position(item, response)
            except:
                pass
            yield item
