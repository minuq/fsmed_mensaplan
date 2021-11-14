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
    #jsonString = jsonString.replace("div","span")
    #jsonString = jsonString.replace("image","span")
    #print(jsonString)
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
            #print(days[currentDate])
        cnt+=1
        # * <td class="menue-wrapper">
        # *   <span class="menue-item menue-category">Wok</span>
        # *   <span class="menue-item menue-desc">
        # *       <span class="expand-nutr"><span class="menue-nutr">+</span>Hähnchenfleisch süss-scharf | Bananen-Erdnuss-Sauce <sup> 2,A,F,G,A1</sup> | Basmatireis</span>
        # *       <div class="nutr-info">
        # *           <div>Brennwert = 3691 kJ (882 kcal)<br>Fett = 27,9g<br>Kohlenhydrate = 101,3g<br>Eiweiß = 51,3g</div>
        # *           <img src="resources/images/inhalt/Geflügel.png" class="content-image">
        # *       </div>
        # *   </span>
        # *   <span class="menue-item menue-price large-price">3,50 €</span>
        # * </td>

        # iterate through tds of each table
        tds = table.find_all("td")
        for td in tds:
            try:
                category = "Undefined"
                # iterate through td contents, parsing menu categories
                for child in td.contents:
                    if ("menue-category" in child['class']):
                        category = child.text
                        # if category does not exist yet, add it
                        if (category not in menus[currentDate]):
                            menus[currentDate][category] = {}
                    # if there's a menu description, there are children
                    if ("menue-desc" in child['class']):
                        for dish in child.contents:
                            # if there are multiple menus for a category, append them
                            if ("expand-nutr" in dish['class']):
                                idx = len(menus[currentDate][category])
                                foodName = dish.text
                            nutrition_info = ""
                            image = ""
                            # bullshit regex parsing, but necessary
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
            #! todo side dishes
            
            except TypeError:
                pass
            except KeyError:
                pass
    #print(json.dumps(menus[currentDate], indent=2, ensure_ascii=False))
    
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
    today = datetime.strptime(menu['date'].split(", ")[1], '%d.%m.%Y')-timedelta(days=1)
    header_date = today.strftime('%Y-%m-%d')
    md = "---\ntitle: \""+header_title+"\"\ndate: "+header_date+"\ndraft: false\n---\n"
    for dish in menu:
        try:
            md+=("**"+dish+":** "+menu[dish]['0']['name'])+"\n"
            for image in menu[dish]['0']['image']:
                #md += "![image](../images/"+image+")"
                md += "<img loading=\"lazy\" style=\"display: block; float:left;\" src=\"../images/"+image+"\" alt=\""+image+"\">"
            md += "\n\n"
        except (TypeError, KeyError):
            pass
        
    return(md)
    
# Tellergericht
# Vegetarisch
# Klassiker
# Pizza des Tages
# Pizza Classics
# Wok
# Hauptbeilagen
# Nebenbeilage

f = open('content/posts/1.md','w')
f.write(convertToMarkdown(parseMenu()))
f.close()

#Klassiker {'0': {'name': 'Wirsingroulade vom Schwein (A,B,D,G,H,J) | Kümmelsauce mit Weißwein (5,L)', 
# 'nutrition_info': '', 
# 'image': ['resources/images/inhalt/Schwein.png'], 
# 'price': '2.60€'}}
