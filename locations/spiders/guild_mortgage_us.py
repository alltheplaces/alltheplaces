from locations.storefinders.rio_seo import RioSeoSpider


class GuildMortgageUSSpider(RioSeoSpider):
    name = "guild_mortgage_us"
    item_attributes = {"brand": "Guild Mortgage Company", "brand_wikidata": "Q122074693"}
    end_point = "https://maps-r1.guildmortgage.com"
