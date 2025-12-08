from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class RitualsSpider(SitemapSpider, StructuredDataSpider):
    name = "rituals"
    item_attributes = {"brand": "Rituals", "brand_wikidata": "Q62874140"}
    sitemap_urls = ["https://www.rituals.com/sitemap.xml"]
    sitemap_rules = [
        (
            # Rituals has stores under their own brand, and they sell their
            # products in stores of other brands. Unfortunately their own
            # stores are not possible to detect just from the URL.
            #
            # To cut down on the number of pages that need to be visited,
            # exclude the most common other chains, since their name does
            # appear in the URL.
            r"/store-detail\?store=(?!%C3%85hlens|Akzente|Arenal|BEAUTY-%7C-ZONE|Beauty-?X|Becker|Bijenkorf|Boots"
            "|Breuninger|Cebulla|Douglas|DOUGLAS|Druni|Ed%C3%A9n|El-Corte-Ingl|[fF]armacia|FARMACIA|Fenwick|Flair"
            "|Frasers|Fredrik-%26-Louisa|Fund-Grube|Gabriel|Galeries-Lafayette|Globus|Godel|I(ci|CI)-Paris-XL|Inno"
            "|John-Lewis|Karstadt|Kaufhof|Kicks|KICKS|Kunzmann|Loeb|Lyko|Magasin-du-Nord|Manor|Marvimundo|Marionnaud"
            "|MARIONNAUD|Matas|Mooi|MOOI|Next|Nocib%C3%A9|P%26C|Parf%C3%BCmerie|Passion-Beaut|PASSION-BEAUT|Pieper"
            "|Pour-Vous|Printemps|Sabina|Schuback|Sephora|Stephan|Stockmann|Top-Parf%C3%BCmerie|Wiedemann)",
            "parse_sd",
        )
    ]

    def post_process_item(self, item, response, ld_data, **kwargs):
        item["ref"] = response.url.rsplit("=", maxsplit=1)[-1]
        item["website"] = response.url
        yield item
