#!/usr/bin/env python

import requests
from bs4 import BeautifulSoup, NavigableString
import json
import re
from babel.dates import format_date
from datetime import datetime, date, timedelta


# returns a json containing all available days
def parseMenu():
    url = 'https://www.studierendenwerk-aachen.de/speiseplaene/vita-w.html'
    r = requests.get(url)
    r.encoding = "utf-8"
    jsonString = r.text.replace("<br>"," ").replace("<br />"," ")
    jsonString = re.sub("<span class=\"seperator\">(.+?)</span>",r' \1 ', jsonString)
    jsonString = jsonString.replace("<span class=\"menue-nutr\">+</span>", "")
    jsonString = jsonString.replace("<sup> ", "(")
    jsonString = jsonString.replace("</sup>", ")")
    jsonString = BeautifulSoup(jsonString, 'html.parser')
    pricingList = {
        "Wok":"3.50€",
        "Pasta":"3.50€",
        "Pizza Classics":"3.50€",
        "Pizza des Tages":"3.50€",
        "Klassiker":"2.60€",
        "Vegetarisch":"2.10€"
    }

    menus = {}

    # create an array of days that we'll call upon later
    days = []
    h3 = jsonString.find_all("h3")
    for day in h3:
        days.append(day.text)

    tables = jsonString.find_all("table")
    cnt = 0
    for table in tables:
        if (cnt % 2 == 0):
            currentDate = int(cnt/2)
            menus[currentDate] = {"date":days[currentDate]}
        cnt+=1

        # iterate through tds of each table
        tds = table.find_all("td")
        for td in tds:
            try:
                category = "Undefined"
                # iterate through td contents, finding menu categories
                for child in td.contents:
                    if ("menue-category" in child['class']):
                        category = child.text
                        # if category does not exist yet, add it
                        if (category not in menus[currentDate]):
                            menus[currentDate][category] = {}
                    # if there's a menu description, there are children
                    if ("menue-desc" in child['class']):
                        # side dishes need to be handled different, having no nutr-info class
                        if ("extra" in child['class']):
                            idx = len(menus[currentDate][category])
                            foodName = child.text
                            menus[currentDate][category][idx] = {
                                "name": foodName,
                                "image": ""
                            }

                        for dish in child.contents:
                            # if there are multiple menus for a category, append them
                            if ("expand-nutr" in dish['class']):
                                idx = len(menus[currentDate][category])
                                foodName = dish.text
                            nutrition_info = ""
                            image = ""
                            # bullshit regex parsing, but necessary
                            # at least it was when nutrition info was still provided
                            for div in child:
                                nutrition_info = re.sub("<div>Brennwert(.+?)</div>",r'Brennwert \1',dish.text)
                                if ("nutr-info" in div['class']):
                                    image = re.findall(r'src=\"resources/images/inhalt/(.+?)\"',str(div))
                            price = 0.0
                            try:
                                price = pricingList[category]
                            except Exception:
                                pass
                            menus[currentDate][category][idx] = {
                                "name": foodName, 
                                "nutrition_info": nutrition_info,
                                "image": image,
                                "price": price
                            }
            except TypeError:
                pass
            except KeyError:
                pass
    d = date.today().strftime('%A')
    today = date.today()
    if d == "Saturday":
        today += timedelta(days=2)
    if d == "Sunday":
        today += timedelta(days=1)


    today = format_date(today, 'EEEE, dd.M.yyyy', locale='de_DE')
    try:
        return(json.dumps(menus[days.index(today)], indent=2, ensure_ascii=False))
    except ValueError:
        return("Mensa geschlossen")



def convertToMarkdown(jsonString):
    menu = json.loads(jsonString)
    header_title = menu['date'].split(", ")[0]
    today = datetime.strptime(menu['date'].split(", ")[1], '%d.%m.%Y')
    header_date = today.strftime('%Y-%m-%d')
    # publish date has to be in the past so we make that happen
    # not a static date though so our action doesn't fail on weekends and causes nasty emails
    print(today)
    header_publish = today-timedelta(days=365)
    header_publish = header_publish.strftime('%Y-%m-%d %H:%M:%S')
    md = "---\ntitle: \""+header_title+"\"\ndate: "+header_date+"\npublishDate: "+header_publish+"\ndraft: false\n---\n"
    for dish in menu:
        try:
            if (dish == "date"):
                continue
            md+="### "+dish+"  \n"
            for variant in menu[dish]:
                md += "<div class=\"flex-container\">\n<div>"
                # remove allergen informations as nobody really cares on this display
                name = re.sub(" \(.+?\)","",menu[dish][variant]['name']).replace(" | ",", ")
                # replace trailing " oder  " if there's no alternative
                if (name[-7:]==" oder  "):
                    name = name[0:-7]
                md += name
                md += "</div>"
                md += "<div margin-left=\"auto\">"
                for image in menu[dish][variant]['image']:
                    md += "<img loading=\"lazy\" src=\"../images/"+image+"\" style=\"float:right;\" alt=\""+image+"\" height=30px>"
                md += "</div>"
                md +="</div>"
            # double newline is necessary for hugo to interpret headlines correctly
            md += "\n\n"
        except (TypeError, KeyError):
            pass
    return(md)

f = open('content/posts/1.md','w')
f.write(convertToMarkdown(parseMenu()))
f.close()
