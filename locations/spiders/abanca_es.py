from scrapy.spiders import SitemapSpider

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.structured_data_spider import StructuredDataSpider


class AbancaESSpider(SitemapSpider, StructuredDataSpider):
    name = "abanca_es"
    item_attributes = {"brand": "Abanca", "brand_wikidata": "Q9598744"}
    sitemap_urls = ["https://www.abanca.com/sitemap.xml"]
    sitemap_rules = [(r"\/es\/oficinas\/oficina\/\d+\/$", "parse_sd")]

    def post_process_item(self, item, response, ld_data):
        item["lon"], item["lat"] = response.xpath("//@data-coordinates").get().strip("[]").split(",", 1)
        item["branch"] = item.pop("name").removeprefix("Oficina ABANCA en ").removesuffix(" | ABANCA")
        apply_category(Categories.BANK, item)
        apply_yes_no(Extras.ATM, item, "Dispone de cajero automático" in response.text)

        item["website"] = response.url
        item["extras"]["website:eu"] = response.xpath('//link[@rel="alternate"][@hreflang="eu"]/@href').get()
        item["extras"]["website:es"] = response.xpath('//link[@rel="alternate"][@hreflang="es"]/@href').get()
        item["extras"]["website:gl"] = response.xpath('//link[@rel="alternate"][@hreflang="gl"]/@href').get()

        yield item
