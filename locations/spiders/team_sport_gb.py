from scrapy.spiders import SitemapSpider

from locations.structured_data_spider import StructuredDataSpider


class TeamSportGBSpider(SitemapSpider, StructuredDataSpider):
    name = "team_sport_gb"
    item_attributes = {"brand": "TeamSport Go Karting", "brand_wikidata": "Q7691413"}
    sitemap_urls = ["https://www.team-sport.co.uk/robots.txt"]
    sitemap_rules = [("/go-kart-tracks/", "parse")]
    wanted_types = ["SportsActivityLocation"]
    json_parser = "chompjs"
