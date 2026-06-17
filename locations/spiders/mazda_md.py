from locations.spiders.mazda_gr import MazdaGRSpider


class MazdaMDSpider(MazdaGRSpider):
    name = "mazda_md"
    api_url = "https://www.mazda.md/api/2sxc/app/auto/query/DealerListByPortalAlias/Default"
    module_id = "22362"
    tab_id = "1421"
    country = "MD"
