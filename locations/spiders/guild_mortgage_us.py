import chompjs
from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class GuildMortgageUSSpider(SitemapSpider, StructuredDataSpider):
    name = "guild_mortgage_us"
    item_attributes = {
        "brand": "Guild Mortgage Company",
        "brand_wikidata": "Q122074693",
    }
    sitemap_urls = ["https://branches.guildmortgage.com/robots.txt"]
    sitemap_rules = [
        (r"https://branches.guildmortgage.com/\w\w/[\w-]+/[\w-]+-(\d+)(?:\.html|/)$", "parse"),
    ]
    drop_attributes = {"facebook", "image", "name"}

    def parse(self, response):
        for nextjs_script in response.xpath(
            "//script[starts-with(text(), 'self.__next_f.push([1,\"{\\\"@context')]/text()"
        ).getall():
            script_el = response.selector.root.makeelement("script", {"type": "application/ld+json"})
            script_el.text = chompjs.parse_js_object(nextjs_script)[1]
            response.selector.root.append(script_el)
        yield from super().parse(response)
