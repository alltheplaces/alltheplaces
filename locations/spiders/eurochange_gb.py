from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class EurochangeGBSpider(SitemapSpider, StructuredDataSpider):
    name = "eurochange_gb"
    EUROCHANGE = {"brand": "Eurochange", "brand_wikidata": "Q86525249"}
    NM_MONEY = {"brand": "NM Money", "brand_wikidata": "Q86529747"}
    item_attributes = EUROCHANGE
    allowed_domains = ["www.eurochange.co.uk"]
    sitemap_urls = ["https://www.eurochange.co.uk/sitemap.xml"]
    sitemap_rules = [(r"https:\/\/www\.eurochange\.co\.uk\/branches\/([\w-]+\/[\w-]+)$", "parse_sd")]
    wanted_types = ["Store"]
    time_format = "%H.%M"
    requires_proxy = True

    def post_process_item(self, item, response, ld_data, **kwargs):
        if item.get("facebook") == "https://www.facebook.com/eurochange/":
            item["facebook"] = None
        if item.get("image") == "https://www.eurochange.co.uk/assets/img/logo.svg":
            item["image"] = None
        if "NM Money" in item["name"]:
            item.update(self.NM_MONEY)
            item["website"] = item["website"].replace("eurochange.co.uk", "nmmoney.co.uk")
        yield item
