from locations.spiders.mazda_gr import MazdaGRSpider


class MazdaMKSpider(MazdaGRSpider):
    name = "mazda_mk"
    api_url = "https://www.mazda.mk/api/2sxc/app/auto/query/DealerListByPortalAlias/Default"
    module_id = "22416"
    tab_id = "2406"
    country = "MK"
