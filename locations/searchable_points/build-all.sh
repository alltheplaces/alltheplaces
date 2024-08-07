#!/usr/bin/env bash

if ! command -v unzip &> /dev/null
then
    echo "unzip could not be found"
    exit 1
fi


if ! command -v ogr2ogr &> /dev/null
then
    echo "ogr2ogr could not be found. You may want to add the gdal-bin package"
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

if [ ! -f fi
.shp ]; then
  ogr2ogr -sql "SELECT OGR_GEOMETRY FROM ne_10m_admin_0_countries_lakes WHERE ISO_A2='FI
  '" fi
  .shp ne_10m_admin_0_countries_lakes.shp
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