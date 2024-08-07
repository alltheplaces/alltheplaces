#!/usr/bin/env bash

if ! command -v unzip &> /dev/null
then
    echo "unzip could not be found"
    exit 1
fi


if ! command -v ogr2ogr &> /dev/null
then
    echo "ogr2ogr could not be found. You may want to add the gdal-bin and libgdal-dev package"
    exit 1
fi

if ! command -v dggrid &> /dev/null
then
    echo "dggrid could not be found. See https://github.com/alltheplaces/alltheplaces/blob/master/locations/searchable_points/earth_centroids_iseadgg.md?plain=1"
    exit 1
fi

# Retrieve data, only if not available
if [ ! -f ne_10m_admin_0_countries_lakes.zip ]; then
    curl 'https://naciscdn.org/naturalearth/10m/cultural/ne_10m_admin_0_countries_lakes.zip' \
    -H 'accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7' \
    -H 'accept-language: en-GB,en;q=0.9,en-US;q=0.8,de;q=0.7,es;q=0.6,fr;q=0.5' \
    -H 'dnt: 1' \
    -H 'priority: u=0, i' \
    -H 'referer: https://www.naturalearthdata.com/' \
    -H 'sec-ch-ua: "Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"' \
    -H 'sec-ch-ua-mobile: ?0' \
    -H 'sec-ch-ua-platform: "Windows"' \
    -H 'sec-fetch-dest: document' \
    -H 'sec-fetch-mode: navigate' \
    -H 'sec-fetch-site: cross-site' \
    -H 'sec-fetch-user: ?1' \
    -H 'sec-gpc: 1' \
    -H 'upgrade-insecure-requests: 1' \
    -H 'user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36' > ne_10m_admin_0_countries_lakes.zip
fi

unzip -n ne_10m_admin_0_countries_lakes.zip

if [ ! -f ad.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='AD'" ad.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f ae.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='AE'" ae.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f af.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='AF'" af.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f ag.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='AG'" ag.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f ai.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='AI'" ai.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f al.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='AL'" al.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f am.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='AM'" am.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f ao.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='AO'" ao.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f aq.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='AQ'" aq.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f ar.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='AR'" ar.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f as.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='AS'" as.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f at.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='AT'" at.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f au.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='AU'" au.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f aw.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='AW'" aw.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f ax.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='AX'" ax.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f az.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='AZ'" az.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f ba.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='BA'" ba.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f bb.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='BB'" bb.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f bd.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='BD'" bd.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f be.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='BE'" be.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f bf.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='BF'" bf.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f bg.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='BG'" bg.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f bh.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='BH'" bh.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f bi.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='BI'" bi.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f bj.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='BJ'" bj.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f bl.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='BL'" bl.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f bm.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='BM'" bm.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f bn.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='BN'" bn.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f bo.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='BO'" bo.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f bq.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='BQ'" bq.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f br.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='BR'" br.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f bs.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='BS'" bs.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f bt.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='BT'" bt.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f bv.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='BV'" bv.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f bw.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='BW'" bw.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f by.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='BY'" by.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f bz.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='BZ'" bz.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f ca.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='CA'" ca.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f cc.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='CC'" cc.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f cd.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='CD'" cd.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f cf.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='CF'" cf.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f cg.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='CG'" cg.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f ch.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='CH'" ch.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f ci.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='CI'" ci.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f ck.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='CK'" ck.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f cl.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='CL'" cl.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f cm.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='CM'" cm.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f cn.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='CN'" cn.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f co.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='CO'" co.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f cr.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='CR'" cr.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f cu.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='CU'" cu.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f cv.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='CV'" cv.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f cw.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='CW'" cw.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f cx.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='CX'" cx.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f cy.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='CY'" cy.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f cz.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='CZ'" cz.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f de.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='DE'" de.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f dj.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='DJ'" dj.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f dk.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='DK'" dk.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f dm.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='DM'" dm.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f do.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='DO'" do.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f dz.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='DZ'" dz.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f ec.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='EC'" ec.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f ee.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='EE'" ee.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f eg.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='EG'" eg.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f eh.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='EH'" eh.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f er.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='ER'" er.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f es.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='ES'" es.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f et.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='ET'" et.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f fi.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='FI'" fi.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f fj.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='FJ'" fj.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f fk.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='FK'" fk.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f fm.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='FM'" fm.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f fo.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='FO'" fo.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f fr.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='FR'" fr.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f ga.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='GA'" ga.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f gb.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='GB'" gb.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f gd.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='GD'" gd.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f ge.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='GE'" ge.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f gf.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='GF'" gf.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f gg.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='GG'" gg.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f gh.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='GH'" gh.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f gi.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='GI'" gi.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f gl.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='GL'" gl.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f gm.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='GM'" gm.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f gn.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='GN'" gn.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f gp.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='GP'" gp.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f gq.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='GQ'" gq.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f gr.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='GR'" gr.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f gs.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='GS'" gs.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f gt.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='GT'" gt.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f gu.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='GU'" gu.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f gw.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='GW'" gw.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f gy.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='GY'" gy.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f hk.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='HK'" hk.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f hm.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='HM'" hm.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f hn.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='HN'" hn.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f hr.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='HR'" hr.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f ht.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='HT'" ht.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f hu.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='HU'" hu.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f id.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='ID'" id.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f ie.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='IE'" ie.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f il.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='IL'" il.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f im.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='IM'" im.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f in.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='IN'" in.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f io.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='IO'" io.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f iq.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='IQ'" iq.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f ir.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='IR'" ir.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f is.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='IS'" is.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f it.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='IT'" it.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f je.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='JE'" je.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f jm.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='JM'" jm.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f jo.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='JO'" jo.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f jp.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='JP'" jp.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f ke.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='KE'" ke.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f kg.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='KG'" kg.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f kh.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='KH'" kh.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f ki.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='KI'" ki.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f km.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='KM'" km.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f kn.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='KN'" kn.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f kp.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='KP'" kp.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f kr.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='KR'" kr.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f kw.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='KW'" kw.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f ky.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='KY'" ky.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f kz.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='KZ'" kz.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f la.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='LA'" la.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f lb.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='LB'" lb.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f lc.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='LC'" lc.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f li.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='LI'" li.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f lk.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='LK'" lk.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f lr.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='LR'" lr.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f ls.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='LS'" ls.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f lt.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='LT'" lt.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f lu.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='LU'" lu.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f lv.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='LV'" lv.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f ly.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='LY'" ly.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f ma.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='MA'" ma.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f mc.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='MC'" mc.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f md.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='MD'" md.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f me.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='ME'" me.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f mf.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='MF'" mf.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f mg.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='MG'" mg.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f mh.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='MH'" mh.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f mk.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='MK'" mk.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f ml.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='ML'" ml.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f mm.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='MM'" mm.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f mn.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='MN'" mn.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f mo.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='MO'" mo.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f mp.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='MP'" mp.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f mq.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='MQ'" mq.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f mr.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='MR'" mr.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f ms.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='MS'" ms.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f mt.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='MT'" mt.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f mu.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='MU'" mu.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f mv.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='MV'" mv.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f mw.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='MW'" mw.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f mx.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='MX'" mx.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f my.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='MY'" my.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f mz.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='MZ'" mz.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f na.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='NA'" na.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f nc.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='NC'" nc.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f ne.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='NE'" ne.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f nf.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='NF'" nf.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f ng.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='NG'" ng.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f ni.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='NI'" ni.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f nl.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='NL'" nl.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f no.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='NO'" no.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f np.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='NP'" np.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f nr.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='NR'" nr.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f nu.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='NU'" nu.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f nz.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='NZ'" nz.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f om.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='OM'" om.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f pa.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='PA'" pa.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f pe.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='PE'" pe.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f pf.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='PF'" pf.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f pg.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='PG'" pg.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f ph.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='PH'" ph.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f pk.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='PK'" pk.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f pl.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='PL'" pl.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f pm.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='PM'" pm.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f pn.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='PN'" pn.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f pr.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='PR'" pr.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f ps.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='PS'" ps.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f pt.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='PT'" pt.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f pw.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='PW'" pw.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f py.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='PY'" py.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f qa.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='QA'" qa.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f re.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='RE'" re.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f ro.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='RO'" ro.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f rs.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='RS'" rs.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f ru.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='RU'" ru.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f rw.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='RW'" rw.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f sa.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='SA'" sa.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f sb.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='SB'" sb.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f sc.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='SC'" sc.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f sd.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='SD'" sd.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f se.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='SE'" se.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f sg.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='SG'" sg.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f sh.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='SH'" sh.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f si.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='SI'" si.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f sj.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='SJ'" sj.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f sk.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='SK'" sk.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f sl.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='SL'" sl.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f sm.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='SM'" sm.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f sn.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='SN'" sn.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f so.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='SO'" so.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f sr.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='SR'" sr.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f ss.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='SS'" ss.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f st.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='ST'" st.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f sv.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='SV'" sv.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f sx.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='SX'" sx.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f sy.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='SY'" sy.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f sz.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='SZ'" sz.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f tc.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='TC'" tc.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f td.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='TD'" td.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f tf.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='TF'" tf.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f tg.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='TG'" tg.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f th.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='TH'" th.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f tj.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='TJ'" tj.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f tk.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='TK'" tk.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f tl.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='TL'" tl.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f tm.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='TM'" tm.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f tn.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='TN'" tn.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f to.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='TO'" to.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f tr.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='TR'" tr.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f tt.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='TT'" tt.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f tv.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='TV'" tv.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f tw.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='TW'" tw.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f tz.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='TZ'" tz.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f ua.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='UA'" ua.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f ug.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='UG'" ug.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f um.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='UM'" um.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f us.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='US'" us.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f uy.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='UY'" uy.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f uz.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='UZ'" uz.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f va.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='VA'" va.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f vc.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='VC'" vc.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f ve.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='VE'" ve.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f vg.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='VG'" vg.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f vi.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='VI'" vi.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f vn.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='VN'" vn.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f vu.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='VU'" vu.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f wf.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='WF'" wf.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f ws.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='WS'" ws.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f ye.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='YE'" ye.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f yt.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='YT'" yt.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f za.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='ZA'" za.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f zm.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='ZM'" zm.shp ne_10m_admin_0_countries_lakes.shp
fi

if [ ! -f zw.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='ZW'" zw.shp ne_10m_admin_0_countries_lakes.shp
fi


echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ad_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ad.shp" > ad_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ae_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ae.shp" > ae_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name af_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files af.shp" > af_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ag_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ag.shp" > ag_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ai_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ai.shp" > ai_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name al_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files al.shp" > al_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name am_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files am.shp" > am_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ao_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ao.shp" > ao_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name aq_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files aq.shp" > aq_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ar_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ar.shp" > ar_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name as_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files as.shp" > as_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name at_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files at.shp" > at_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name au_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files au.shp" > au_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name aw_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files aw.shp" > aw_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ax_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ax.shp" > ax_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name az_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files az.shp" > az_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ba_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ba.shp" > ba_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name bb_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files bb.shp" > bb_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name bd_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files bd.shp" > bd_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name be_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files be.shp" > be_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name bf_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files bf.shp" > bf_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name bg_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files bg.shp" > bg_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name bh_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files bh.shp" > bh_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name bi_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files bi.shp" > bi_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name bj_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files bj.shp" > bj_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name bl_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files bl.shp" > bl_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name bm_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files bm.shp" > bm_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name bn_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files bn.shp" > bn_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name bo_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files bo.shp" > bo_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name bq_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files bq.shp" > bq_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name br_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files br.shp" > br_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name bs_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files bs.shp" > bs_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name bt_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files bt.shp" > bt_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name bv_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files bv.shp" > bv_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name bw_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files bw.shp" > bw_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name by_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files by.shp" > by_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name bz_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files bz.shp" > bz_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ca_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ca.shp" > ca_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name cc_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files cc.shp" > cc_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name cd_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files cd.shp" > cd_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name cf_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files cf.shp" > cf_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name cg_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files cg.shp" > cg_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ch_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ch.shp" > ch_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ci_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ci.shp" > ci_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ck_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ck.shp" > ck_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name cl_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files cl.shp" > cl_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name cm_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files cm.shp" > cm_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name cn_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files cn.shp" > cn_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name co_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files co.shp" > co_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name cr_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files cr.shp" > cr_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name cu_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files cu.shp" > cu_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name cv_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files cv.shp" > cv_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name cw_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files cw.shp" > cw_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name cx_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files cx.shp" > cx_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name cy_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files cy.shp" > cy_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name cz_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files cz.shp" > cz_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name de_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files de.shp" > de_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name dj_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files dj.shp" > dj_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name dk_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files dk.shp" > dk_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name dm_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files dm.shp" > dm_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name do_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files do.shp" > do_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name dz_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files dz.shp" > dz_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ec_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ec.shp" > ec_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ee_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ee.shp" > ee_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name eg_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files eg.shp" > eg_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name eh_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files eh.shp" > eh_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name er_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files er.shp" > er_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name es_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files es.shp" > es_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name et_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files et.shp" > et_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name fi_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files fi.shp" > fi_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name fj_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files fj.shp" > fj_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name fk_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files fk.shp" > fk_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name fm_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files fm.shp" > fm_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name fo_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files fo.shp" > fo_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name fr_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files fr.shp" > fr_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ga_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ga.shp" > ga_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name gb_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files gb.shp" > gb_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name gd_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files gd.shp" > gd_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ge_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ge.shp" > ge_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name gf_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files gf.shp" > gf_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name gg_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files gg.shp" > gg_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name gh_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files gh.shp" > gh_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name gi_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files gi.shp" > gi_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name gl_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files gl.shp" > gl_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name gm_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files gm.shp" > gm_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name gn_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files gn.shp" > gn_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name gp_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files gp.shp" > gp_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name gq_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files gq.shp" > gq_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name gr_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files gr.shp" > gr_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name gs_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files gs.shp" > gs_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name gt_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files gt.shp" > gt_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name gu_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files gu.shp" > gu_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name gw_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files gw.shp" > gw_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name gy_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files gy.shp" > gy_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name hk_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files hk.shp" > hk_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name hm_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files hm.shp" > hm_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name hn_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files hn.shp" > hn_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name hr_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files hr.shp" > hr_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ht_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ht.shp" > ht_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name hu_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files hu.shp" > hu_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name id_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files id.shp" > id_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ie_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ie.shp" > ie_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name il_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files il.shp" > il_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name im_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files im.shp" > im_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name in_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files in.shp" > in_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name io_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files io.shp" > io_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name iq_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files iq.shp" > iq_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ir_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ir.shp" > ir_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name is_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files is.shp" > is_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name it_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files it.shp" > it_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name je_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files je.shp" > je_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name jm_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files jm.shp" > jm_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name jo_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files jo.shp" > jo_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name jp_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files jp.shp" > jp_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ke_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ke.shp" > ke_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name kg_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files kg.shp" > kg_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name kh_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files kh.shp" > kh_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ki_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ki.shp" > ki_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name km_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files km.shp" > km_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name kn_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files kn.shp" > kn_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name kp_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files kp.shp" > kp_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name kr_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files kr.shp" > kr_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name kw_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files kw.shp" > kw_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ky_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ky.shp" > ky_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name kz_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files kz.shp" > kz_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name la_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files la.shp" > la_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name lb_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files lb.shp" > lb_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name lc_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files lc.shp" > lc_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name li_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files li.shp" > li_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name lk_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files lk.shp" > lk_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name lr_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files lr.shp" > lr_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ls_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ls.shp" > ls_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name lt_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files lt.shp" > lt_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name lu_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files lu.shp" > lu_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name lv_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files lv.shp" > lv_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ly_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ly.shp" > ly_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ma_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ma.shp" > ma_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name mc_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files mc.shp" > mc_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name md_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files md.shp" > md_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name me_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files me.shp" > me_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name mf_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files mf.shp" > mf_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name mg_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files mg.shp" > mg_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name mh_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files mh.shp" > mh_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name mk_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files mk.shp" > mk_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ml_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ml.shp" > ml_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name mm_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files mm.shp" > mm_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name mn_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files mn.shp" > mn_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name mo_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files mo.shp" > mo_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name mp_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files mp.shp" > mp_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name mq_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files mq.shp" > mq_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name mr_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files mr.shp" > mr_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ms_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ms.shp" > ms_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name mt_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files mt.shp" > mt_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name mu_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files mu.shp" > mu_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name mv_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files mv.shp" > mv_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name mw_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files mw.shp" > mw_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name mx_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files mx.shp" > mx_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name my_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files my.shp" > my_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name mz_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files mz.shp" > mz_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name na_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files na.shp" > na_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name nc_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files nc.shp" > nc_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ne_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ne.shp" > ne_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name nf_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files nf.shp" > nf_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ng_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ng.shp" > ng_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ni_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ni.shp" > ni_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name nl_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files nl.shp" > nl_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name no_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files no.shp" > no_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name np_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files np.shp" > np_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name nr_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files nr.shp" > nr_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name nu_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files nu.shp" > nu_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name nz_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files nz.shp" > nz_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name om_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files om.shp" > om_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name pa_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files pa.shp" > pa_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name pe_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files pe.shp" > pe_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name pf_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files pf.shp" > pf_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name pg_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files pg.shp" > pg_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ph_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ph.shp" > ph_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name pk_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files pk.shp" > pk_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name pl_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files pl.shp" > pl_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name pm_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files pm.shp" > pm_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name pn_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files pn.shp" > pn_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name pr_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files pr.shp" > pr_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ps_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ps.shp" > ps_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name pt_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files pt.shp" > pt_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name pw_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files pw.shp" > pw_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name py_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files py.shp" > py_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name qa_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files qa.shp" > qa_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name re_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files re.shp" > re_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ro_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ro.shp" > ro_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name rs_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files rs.shp" > rs_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ru_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ru.shp" > ru_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name rw_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files rw.shp" > rw_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name sa_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files sa.shp" > sa_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name sb_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files sb.shp" > sb_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name sc_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files sc.shp" > sc_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name sd_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files sd.shp" > sd_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name se_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files se.shp" > se_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name sg_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files sg.shp" > sg_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name sh_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files sh.shp" > sh_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name si_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files si.shp" > si_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name sj_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files sj.shp" > sj_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name sk_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files sk.shp" > sk_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name sl_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files sl.shp" > sl_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name sm_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files sm.shp" > sm_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name sn_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files sn.shp" > sn_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name so_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files so.shp" > so_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name sr_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files sr.shp" > sr_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ss_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ss.shp" > ss_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name st_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files st.shp" > st_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name sv_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files sv.shp" > sv_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name sx_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files sx.shp" > sx_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name sy_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files sy.shp" > sy_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name sz_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files sz.shp" > sz_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name tc_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files tc.shp" > tc_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name td_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files td.shp" > td_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name tf_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files tf.shp" > tf_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name tg_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files tg.shp" > tg_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name th_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files th.shp" > th_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name tj_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files tj.shp" > tj_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name tk_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files tk.shp" > tk_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name tl_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files tl.shp" > tl_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name tm_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files tm.shp" > tm_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name tn_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files tn.shp" > tn_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name to_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files to.shp" > to_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name tr_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files tr.shp" > tr_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name tt_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files tt.shp" > tt_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name tv_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files tv.shp" > tv_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name tw_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files tw.shp" > tw_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name tz_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files tz.shp" > tz_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ua_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ua.shp" > ua_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ug_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ug.shp" > ug_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name um_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files um.shp" > um_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name us_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files us.shp" > us_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name uy_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files uy.shp" > uy_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name uz_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files uz.shp" > uz_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name va_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files va.shp" > va_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name vc_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files vc.shp" > vc_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ve_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ve.shp" > ve_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name vg_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files vg.shp" > vg_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name vi_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files vi.shp" > vi_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name vn_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files vn.shp" > vn_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name vu_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files vu.shp" > vu_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name wf_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files wf.shp" > wf_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ws_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ws.shp" > ws_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ye_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ye.shp" > ye_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name yt_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files yt.shp" > yt_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name za_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files za.shp" > za_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name zm_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files zm.shp" > zm_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name zw_iseagg_20km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files zw.shp" > zw_iseagg_20km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ad_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ad.shp" > ad_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ae_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ae.shp" > ae_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name af_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files af.shp" > af_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ag_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ag.shp" > ag_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ai_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ai.shp" > ai_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name al_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files al.shp" > al_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name am_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files am.shp" > am_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ao_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ao.shp" > ao_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name aq_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files aq.shp" > aq_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ar_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ar.shp" > ar_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name as_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files as.shp" > as_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name at_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files at.shp" > at_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name au_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files au.shp" > au_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name aw_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files aw.shp" > aw_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ax_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ax.shp" > ax_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name az_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files az.shp" > az_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ba_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ba.shp" > ba_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name bb_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files bb.shp" > bb_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name bd_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files bd.shp" > bd_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name be_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files be.shp" > be_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name bf_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files bf.shp" > bf_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name bg_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files bg.shp" > bg_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name bh_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files bh.shp" > bh_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name bi_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files bi.shp" > bi_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name bj_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files bj.shp" > bj_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name bl_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files bl.shp" > bl_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name bm_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files bm.shp" > bm_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name bn_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files bn.shp" > bn_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name bo_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files bo.shp" > bo_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name bq_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files bq.shp" > bq_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name br_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files br.shp" > br_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name bs_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files bs.shp" > bs_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name bt_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files bt.shp" > bt_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name bv_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files bv.shp" > bv_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name bw_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files bw.shp" > bw_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name by_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files by.shp" > by_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name bz_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files bz.shp" > bz_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ca_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ca.shp" > ca_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name cc_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files cc.shp" > cc_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name cd_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files cd.shp" > cd_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name cf_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files cf.shp" > cf_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name cg_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files cg.shp" > cg_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ch_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ch.shp" > ch_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ci_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ci.shp" > ci_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ck_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ck.shp" > ck_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name cl_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files cl.shp" > cl_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name cm_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files cm.shp" > cm_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name cn_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files cn.shp" > cn_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name co_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files co.shp" > co_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name cr_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files cr.shp" > cr_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name cu_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files cu.shp" > cu_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name cv_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files cv.shp" > cv_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name cw_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files cw.shp" > cw_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name cx_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files cx.shp" > cx_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name cy_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files cy.shp" > cy_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name cz_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files cz.shp" > cz_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name de_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files de.shp" > de_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name dj_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files dj.shp" > dj_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name dk_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files dk.shp" > dk_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name dm_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files dm.shp" > dm_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name do_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files do.shp" > do_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name dz_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files dz.shp" > dz_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ec_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ec.shp" > ec_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ee_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ee.shp" > ee_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name eg_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files eg.shp" > eg_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name eh_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files eh.shp" > eh_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name er_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files er.shp" > er_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name es_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files es.shp" > es_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name et_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files et.shp" > et_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name fi_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files fi.shp" > fi_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name fj_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files fj.shp" > fj_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name fk_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files fk.shp" > fk_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name fm_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files fm.shp" > fm_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name fo_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files fo.shp" > fo_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name fr_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files fr.shp" > fr_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ga_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ga.shp" > ga_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name gb_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files gb.shp" > gb_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name gd_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files gd.shp" > gd_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ge_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ge.shp" > ge_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name gf_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files gf.shp" > gf_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name gg_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files gg.shp" > gg_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name gh_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files gh.shp" > gh_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name gi_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files gi.shp" > gi_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name gl_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files gl.shp" > gl_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name gm_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files gm.shp" > gm_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name gn_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files gn.shp" > gn_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name gp_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files gp.shp" > gp_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name gq_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files gq.shp" > gq_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name gr_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files gr.shp" > gr_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name gs_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files gs.shp" > gs_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name gt_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files gt.shp" > gt_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name gu_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files gu.shp" > gu_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name gw_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files gw.shp" > gw_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name gy_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files gy.shp" > gy_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name hk_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files hk.shp" > hk_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name hm_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files hm.shp" > hm_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name hn_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files hn.shp" > hn_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name hr_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files hr.shp" > hr_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ht_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ht.shp" > ht_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name hu_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files hu.shp" > hu_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name id_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files id.shp" > id_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ie_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ie.shp" > ie_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name il_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files il.shp" > il_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name im_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files im.shp" > im_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name in_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files in.shp" > in_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name io_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files io.shp" > io_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name iq_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files iq.shp" > iq_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ir_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ir.shp" > ir_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name is_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files is.shp" > is_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name it_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files it.shp" > it_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name je_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files je.shp" > je_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name jm_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files jm.shp" > jm_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name jo_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files jo.shp" > jo_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name jp_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files jp.shp" > jp_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ke_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ke.shp" > ke_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name kg_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files kg.shp" > kg_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name kh_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files kh.shp" > kh_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ki_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ki.shp" > ki_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name km_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files km.shp" > km_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name kn_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files kn.shp" > kn_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name kp_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files kp.shp" > kp_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name kr_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files kr.shp" > kr_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name kw_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files kw.shp" > kw_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ky_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ky.shp" > ky_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name kz_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files kz.shp" > kz_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name la_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files la.shp" > la_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name lb_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files lb.shp" > lb_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name lc_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files lc.shp" > lc_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name li_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files li.shp" > li_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name lk_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files lk.shp" > lk_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name lr_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files lr.shp" > lr_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ls_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ls.shp" > ls_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name lt_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files lt.shp" > lt_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name lu_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files lu.shp" > lu_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name lv_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files lv.shp" > lv_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ly_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ly.shp" > ly_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ma_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ma.shp" > ma_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name mc_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files mc.shp" > mc_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name md_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files md.shp" > md_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name me_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files me.shp" > me_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name mf_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files mf.shp" > mf_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name mg_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files mg.shp" > mg_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name mh_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files mh.shp" > mh_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name mk_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files mk.shp" > mk_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ml_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ml.shp" > ml_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name mm_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files mm.shp" > mm_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name mn_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files mn.shp" > mn_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name mo_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files mo.shp" > mo_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name mp_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files mp.shp" > mp_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name mq_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files mq.shp" > mq_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name mr_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files mr.shp" > mr_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ms_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ms.shp" > ms_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name mt_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files mt.shp" > mt_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name mu_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files mu.shp" > mu_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name mv_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files mv.shp" > mv_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name mw_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files mw.shp" > mw_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name mx_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files mx.shp" > mx_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name my_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files my.shp" > my_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name mz_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files mz.shp" > mz_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name na_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files na.shp" > na_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name nc_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files nc.shp" > nc_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ne_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ne.shp" > ne_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name nf_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files nf.shp" > nf_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ng_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ng.shp" > ng_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ni_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ni.shp" > ni_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name nl_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files nl.shp" > nl_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name no_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files no.shp" > no_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name np_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files np.shp" > np_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name nr_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files nr.shp" > nr_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name nu_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files nu.shp" > nu_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name nz_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files nz.shp" > nz_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name om_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files om.shp" > om_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name pa_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files pa.shp" > pa_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name pe_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files pe.shp" > pe_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name pf_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files pf.shp" > pf_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name pg_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files pg.shp" > pg_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ph_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ph.shp" > ph_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name pk_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files pk.shp" > pk_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name pl_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files pl.shp" > pl_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name pm_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files pm.shp" > pm_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name pn_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files pn.shp" > pn_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name pr_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files pr.shp" > pr_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ps_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ps.shp" > ps_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name pt_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files pt.shp" > pt_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name pw_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files pw.shp" > pw_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name py_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files py.shp" > py_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name qa_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files qa.shp" > qa_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name re_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files re.shp" > re_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ro_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ro.shp" > ro_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name rs_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files rs.shp" > rs_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ru_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ru.shp" > ru_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name rw_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files rw.shp" > rw_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name sa_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files sa.shp" > sa_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name sb_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files sb.shp" > sb_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name sc_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files sc.shp" > sc_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name sd_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files sd.shp" > sd_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name se_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files se.shp" > se_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name sg_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files sg.shp" > sg_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name sh_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files sh.shp" > sh_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name si_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files si.shp" > si_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name sj_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files sj.shp" > sj_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name sk_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files sk.shp" > sk_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name sl_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files sl.shp" > sl_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name sm_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files sm.shp" > sm_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name sn_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files sn.shp" > sn_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name so_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files so.shp" > so_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name sr_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files sr.shp" > sr_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ss_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ss.shp" > ss_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name st_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files st.shp" > st_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name sv_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files sv.shp" > sv_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name sx_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files sx.shp" > sx_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name sy_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files sy.shp" > sy_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name sz_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files sz.shp" > sz_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name tc_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files tc.shp" > tc_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name td_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files td.shp" > td_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name tf_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files tf.shp" > tf_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name tg_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files tg.shp" > tg_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name th_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files th.shp" > th_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name tj_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files tj.shp" > tj_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name tk_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files tk.shp" > tk_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name tl_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files tl.shp" > tl_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name tm_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files tm.shp" > tm_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name tn_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files tn.shp" > tn_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name to_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files to.shp" > to_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name tr_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files tr.shp" > tr_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name tt_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files tt.shp" > tt_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name tv_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files tv.shp" > tv_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name tw_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files tw.shp" > tw_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name tz_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files tz.shp" > tz_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ua_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ua.shp" > ua_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ug_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ug.shp" > ug_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name um_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files um.shp" > um_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name us_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files us.shp" > us_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name uy_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files uy.shp" > uy_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name uz_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files uz.shp" > uz_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name va_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files va.shp" > va_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name vc_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files vc.shp" > vc_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ve_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ve.shp" > ve_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name vg_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files vg.shp" > vg_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name vi_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files vi.shp" > vi_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name vn_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files vn.shp" > vn_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name vu_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files vu.shp" > vu_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name wf_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files wf.shp" > wf_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ws_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ws.shp" > ws_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ye_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ye.shp" > ye_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name yt_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files yt.shp" > yt_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name za_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files za.shp" > za_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name zm_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files zm.shp" > zm_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name zw_iseagg_40km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files zw.shp" > zw_iseagg_40km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ad_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ad.shp" > ad_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ae_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ae.shp" > ae_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name af_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files af.shp" > af_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ag_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ag.shp" > ag_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ai_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ai.shp" > ai_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name al_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files al.shp" > al_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name am_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files am.shp" > am_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ao_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ao.shp" > ao_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name aq_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files aq.shp" > aq_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ar_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ar.shp" > ar_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name as_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files as.shp" > as_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name at_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files at.shp" > at_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name au_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files au.shp" > au_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name aw_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files aw.shp" > aw_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ax_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ax.shp" > ax_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name az_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files az.shp" > az_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ba_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ba.shp" > ba_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name bb_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files bb.shp" > bb_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name bd_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files bd.shp" > bd_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name be_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files be.shp" > be_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name bf_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files bf.shp" > bf_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name bg_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files bg.shp" > bg_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name bh_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files bh.shp" > bh_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name bi_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files bi.shp" > bi_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name bj_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files bj.shp" > bj_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name bl_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files bl.shp" > bl_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name bm_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files bm.shp" > bm_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name bn_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files bn.shp" > bn_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name bo_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files bo.shp" > bo_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name bq_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files bq.shp" > bq_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name br_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files br.shp" > br_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name bs_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files bs.shp" > bs_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name bt_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files bt.shp" > bt_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name bv_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files bv.shp" > bv_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name bw_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files bw.shp" > bw_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name by_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files by.shp" > by_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name bz_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files bz.shp" > bz_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ca_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ca.shp" > ca_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name cc_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files cc.shp" > cc_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name cd_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files cd.shp" > cd_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name cf_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files cf.shp" > cf_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name cg_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files cg.shp" > cg_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ch_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ch.shp" > ch_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ci_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ci.shp" > ci_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ck_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ck.shp" > ck_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name cl_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files cl.shp" > cl_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name cm_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files cm.shp" > cm_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name cn_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files cn.shp" > cn_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name co_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files co.shp" > co_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name cr_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files cr.shp" > cr_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name cu_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files cu.shp" > cu_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name cv_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files cv.shp" > cv_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name cw_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files cw.shp" > cw_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name cx_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files cx.shp" > cx_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name cy_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files cy.shp" > cy_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name cz_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files cz.shp" > cz_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name de_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files de.shp" > de_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name dj_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files dj.shp" > dj_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name dk_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files dk.shp" > dk_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name dm_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files dm.shp" > dm_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name do_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files do.shp" > do_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name dz_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files dz.shp" > dz_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ec_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ec.shp" > ec_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ee_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ee.shp" > ee_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name eg_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files eg.shp" > eg_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name eh_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files eh.shp" > eh_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name er_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files er.shp" > er_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name es_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files es.shp" > es_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name et_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files et.shp" > et_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name fi_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files fi.shp" > fi_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name fj_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files fj.shp" > fj_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name fk_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files fk.shp" > fk_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name fm_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files fm.shp" > fm_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name fo_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files fo.shp" > fo_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name fr_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files fr.shp" > fr_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ga_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ga.shp" > ga_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name gb_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files gb.shp" > gb_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name gd_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files gd.shp" > gd_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ge_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ge.shp" > ge_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name gf_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files gf.shp" > gf_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name gg_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files gg.shp" > gg_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name gh_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files gh.shp" > gh_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name gi_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files gi.shp" > gi_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name gl_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files gl.shp" > gl_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name gm_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files gm.shp" > gm_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name gn_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files gn.shp" > gn_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name gp_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files gp.shp" > gp_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name gq_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files gq.shp" > gq_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name gr_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files gr.shp" > gr_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name gs_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files gs.shp" > gs_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name gt_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files gt.shp" > gt_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name gu_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files gu.shp" > gu_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name gw_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files gw.shp" > gw_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name gy_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files gy.shp" > gy_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name hk_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files hk.shp" > hk_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name hm_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files hm.shp" > hm_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name hn_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files hn.shp" > hn_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name hr_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files hr.shp" > hr_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ht_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ht.shp" > ht_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name hu_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files hu.shp" > hu_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name id_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files id.shp" > id_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ie_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ie.shp" > ie_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name il_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files il.shp" > il_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name im_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files im.shp" > im_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name in_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files in.shp" > in_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name io_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files io.shp" > io_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name iq_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files iq.shp" > iq_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ir_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ir.shp" > ir_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name is_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files is.shp" > is_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name it_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files it.shp" > it_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name je_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files je.shp" > je_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name jm_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files jm.shp" > jm_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name jo_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files jo.shp" > jo_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name jp_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files jp.shp" > jp_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ke_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ke.shp" > ke_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name kg_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files kg.shp" > kg_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name kh_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files kh.shp" > kh_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ki_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ki.shp" > ki_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name km_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files km.shp" > km_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name kn_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files kn.shp" > kn_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name kp_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files kp.shp" > kp_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name kr_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files kr.shp" > kr_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name kw_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files kw.shp" > kw_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ky_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ky.shp" > ky_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name kz_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files kz.shp" > kz_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name la_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files la.shp" > la_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name lb_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files lb.shp" > lb_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name lc_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files lc.shp" > lc_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name li_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files li.shp" > li_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name lk_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files lk.shp" > lk_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name lr_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files lr.shp" > lr_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ls_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ls.shp" > ls_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name lt_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files lt.shp" > lt_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name lu_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files lu.shp" > lu_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name lv_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files lv.shp" > lv_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ly_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ly.shp" > ly_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ma_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ma.shp" > ma_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name mc_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files mc.shp" > mc_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name md_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files md.shp" > md_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name me_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files me.shp" > me_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name mf_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files mf.shp" > mf_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name mg_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files mg.shp" > mg_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name mh_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files mh.shp" > mh_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name mk_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files mk.shp" > mk_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ml_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ml.shp" > ml_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name mm_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files mm.shp" > mm_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name mn_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files mn.shp" > mn_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name mo_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files mo.shp" > mo_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name mp_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files mp.shp" > mp_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name mq_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files mq.shp" > mq_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name mr_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files mr.shp" > mr_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ms_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ms.shp" > ms_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name mt_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files mt.shp" > mt_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name mu_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files mu.shp" > mu_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name mv_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files mv.shp" > mv_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name mw_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files mw.shp" > mw_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name mx_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files mx.shp" > mx_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name my_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files my.shp" > my_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name mz_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files mz.shp" > mz_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name na_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files na.shp" > na_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name nc_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files nc.shp" > nc_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ne_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ne.shp" > ne_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name nf_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files nf.shp" > nf_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ng_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ng.shp" > ng_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ni_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ni.shp" > ni_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name nl_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files nl.shp" > nl_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name no_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files no.shp" > no_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name np_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files np.shp" > np_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name nr_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files nr.shp" > nr_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name nu_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files nu.shp" > nu_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name nz_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files nz.shp" > nz_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name om_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files om.shp" > om_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name pa_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files pa.shp" > pa_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name pe_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files pe.shp" > pe_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name pf_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files pf.shp" > pf_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name pg_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files pg.shp" > pg_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ph_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ph.shp" > ph_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name pk_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files pk.shp" > pk_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name pl_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files pl.shp" > pl_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name pm_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files pm.shp" > pm_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name pn_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files pn.shp" > pn_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name pr_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files pr.shp" > pr_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ps_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ps.shp" > ps_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name pt_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files pt.shp" > pt_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name pw_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files pw.shp" > pw_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name py_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files py.shp" > py_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name qa_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files qa.shp" > qa_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name re_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files re.shp" > re_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ro_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ro.shp" > ro_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name rs_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files rs.shp" > rs_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ru_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ru.shp" > ru_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name rw_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files rw.shp" > rw_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name sa_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files sa.shp" > sa_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name sb_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files sb.shp" > sb_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name sc_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files sc.shp" > sc_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name sd_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files sd.shp" > sd_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name se_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files se.shp" > se_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name sg_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files sg.shp" > sg_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name sh_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files sh.shp" > sh_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name si_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files si.shp" > si_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name sj_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files sj.shp" > sj_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name sk_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files sk.shp" > sk_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name sl_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files sl.shp" > sl_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name sm_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files sm.shp" > sm_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name sn_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files sn.shp" > sn_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name so_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files so.shp" > so_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name sr_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files sr.shp" > sr_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ss_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ss.shp" > ss_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name st_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files st.shp" > st_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name sv_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files sv.shp" > sv_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name sx_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files sx.shp" > sx_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name sy_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files sy.shp" > sy_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name sz_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files sz.shp" > sz_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name tc_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files tc.shp" > tc_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name td_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files td.shp" > td_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name tf_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files tf.shp" > tf_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name tg_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files tg.shp" > tg_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name th_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files th.shp" > th_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name tj_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files tj.shp" > tj_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name tk_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files tk.shp" > tk_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name tl_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files tl.shp" > tl_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name tm_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files tm.shp" > tm_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name tn_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files tn.shp" > tn_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name to_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files to.shp" > to_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name tr_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files tr.shp" > tr_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name tt_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files tt.shp" > tt_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name tv_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files tv.shp" > tv_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name tw_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files tw.shp" > tw_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name tz_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files tz.shp" > tz_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ua_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ua.shp" > ua_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ug_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ug.shp" > ug_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name um_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files um.shp" > um_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name us_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files us.shp" > us_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name uy_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files uy.shp" > uy_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name uz_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files uz.shp" > uz_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name va_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files va.shp" > va_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name vc_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files vc.shp" > vc_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ve_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ve.shp" > ve_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name vg_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files vg.shp" > vg_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name vi_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files vi.shp" > vi_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name vn_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files vn.shp" > vn_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name vu_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files vu.shp" > vu_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name wf_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files wf.shp" > wf_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ws_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ws.shp" > ws_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name ye_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files ye.shp" > ye_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name yt_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files yt.shp" > yt_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name za_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files za.shp" > za_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name zm_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files zm.shp" > zm_iseagg_120km_radius.meta

echo "dggrid_operation GENERATE_GRID

dggs_type ISEA43H
dggs_num_aperture_4_res 3
dggs_res_spec 5

point_output_type TEXT
point_output_file_name zw_iseagg_120km_radius

clip_type POLY_INTERSECT
clip_subset_type SHAPEFILE
clip_region_files zw.shp" > zw_iseagg_120km_radius.meta

ad_iseagg_20km_radiusdggrid .meta
dggrid ae_iseagg_20km_radius.meta
dggrid af_iseagg_20km_radius.meta
dggrid ag_iseagg_20km_radius.meta
dggrid ai_iseagg_20km_radius.meta
dggrid al_iseagg_20km_radius.meta
dggrid am_iseagg_20km_radius.meta
dggrid ao_iseagg_20km_radius.meta
dggrid aq_iseagg_20km_radius.meta
dggrid ar_iseagg_20km_radius.meta
dggrid as_iseagg_20km_radius.meta
dggrid at_iseagg_20km_radius.meta
dggrid au_iseagg_20km_radius.meta
dggrid aw_iseagg_20km_radius.meta
dggrid ax_iseagg_20km_radius.meta
dggrid az_iseagg_20km_radius.meta
dggrid ba_iseagg_20km_radius.meta
dggrid bb_iseagg_20km_radius.meta
dggrid bd_iseagg_20km_radius.meta
dggrid be_iseagg_20km_radius.meta
dggrid bf_iseagg_20km_radius.meta
dggrid bg_iseagg_20km_radius.meta
dggrid bh_iseagg_20km_radius.meta
dggrid bi_iseagg_20km_radius.meta
dggrid bj_iseagg_20km_radius.meta
dggrid bl_iseagg_20km_radius.meta
dggrid bm_iseagg_20km_radius.meta
dggrid bn_iseagg_20km_radius.meta
dggrid bo_iseagg_20km_radius.meta
dggrid bq_iseagg_20km_radius.meta
dggrid br_iseagg_20km_radius.meta
dggrid bs_iseagg_20km_radius.meta
dggrid bt_iseagg_20km_radius.meta
dggrid bv_iseagg_20km_radius.meta
dggrid bw_iseagg_20km_radius.meta
dggrid by_iseagg_20km_radius.meta
dggrid bz_iseagg_20km_radius.meta
dggrid ca_iseagg_20km_radius.meta
dggrid cc_iseagg_20km_radius.meta
dggrid cd_iseagg_20km_radius.meta
dggrid cf_iseagg_20km_radius.meta
dggrid cg_iseagg_20km_radius.meta
dggrid ch_iseagg_20km_radius.meta
dggrid ci_iseagg_20km_radius.meta
dggrid ck_iseagg_20km_radius.meta
dggrid cl_iseagg_20km_radius.meta
dggrid cm_iseagg_20km_radius.meta
dggrid cn_iseagg_20km_radius.meta
dggrid co_iseagg_20km_radius.meta
dggrid cr_iseagg_20km_radius.meta
dggrid cu_iseagg_20km_radius.meta
dggrid cv_iseagg_20km_radius.meta
dggrid cw_iseagg_20km_radius.meta
dggrid cx_iseagg_20km_radius.meta
dggrid cy_iseagg_20km_radius.meta
dggrid cz_iseagg_20km_radius.meta
dggrid de_iseagg_20km_radius.meta
dggrid dj_iseagg_20km_radius.meta
dggrid dk_iseagg_20km_radius.meta
dggrid dm_iseagg_20km_radius.meta
dggrid do_iseagg_20km_radius.meta
dggrid dz_iseagg_20km_radius.meta
dggrid ec_iseagg_20km_radius.meta
dggrid ee_iseagg_20km_radius.meta
dggrid eg_iseagg_20km_radius.meta
dggrid eh_iseagg_20km_radius.meta
dggrid er_iseagg_20km_radius.meta
dggrid es_iseagg_20km_radius.meta
dggrid et_iseagg_20km_radius.meta
dggrid fi_iseagg_20km_radius.meta
dggrid fj_iseagg_20km_radius.meta
dggrid fk_iseagg_20km_radius.meta
dggrid fm_iseagg_20km_radius.meta
dggrid fo_iseagg_20km_radius.meta
dggrid fr_iseagg_20km_radius.meta
dggrid ga_iseagg_20km_radius.meta
dggrid gb_iseagg_20km_radius.meta
dggrid gd_iseagg_20km_radius.meta
dggrid ge_iseagg_20km_radius.meta
dggrid gf_iseagg_20km_radius.meta
dggrid gg_iseagg_20km_radius.meta
dggrid gh_iseagg_20km_radius.meta
dggrid gi_iseagg_20km_radius.meta
dggrid gl_iseagg_20km_radius.meta
dggrid gm_iseagg_20km_radius.meta
dggrid gn_iseagg_20km_radius.meta
dggrid gp_iseagg_20km_radius.meta
dggrid gq_iseagg_20km_radius.meta
dggrid gr_iseagg_20km_radius.meta
dggrid gs_iseagg_20km_radius.meta
dggrid gt_iseagg_20km_radius.meta
dggrid gu_iseagg_20km_radius.meta
dggrid gw_iseagg_20km_radius.meta
dggrid gy_iseagg_20km_radius.meta
dggrid hk_iseagg_20km_radius.meta
dggrid hm_iseagg_20km_radius.meta
dggrid hn_iseagg_20km_radius.meta
dggrid hr_iseagg_20km_radius.meta
dggrid ht_iseagg_20km_radius.meta
dggrid hu_iseagg_20km_radius.meta
dggrid id_iseagg_20km_radius.meta
dggrid ie_iseagg_20km_radius.meta
dggrid il_iseagg_20km_radius.meta
dggrid im_iseagg_20km_radius.meta
dggrid in_iseagg_20km_radius.meta
dggrid io_iseagg_20km_radius.meta
dggrid iq_iseagg_20km_radius.meta
dggrid ir_iseagg_20km_radius.meta
dggrid is_iseagg_20km_radius.meta
dggrid it_iseagg_20km_radius.meta
dggrid je_iseagg_20km_radius.meta
dggrid jm_iseagg_20km_radius.meta
dggrid jo_iseagg_20km_radius.meta
dggrid jp_iseagg_20km_radius.meta
dggrid ke_iseagg_20km_radius.meta
dggrid kg_iseagg_20km_radius.meta
dggrid kh_iseagg_20km_radius.meta
dggrid ki_iseagg_20km_radius.meta
dggrid km_iseagg_20km_radius.meta
dggrid kn_iseagg_20km_radius.meta
dggrid kp_iseagg_20km_radius.meta
dggrid kr_iseagg_20km_radius.meta
dggrid kw_iseagg_20km_radius.meta
dggrid ky_iseagg_20km_radius.meta
dggrid kz_iseagg_20km_radius.meta
dggrid la_iseagg_20km_radius.meta
dggrid lb_iseagg_20km_radius.meta
dggrid lc_iseagg_20km_radius.meta
dggrid li_iseagg_20km_radius.meta
dggrid lk_iseagg_20km_radius.meta
dggrid lr_iseagg_20km_radius.meta
dggrid ls_iseagg_20km_radius.meta
dggrid lt_iseagg_20km_radius.meta
dggrid lu_iseagg_20km_radius.meta
dggrid lv_iseagg_20km_radius.meta
dggrid ly_iseagg_20km_radius.meta
dggrid ma_iseagg_20km_radius.meta
dggrid mc_iseagg_20km_radius.meta
dggrid md_iseagg_20km_radius.meta
dggrid me_iseagg_20km_radius.meta
dggrid mf_iseagg_20km_radius.meta
dggrid mg_iseagg_20km_radius.meta
dggrid mh_iseagg_20km_radius.meta
dggrid mk_iseagg_20km_radius.meta
dggrid ml_iseagg_20km_radius.meta
dggrid mm_iseagg_20km_radius.meta
dggrid mn_iseagg_20km_radius.meta
dggrid mo_iseagg_20km_radius.meta
dggrid mp_iseagg_20km_radius.meta
dggrid mq_iseagg_20km_radius.meta
dggrid mr_iseagg_20km_radius.meta
dggrid ms_iseagg_20km_radius.meta
dggrid mt_iseagg_20km_radius.meta
dggrid mu_iseagg_20km_radius.meta
dggrid mv_iseagg_20km_radius.meta
dggrid mw_iseagg_20km_radius.meta
dggrid mx_iseagg_20km_radius.meta
dggrid my_iseagg_20km_radius.meta
dggrid mz_iseagg_20km_radius.meta
dggrid na_iseagg_20km_radius.meta
dggrid nc_iseagg_20km_radius.meta
dggrid ne_iseagg_20km_radius.meta
dggrid nf_iseagg_20km_radius.meta
dggrid ng_iseagg_20km_radius.meta
dggrid ni_iseagg_20km_radius.meta
dggrid nl_iseagg_20km_radius.meta
dggrid no_iseagg_20km_radius.meta
dggrid np_iseagg_20km_radius.meta
dggrid nr_iseagg_20km_radius.meta
dggrid nu_iseagg_20km_radius.meta
dggrid nz_iseagg_20km_radius.meta
dggrid om_iseagg_20km_radius.meta
dggrid pa_iseagg_20km_radius.meta
dggrid pe_iseagg_20km_radius.meta
dggrid pf_iseagg_20km_radius.meta
dggrid pg_iseagg_20km_radius.meta
dggrid ph_iseagg_20km_radius.meta
dggrid pk_iseagg_20km_radius.meta
dggrid pl_iseagg_20km_radius.meta
dggrid pm_iseagg_20km_radius.meta
dggrid pn_iseagg_20km_radius.meta
dggrid pr_iseagg_20km_radius.meta
dggrid ps_iseagg_20km_radius.meta
dggrid pt_iseagg_20km_radius.meta
dggrid pw_iseagg_20km_radius.meta
dggrid py_iseagg_20km_radius.meta
dggrid qa_iseagg_20km_radius.meta
dggrid re_iseagg_20km_radius.meta
dggrid ro_iseagg_20km_radius.meta
dggrid rs_iseagg_20km_radius.meta
dggrid ru_iseagg_20km_radius.meta
dggrid rw_iseagg_20km_radius.meta
dggrid sa_iseagg_20km_radius.meta
dggrid sb_iseagg_20km_radius.meta
dggrid sc_iseagg_20km_radius.meta
dggrid sd_iseagg_20km_radius.meta
dggrid se_iseagg_20km_radius.meta
dggrid sg_iseagg_20km_radius.meta
dggrid sh_iseagg_20km_radius.meta
dggrid si_iseagg_20km_radius.meta
dggrid sj_iseagg_20km_radius.meta
dggrid sk_iseagg_20km_radius.meta
dggrid sl_iseagg_20km_radius.meta
dggrid sm_iseagg_20km_radius.meta
dggrid sn_iseagg_20km_radius.meta
dggrid so_iseagg_20km_radius.meta
dggrid sr_iseagg_20km_radius.meta
dggrid ss_iseagg_20km_radius.meta
dggrid st_iseagg_20km_radius.meta
dggrid sv_iseagg_20km_radius.meta
dggrid sx_iseagg_20km_radius.meta
dggrid sy_iseagg_20km_radius.meta
dggrid sz_iseagg_20km_radius.meta
dggrid tc_iseagg_20km_radius.meta
dggrid td_iseagg_20km_radius.meta
dggrid tf_iseagg_20km_radius.meta
dggrid tg_iseagg_20km_radius.meta
dggrid th_iseagg_20km_radius.meta
dggrid tj_iseagg_20km_radius.meta
dggrid tk_iseagg_20km_radius.meta
dggrid tl_iseagg_20km_radius.meta
dggrid tm_iseagg_20km_radius.meta
dggrid tn_iseagg_20km_radius.meta
dggrid to_iseagg_20km_radius.meta
dggrid tr_iseagg_20km_radius.meta
dggrid tt_iseagg_20km_radius.meta
dggrid tv_iseagg_20km_radius.meta
dggrid tw_iseagg_20km_radius.meta
dggrid tz_iseagg_20km_radius.meta
dggrid ua_iseagg_20km_radius.meta
dggrid ug_iseagg_20km_radius.meta
dggrid um_iseagg_20km_radius.meta
dggrid us_iseagg_20km_radius.meta
dggrid uy_iseagg_20km_radius.meta
dggrid uz_iseagg_20km_radius.meta
dggrid va_iseagg_20km_radius.meta
dggrid vc_iseagg_20km_radius.meta
dggrid ve_iseagg_20km_radius.meta
dggrid vg_iseagg_20km_radius.meta
dggrid vi_iseagg_20km_radius.meta
dggrid vn_iseagg_20km_radius.meta
dggrid vu_iseagg_20km_radius.meta
dggrid wf_iseagg_20km_radius.meta
dggrid ws_iseagg_20km_radius.meta
dggrid ye_iseagg_20km_radius.meta
dggrid yt_iseagg_20km_radius.meta
dggrid za_iseagg_20km_radius.meta
dggrid zm_iseagg_20km_radius.meta
dggrid zw_iseagg_20km_radius.meta
dggrid ad_iseagg_40km_radius.meta
dggrid ae_iseagg_40km_radius.meta
dggrid af_iseagg_40km_radius.meta
dggrid ag_iseagg_40km_radius.meta
dggrid ai_iseagg_40km_radius.meta
dggrid al_iseagg_40km_radius.meta
dggrid am_iseagg_40km_radius.meta
dggrid ao_iseagg_40km_radius.meta
dggrid aq_iseagg_40km_radius.meta
dggrid ar_iseagg_40km_radius.meta
dggrid as_iseagg_40km_radius.meta
dggrid at_iseagg_40km_radius.meta
dggrid au_iseagg_40km_radius.meta
dggrid aw_iseagg_40km_radius.meta
dggrid ax_iseagg_40km_radius.meta
dggrid az_iseagg_40km_radius.meta
dggrid ba_iseagg_40km_radius.meta
dggrid bb_iseagg_40km_radius.meta
dggrid bd_iseagg_40km_radius.meta
dggrid be_iseagg_40km_radius.meta
dggrid bf_iseagg_40km_radius.meta
dggrid bg_iseagg_40km_radius.meta
dggrid bh_iseagg_40km_radius.meta
dggrid bi_iseagg_40km_radius.meta
dggrid bj_iseagg_40km_radius.meta
dggrid bl_iseagg_40km_radius.meta
dggrid bm_iseagg_40km_radius.meta
dggrid bn_iseagg_40km_radius.meta
dggrid bo_iseagg_40km_radius.meta
dggrid bq_iseagg_40km_radius.meta
dggrid br_iseagg_40km_radius.meta
dggrid bs_iseagg_40km_radius.meta
dggrid bt_iseagg_40km_radius.meta
dggrid bv_iseagg_40km_radius.meta
dggrid bw_iseagg_40km_radius.meta
dggrid by_iseagg_40km_radius.meta
dggrid bz_iseagg_40km_radius.meta
dggrid ca_iseagg_40km_radius.meta
dggrid cc_iseagg_40km_radius.meta
dggrid cd_iseagg_40km_radius.meta
dggrid cf_iseagg_40km_radius.meta
dggrid cg_iseagg_40km_radius.meta
dggrid ch_iseagg_40km_radius.meta
dggrid ci_iseagg_40km_radius.meta
dggrid ck_iseagg_40km_radius.meta
dggrid cl_iseagg_40km_radius.meta
dggrid cm_iseagg_40km_radius.meta
dggrid cn_iseagg_40km_radius.meta
dggrid co_iseagg_40km_radius.meta
dggrid cr_iseagg_40km_radius.meta
dggrid cu_iseagg_40km_radius.meta
dggrid cv_iseagg_40km_radius.meta
dggrid cw_iseagg_40km_radius.meta
dggrid cx_iseagg_40km_radius.meta
dggrid cy_iseagg_40km_radius.meta
dggrid cz_iseagg_40km_radius.meta
dggrid de_iseagg_40km_radius.meta
dggrid dj_iseagg_40km_radius.meta
dggrid dk_iseagg_40km_radius.meta
dggrid dm_iseagg_40km_radius.meta
dggrid do_iseagg_40km_radius.meta
dggrid dz_iseagg_40km_radius.meta
dggrid ec_iseagg_40km_radius.meta
dggrid ee_iseagg_40km_radius.meta
dggrid eg_iseagg_40km_radius.meta
dggrid eh_iseagg_40km_radius.meta
dggrid er_iseagg_40km_radius.meta
dggrid es_iseagg_40km_radius.meta
dggrid et_iseagg_40km_radius.meta
dggrid fi_iseagg_40km_radius.meta
dggrid fj_iseagg_40km_radius.meta
dggrid fk_iseagg_40km_radius.meta
dggrid fm_iseagg_40km_radius.meta
dggrid fo_iseagg_40km_radius.meta
dggrid fr_iseagg_40km_radius.meta
dggrid ga_iseagg_40km_radius.meta
dggrid gb_iseagg_40km_radius.meta
dggrid gd_iseagg_40km_radius.meta
dggrid ge_iseagg_40km_radius.meta
dggrid gf_iseagg_40km_radius.meta
dggrid gg_iseagg_40km_radius.meta
dggrid gh_iseagg_40km_radius.meta
dggrid gi_iseagg_40km_radius.meta
dggrid gl_iseagg_40km_radius.meta
dggrid gm_iseagg_40km_radius.meta
dggrid gn_iseagg_40km_radius.meta
dggrid gp_iseagg_40km_radius.meta
dggrid gq_iseagg_40km_radius.meta
dggrid gr_iseagg_40km_radius.meta
dggrid gs_iseagg_40km_radius.meta
dggrid gt_iseagg_40km_radius.meta
dggrid gu_iseagg_40km_radius.meta
dggrid gw_iseagg_40km_radius.meta
dggrid gy_iseagg_40km_radius.meta
dggrid hk_iseagg_40km_radius.meta
dggrid hm_iseagg_40km_radius.meta
dggrid hn_iseagg_40km_radius.meta
dggrid hr_iseagg_40km_radius.meta
dggrid ht_iseagg_40km_radius.meta
dggrid hu_iseagg_40km_radius.meta
dggrid id_iseagg_40km_radius.meta
dggrid ie_iseagg_40km_radius.meta
dggrid il_iseagg_40km_radius.meta
dggrid im_iseagg_40km_radius.meta
dggrid in_iseagg_40km_radius.meta
dggrid io_iseagg_40km_radius.meta
dggrid iq_iseagg_40km_radius.meta
dggrid ir_iseagg_40km_radius.meta
dggrid is_iseagg_40km_radius.meta
dggrid it_iseagg_40km_radius.meta
dggrid je_iseagg_40km_radius.meta
dggrid jm_iseagg_40km_radius.meta
dggrid jo_iseagg_40km_radius.meta
dggrid jp_iseagg_40km_radius.meta
dggrid ke_iseagg_40km_radius.meta
dggrid kg_iseagg_40km_radius.meta
dggrid kh_iseagg_40km_radius.meta
dggrid ki_iseagg_40km_radius.meta
dggrid km_iseagg_40km_radius.meta
dggrid kn_iseagg_40km_radius.meta
dggrid kp_iseagg_40km_radius.meta
dggrid kr_iseagg_40km_radius.meta
dggrid kw_iseagg_40km_radius.meta
dggrid ky_iseagg_40km_radius.meta
dggrid kz_iseagg_40km_radius.meta
dggrid la_iseagg_40km_radius.meta
dggrid lb_iseagg_40km_radius.meta
dggrid lc_iseagg_40km_radius.meta
dggrid li_iseagg_40km_radius.meta
dggrid lk_iseagg_40km_radius.meta
dggrid lr_iseagg_40km_radius.meta
dggrid ls_iseagg_40km_radius.meta
dggrid lt_iseagg_40km_radius.meta
dggrid lu_iseagg_40km_radius.meta
dggrid lv_iseagg_40km_radius.meta
dggrid ly_iseagg_40km_radius.meta
dggrid ma_iseagg_40km_radius.meta
dggrid mc_iseagg_40km_radius.meta
dggrid md_iseagg_40km_radius.meta
dggrid me_iseagg_40km_radius.meta
dggrid mf_iseagg_40km_radius.meta
dggrid mg_iseagg_40km_radius.meta
dggrid mh_iseagg_40km_radius.meta
dggrid mk_iseagg_40km_radius.meta
dggrid ml_iseagg_40km_radius.meta
dggrid mm_iseagg_40km_radius.meta
dggrid mn_iseagg_40km_radius.meta
dggrid mo_iseagg_40km_radius.meta
dggrid mp_iseagg_40km_radius.meta
dggrid mq_iseagg_40km_radius.meta
dggrid mr_iseagg_40km_radius.meta
dggrid ms_iseagg_40km_radius.meta
dggrid mt_iseagg_40km_radius.meta
dggrid mu_iseagg_40km_radius.meta
dggrid mv_iseagg_40km_radius.meta
dggrid mw_iseagg_40km_radius.meta
dggrid mx_iseagg_40km_radius.meta
dggrid my_iseagg_40km_radius.meta
dggrid mz_iseagg_40km_radius.meta
dggrid na_iseagg_40km_radius.meta
dggrid nc_iseagg_40km_radius.meta
dggrid ne_iseagg_40km_radius.meta
dggrid nf_iseagg_40km_radius.meta
dggrid ng_iseagg_40km_radius.meta
dggrid ni_iseagg_40km_radius.meta
dggrid nl_iseagg_40km_radius.meta
dggrid no_iseagg_40km_radius.meta
dggrid np_iseagg_40km_radius.meta
dggrid nr_iseagg_40km_radius.meta
dggrid nu_iseagg_40km_radius.meta
dggrid nz_iseagg_40km_radius.meta
dggrid om_iseagg_40km_radius.meta
dggrid pa_iseagg_40km_radius.meta
dggrid pe_iseagg_40km_radius.meta
dggrid pf_iseagg_40km_radius.meta
dggrid pg_iseagg_40km_radius.meta
dggrid ph_iseagg_40km_radius.meta
dggrid pk_iseagg_40km_radius.meta
dggrid pl_iseagg_40km_radius.meta
dggrid pm_iseagg_40km_radius.meta
dggrid pn_iseagg_40km_radius.meta
dggrid pr_iseagg_40km_radius.meta
dggrid ps_iseagg_40km_radius.meta
dggrid pt_iseagg_40km_radius.meta
dggrid pw_iseagg_40km_radius.meta
dggrid py_iseagg_40km_radius.meta
dggrid qa_iseagg_40km_radius.meta
dggrid re_iseagg_40km_radius.meta
dggrid ro_iseagg_40km_radius.meta
dggrid rs_iseagg_40km_radius.meta
dggrid ru_iseagg_40km_radius.meta
dggrid rw_iseagg_40km_radius.meta
dggrid sa_iseagg_40km_radius.meta
dggrid sb_iseagg_40km_radius.meta
dggrid sc_iseagg_40km_radius.meta
dggrid sd_iseagg_40km_radius.meta
dggrid se_iseagg_40km_radius.meta
dggrid sg_iseagg_40km_radius.meta
dggrid sh_iseagg_40km_radius.meta
dggrid si_iseagg_40km_radius.meta
dggrid sj_iseagg_40km_radius.meta
dggrid sk_iseagg_40km_radius.meta
dggrid sl_iseagg_40km_radius.meta
dggrid sm_iseagg_40km_radius.meta
dggrid sn_iseagg_40km_radius.meta
dggrid so_iseagg_40km_radius.meta
dggrid sr_iseagg_40km_radius.meta
dggrid ss_iseagg_40km_radius.meta
dggrid st_iseagg_40km_radius.meta
dggrid sv_iseagg_40km_radius.meta
dggrid sx_iseagg_40km_radius.meta
dggrid sy_iseagg_40km_radius.meta
dggrid sz_iseagg_40km_radius.meta
dggrid tc_iseagg_40km_radius.meta
dggrid td_iseagg_40km_radius.meta
dggrid tf_iseagg_40km_radius.meta
dggrid tg_iseagg_40km_radius.meta
dggrid th_iseagg_40km_radius.meta
dggrid tj_iseagg_40km_radius.meta
dggrid tk_iseagg_40km_radius.meta
dggrid tl_iseagg_40km_radius.meta
dggrid tm_iseagg_40km_radius.meta
dggrid tn_iseagg_40km_radius.meta
dggrid to_iseagg_40km_radius.meta
dggrid tr_iseagg_40km_radius.meta
dggrid tt_iseagg_40km_radius.meta
dggrid tv_iseagg_40km_radius.meta
dggrid tw_iseagg_40km_radius.meta
dggrid tz_iseagg_40km_radius.meta
dggrid ua_iseagg_40km_radius.meta
dggrid ug_iseagg_40km_radius.meta
dggrid um_iseagg_40km_radius.meta
dggrid us_iseagg_40km_radius.meta
dggrid uy_iseagg_40km_radius.meta
dggrid uz_iseagg_40km_radius.meta
dggrid va_iseagg_40km_radius.meta
dggrid vc_iseagg_40km_radius.meta
dggrid ve_iseagg_40km_radius.meta
dggrid vg_iseagg_40km_radius.meta
dggrid vi_iseagg_40km_radius.meta
dggrid vn_iseagg_40km_radius.meta
dggrid vu_iseagg_40km_radius.meta
dggrid wf_iseagg_40km_radius.meta
dggrid ws_iseagg_40km_radius.meta
dggrid ye_iseagg_40km_radius.meta
dggrid yt_iseagg_40km_radius.meta
dggrid za_iseagg_40km_radius.meta
dggrid zm_iseagg_40km_radius.meta
dggrid zw_iseagg_40km_radius.meta
dggrid ad_iseagg_120km_radius.meta
dggrid ae_iseagg_120km_radius.meta
dggrid af_iseagg_120km_radius.meta
dggrid ag_iseagg_120km_radius.meta
dggrid ai_iseagg_120km_radius.meta
dggrid al_iseagg_120km_radius.meta
dggrid am_iseagg_120km_radius.meta
dggrid ao_iseagg_120km_radius.meta
dggrid aq_iseagg_120km_radius.meta
dggrid ar_iseagg_120km_radius.meta
dggrid as_iseagg_120km_radius.meta
dggrid at_iseagg_120km_radius.meta
dggrid au_iseagg_120km_radius.meta
dggrid aw_iseagg_120km_radius.meta
dggrid ax_iseagg_120km_radius.meta
dggrid az_iseagg_120km_radius.meta
dggrid ba_iseagg_120km_radius.meta
dggrid bb_iseagg_120km_radius.meta
dggrid bd_iseagg_120km_radius.meta
dggrid be_iseagg_120km_radius.meta
dggrid bf_iseagg_120km_radius.meta
dggrid bg_iseagg_120km_radius.meta
dggrid bh_iseagg_120km_radius.meta
dggrid bi_iseagg_120km_radius.meta
dggrid bj_iseagg_120km_radius.meta
dggrid bl_iseagg_120km_radius.meta
dggrid bm_iseagg_120km_radius.meta
dggrid bn_iseagg_120km_radius.meta
dggrid bo_iseagg_120km_radius.meta
dggrid bq_iseagg_120km_radius.meta
dggrid br_iseagg_120km_radius.meta
dggrid bs_iseagg_120km_radius.meta
dggrid bt_iseagg_120km_radius.meta
dggrid bv_iseagg_120km_radius.meta
dggrid bw_iseagg_120km_radius.meta
dggrid by_iseagg_120km_radius.meta
dggrid bz_iseagg_120km_radius.meta
dggrid ca_iseagg_120km_radius.meta
dggrid cc_iseagg_120km_radius.meta
dggrid cd_iseagg_120km_radius.meta
dggrid cf_iseagg_120km_radius.meta
dggrid cg_iseagg_120km_radius.meta
dggrid ch_iseagg_120km_radius.meta
dggrid ci_iseagg_120km_radius.meta
dggrid ck_iseagg_120km_radius.meta
dggrid cl_iseagg_120km_radius.meta
dggrid cm_iseagg_120km_radius.meta
dggrid cn_iseagg_120km_radius.meta
dggrid co_iseagg_120km_radius.meta
dggrid cr_iseagg_120km_radius.meta
dggrid cu_iseagg_120km_radius.meta
dggrid cv_iseagg_120km_radius.meta
dggrid cw_iseagg_120km_radius.meta
dggrid cx_iseagg_120km_radius.meta
dggrid cy_iseagg_120km_radius.meta
dggrid cz_iseagg_120km_radius.meta
dggrid de_iseagg_120km_radius.meta
dggrid dj_iseagg_120km_radius.meta
dggrid dk_iseagg_120km_radius.meta
dggrid dm_iseagg_120km_radius.meta
dggrid do_iseagg_120km_radius.meta
dggrid dz_iseagg_120km_radius.meta
dggrid ec_iseagg_120km_radius.meta
dggrid ee_iseagg_120km_radius.meta
dggrid eg_iseagg_120km_radius.meta
dggrid eh_iseagg_120km_radius.meta
dggrid er_iseagg_120km_radius.meta
dggrid es_iseagg_120km_radius.meta
dggrid et_iseagg_120km_radius.meta
dggrid fi_iseagg_120km_radius.meta
dggrid fj_iseagg_120km_radius.meta
dggrid fk_iseagg_120km_radius.meta
dggrid fm_iseagg_120km_radius.meta
dggrid fo_iseagg_120km_radius.meta
dggrid fr_iseagg_120km_radius.meta
dggrid ga_iseagg_120km_radius.meta
dggrid gb_iseagg_120km_radius.meta
dggrid gd_iseagg_120km_radius.meta
dggrid ge_iseagg_120km_radius.meta
dggrid gf_iseagg_120km_radius.meta
dggrid gg_iseagg_120km_radius.meta
dggrid gh_iseagg_120km_radius.meta
dggrid gi_iseagg_120km_radius.meta
dggrid gl_iseagg_120km_radius.meta
dggrid gm_iseagg_120km_radius.meta
dggrid gn_iseagg_120km_radius.meta
dggrid gp_iseagg_120km_radius.meta
dggrid gq_iseagg_120km_radius.meta
dggrid gr_iseagg_120km_radius.meta
dggrid gs_iseagg_120km_radius.meta
dggrid gt_iseagg_120km_radius.meta
dggrid gu_iseagg_120km_radius.meta
dggrid gw_iseagg_120km_radius.meta
dggrid gy_iseagg_120km_radius.meta
dggrid hk_iseagg_120km_radius.meta
dggrid hm_iseagg_120km_radius.meta
dggrid hn_iseagg_120km_radius.meta
dggrid hr_iseagg_120km_radius.meta
dggrid ht_iseagg_120km_radius.meta
dggrid hu_iseagg_120km_radius.meta
dggrid id_iseagg_120km_radius.meta
dggrid ie_iseagg_120km_radius.meta
dggrid il_iseagg_120km_radius.meta
dggrid im_iseagg_120km_radius.meta
dggrid in_iseagg_120km_radius.meta
dggrid io_iseagg_120km_radius.meta
dggrid iq_iseagg_120km_radius.meta
dggrid ir_iseagg_120km_radius.meta
dggrid is_iseagg_120km_radius.meta
dggrid it_iseagg_120km_radius.meta
dggrid je_iseagg_120km_radius.meta
dggrid jm_iseagg_120km_radius.meta
dggrid jo_iseagg_120km_radius.meta
dggrid jp_iseagg_120km_radius.meta
dggrid ke_iseagg_120km_radius.meta
dggrid kg_iseagg_120km_radius.meta
dggrid kh_iseagg_120km_radius.meta
dggrid ki_iseagg_120km_radius.meta
dggrid km_iseagg_120km_radius.meta
dggrid kn_iseagg_120km_radius.meta
dggrid kp_iseagg_120km_radius.meta
dggrid kr_iseagg_120km_radius.meta
dggrid kw_iseagg_120km_radius.meta
dggrid ky_iseagg_120km_radius.meta
dggrid kz_iseagg_120km_radius.meta
dggrid la_iseagg_120km_radius.meta
dggrid lb_iseagg_120km_radius.meta
dggrid lc_iseagg_120km_radius.meta
dggrid li_iseagg_120km_radius.meta
dggrid lk_iseagg_120km_radius.meta
dggrid lr_iseagg_120km_radius.meta
dggrid ls_iseagg_120km_radius.meta
dggrid lt_iseagg_120km_radius.meta
dggrid lu_iseagg_120km_radius.meta
dggrid lv_iseagg_120km_radius.meta
dggrid ly_iseagg_120km_radius.meta
dggrid ma_iseagg_120km_radius.meta
dggrid mc_iseagg_120km_radius.meta
dggrid md_iseagg_120km_radius.meta
dggrid me_iseagg_120km_radius.meta
dggrid mf_iseagg_120km_radius.meta
dggrid mg_iseagg_120km_radius.meta
dggrid mh_iseagg_120km_radius.meta
dggrid mk_iseagg_120km_radius.meta
dggrid ml_iseagg_120km_radius.meta
dggrid mm_iseagg_120km_radius.meta
dggrid mn_iseagg_120km_radius.meta
dggrid mo_iseagg_120km_radius.meta
dggrid mp_iseagg_120km_radius.meta
dggrid mq_iseagg_120km_radius.meta
dggrid mr_iseagg_120km_radius.meta
dggrid ms_iseagg_120km_radius.meta
dggrid mt_iseagg_120km_radius.meta
dggrid mu_iseagg_120km_radius.meta
dggrid mv_iseagg_120km_radius.meta
dggrid mw_iseagg_120km_radius.meta
dggrid mx_iseagg_120km_radius.meta
dggrid my_iseagg_120km_radius.meta
dggrid mz_iseagg_120km_radius.meta
dggrid na_iseagg_120km_radius.meta
dggrid nc_iseagg_120km_radius.meta
dggrid ne_iseagg_120km_radius.meta
dggrid nf_iseagg_120km_radius.meta
dggrid ng_iseagg_120km_radius.meta
dggrid ni_iseagg_120km_radius.meta
dggrid nl_iseagg_120km_radius.meta
dggrid no_iseagg_120km_radius.meta
dggrid np_iseagg_120km_radius.meta
dggrid nr_iseagg_120km_radius.meta
dggrid nu_iseagg_120km_radius.meta
dggrid nz_iseagg_120km_radius.meta
dggrid om_iseagg_120km_radius.meta
dggrid pa_iseagg_120km_radius.meta
dggrid pe_iseagg_120km_radius.meta
dggrid pf_iseagg_120km_radius.meta
dggrid pg_iseagg_120km_radius.meta
dggrid ph_iseagg_120km_radius.meta
dggrid pk_iseagg_120km_radius.meta
dggrid pl_iseagg_120km_radius.meta
dggrid pm_iseagg_120km_radius.meta
dggrid pn_iseagg_120km_radius.meta
dggrid pr_iseagg_120km_radius.meta
dggrid ps_iseagg_120km_radius.meta
dggrid pt_iseagg_120km_radius.meta
dggrid pw_iseagg_120km_radius.meta
dggrid py_iseagg_120km_radius.meta
dggrid qa_iseagg_120km_radius.meta
dggrid re_iseagg_120km_radius.meta
dggrid ro_iseagg_120km_radius.meta
dggrid rs_iseagg_120km_radius.meta
dggrid ru_iseagg_120km_radius.meta
dggrid rw_iseagg_120km_radius.meta
dggrid sa_iseagg_120km_radius.meta
dggrid sb_iseagg_120km_radius.meta
dggrid sc_iseagg_120km_radius.meta
dggrid sd_iseagg_120km_radius.meta
dggrid se_iseagg_120km_radius.meta
dggrid sg_iseagg_120km_radius.meta
dggrid sh_iseagg_120km_radius.meta
dggrid si_iseagg_120km_radius.meta
dggrid sj_iseagg_120km_radius.meta
dggrid sk_iseagg_120km_radius.meta
dggrid sl_iseagg_120km_radius.meta
dggrid sm_iseagg_120km_radius.meta
dggrid sn_iseagg_120km_radius.meta
dggrid so_iseagg_120km_radius.meta
dggrid sr_iseagg_120km_radius.meta
dggrid ss_iseagg_120km_radius.meta
dggrid st_iseagg_120km_radius.meta
dggrid sv_iseagg_120km_radius.meta
dggrid sx_iseagg_120km_radius.meta
dggrid sy_iseagg_120km_radius.meta
dggrid sz_iseagg_120km_radius.meta
dggrid tc_iseagg_120km_radius.meta
dggrid td_iseagg_120km_radius.meta
dggrid tf_iseagg_120km_radius.meta
dggrid tg_iseagg_120km_radius.meta
dggrid th_iseagg_120km_radius.meta
dggrid tj_iseagg_120km_radius.meta
dggrid tk_iseagg_120km_radius.meta
dggrid tl_iseagg_120km_radius.meta
dggrid tm_iseagg_120km_radius.meta
dggrid tn_iseagg_120km_radius.meta
dggrid to_iseagg_120km_radius.meta
dggrid tr_iseagg_120km_radius.meta
dggrid tt_iseagg_120km_radius.meta
dggrid tv_iseagg_120km_radius.meta
dggrid tw_iseagg_120km_radius.meta
dggrid tz_iseagg_120km_radius.meta
dggrid ua_iseagg_120km_radius.meta
dggrid ug_iseagg_120km_radius.meta
dggrid um_iseagg_120km_radius.meta
dggrid us_iseagg_120km_radius.meta
dggrid uy_iseagg_120km_radius.meta
dggrid uz_iseagg_120km_radius.meta
dggrid va_iseagg_120km_radius.meta
dggrid vc_iseagg_120km_radius.meta
dggrid ve_iseagg_120km_radius.meta
dggrid vg_iseagg_120km_radius.meta
dggrid vi_iseagg_120km_radius.meta
dggrid vn_iseagg_120km_radius.meta
dggrid vu_iseagg_120km_radius.meta
dggrid wf_iseagg_120km_radius.meta
dggrid ws_iseagg_120km_radius.meta
dggrid ye_iseagg_120km_radius.meta
dggrid yt_iseagg_120km_radius.meta
dggrid za_iseagg_120km_radius.meta
dggrid zm_iseagg_120km_radius.meta
dggrid zw_iseagg_120km_radius.meta
