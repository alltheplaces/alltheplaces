import re

from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class CondadoTacosUSSpider(SitemapSpider, StructuredDataSpider):
    name = "condado_tacos_us"
    item_attributes = {"brand": "Condado Tacos", "brand_wikidata": "Q118640152"}
    allowed_domains = ["locations.condadotacos.com"]
    sitemap_urls = ["https://locations.condadotacos.com/sitemap.xml"]
    sitemap_rules = [(r"https://locations.condadotacos.com\/\w\w\/[-.\w]+$", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        description = response.css("meta[name=description]").attrib["content"]
        matches = re.search(r"(Condado [^,]+),", description)
        if matches is not None:
            [name] = matches.groups()
            item["name"] = name
        item["country"] = response.css("[itemprop=addressCountry]::text").get()
        yield item
