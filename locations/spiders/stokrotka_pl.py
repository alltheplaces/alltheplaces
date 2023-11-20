from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class StokrotkaPLSpider(SitemapSpider, StructuredDataSpider):
    name = "stokrotka_pl"
    item_attributes = {}
    allowed_domains = ["stokrotka.pl"]
    sitemap_urls = [
        "https://stokrotka.pl/data/domains/1/sitemap/c_objects_map.xml",
    ]
    sitemap_rules = [(r"nasze-sklepy\/[a-zA-Z0-9-]+\.html", "parse_sd")]

    def post_process_item(self, item, response, ld_data, **kwargs):
        store_type = item["name"].strip()
        del item["name"]
        if "Express" in store_type:
            item["brand"] = "Stokrotka Express"
            item["brand_wikidata"] = "Q110801119"
        elif "Optima" in store_type:
            item["brand"] = "Stokrotka Optima"
            item["brand_wikidata"] = "Q110801045"
        elif "Market" in store_type or "Supermarket" in store_type:
            item["brand"] = "Stokrotka Market"
            item["brand_wikidata"] = "Q110801183"
        else:
            item["brand"] = "Stokrotka"
            item["brand_wikidata"] = "Q9345945"
        del item["image"]  # always the same url returning 404
        coords_data = response.xpath('//script[contains(text(), "lat:")]/text()').get()
        item["lat"] = coords_data.split("lat: ", 1)[1].split(",", 1)[0]
        item["lon"] = coords_data.split("lng: ", 1)[1].split(",", 1)[0]
        yield item
