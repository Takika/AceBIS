#!/usr/bin/python3

import xmltodict
import argparse
import requests
import json
import re
import os
from classes.dk_unholy import dk_unholy
from classes.dk_protection import dk_protection
from classes.druid_balance import druid_balance
from classes.druid_feral import druid_feral
from classes.druid_tank import druid_tank
from classes.druid_restoration import druid_restoration
from classes.hunter_survival import hunter_survival
from classes.mage_arcane import mage_arcane
from classes.mage_fire import mage_fire
from classes.paladin_holy import paladin_holy
from classes.paladin_protection import paladin_protection
from classes.paladin_retribution import paladin_retribution
from classes.priest_discipline import priest_discipline
from classes.priest_shadow import priest_shadow
from classes.rogue_assassination import rogue_assassination
from classes.rogue_combat import rogue_combat
from classes.shaman_elemental import shaman_elemental
from classes.shaman_enhancement import shaman_enhancement
from classes.shaman_restoration import shaman_restoration
from classes.warlock_affliction import warlock_affliction
from classes.warrior_arms import warrior_arms
from classes.warrior_fury import warrior_fury
from classes.warrior_protection import warrior_protection


item_id = 0
first_id = 20000
final_id = 100000
wowhead_wotlk="https://www.wowhead.com/wotlk/item=%s&xml"

specs = {
    "dk_unholy": dk_unholy,
    "dk_protection": dk_protection,
    "druid_balance": druid_balance,
    "druid_feral": druid_feral,
    "druid_tank": druid_tank,
    "druid_restoration": druid_restoration,
    "hunter_survival": hunter_survival,
    "mage_arcane": mage_arcane,
    "mage_fire": mage_fire,
    "paladin_holy": paladin_holy,
    "paladin_protection": paladin_protection,
    "paladin_retribution": paladin_retribution,
    "priest_discipline": priest_discipline,
    "priest_shadow": priest_shadow,
    "rogue_assassination": rogue_assassination,
    "rogue_combat": rogue_combat,
    "shaman_elemental": shaman_elemental,
    "shaman_enhancement": shaman_enhancement,
    "shaman_restoration": shaman_restoration,
    "warlock_affliction": warlock_affliction,
    "warrior_arms": warrior_arms,
    "warrior_fury": warrior_fury,
    "warrior_protection": warrior_protection,
}

# socket{1,2,3} : 1 - meta, 2 - red, 3 - yellow, 4 - blue

def calculate_epv(spec, item):
    if not spec:
        return 0

    epv = 0
    for key in spec:
        if key in item:
            epv = epv + spec[key] * item[key]
        # item needs to be activated, usually persists for 20s with 2min colddown
        if "use_" + key in item:
            #print("use_%s = %s, ep = %s" % (key, item["use_" + key], item["use_" + key] * 20 / 120))
            epv = epv + spec[key] * item["use_" + key] * 20 / 120

    for idx in [ "1", "2", "3", "4"]:
        if "socket" + idx in item:
            if item["socket" + idx] == 1:
                epv = epv + 40
            else:
                epv = epv + spec["socket"] 

    return epv

def write_itemdata(data):
    with open('itemdata.txt', 'w') as file:
        file.write(json.dumps(data, ensure_ascii=False)) # use `json.loads` to do the reverse

def read_itemdata():
    if not os.path.exists("itemdata.txt"):
        return False

    with open("itemdata.txt") as file:
        userdata = file.read()
        #print("read data: %s" % userdata)
        return json.loads(userdata)

def get_one_item(items, item_id, cached, update):
    item = {}

    item_id = str(item_id)

    # okay to get item from cache and item exists in cache
    if item_id in items.keys() and cached:
        print("get item_id %s from cache" % item_id)
        item = items[item_id]

    # want to update score, if the item doesn't exist then return
    if not item and update:
        return item

    # item doesn't exist in cache and not for update score
    if not item and not update:
        print("retriving item_id %s from wowhead" % item_id)
        url = wowhead_wotlk % item_id
        r = requests.get(url)
        try:
            root = xmltodict.parse(r.text)
        except Exception as err:
            print(f"Unexpected {err=}, {type(err)=}")
            print("Error: %s" % r.text)
            return

        if "item" not in root["wowhead"]:
            return

        item = root["wowhead"]["item"]

        # do not store command or green items
        if int(item["quality"]["@id"]) <= 2:
            return

        # do not store low item level items
        if int(item["level"]) <= 130:
            return

        #value = item["name"]
        #print("name = %s" % value)
        #value = item["class"]["@id"]
        #print("class = %s" % value)
        #value = item["subclass"]["@id"]
        #print("subclass = %s" % value)
        value = item["inventorySlot"]["@id"]
        #print("inventorySlot = %s" % value)

        # can't equip
        if value == "0":
            return

        value = item["htmlTooltip"]
        m = re.search('Phase \d', value)
        if m is not None:
            value = m.group(0).split(' ')[1]
        else:
            value = "0"

        #print("phase = %s" % value)
        item["phase"] = value
        value = '{' + item["json"] + '}'
        #print("json = %s" % value)
        item_json = json.loads(value)
        for key in item_json.keys():
            item[key] = item_json[key]
        #print("json = %s" % item_json)
        # jsonEquip = "{\"appearances\":{\"0\":[55310,\"\"]},\"armor\":1821,\"avgbuyout\":27999997,\"critstrkrtng\":44,\"displayid\":55310,\"dura\":100,\"hitrtng\":60,\"nsockets\":2,\"reqlevel\":80,\"sellprice\":100067,\"slotbak\":1,\"socket1\":1,\"socket2\":4,\"socketbonus\":2787,\"str\":97}"
        value = '{' + item["jsonEquip"] + '}'
        item_equip_json = json.loads(value)
        #print("jsonEquip = %s" % item_equip_json)
        for key in item_equip_json.keys():
            #print("add key %s = %s" % (key, item_equip_json[key]))
            item[key] = item_equip_json[key]

        if "jsonUse" in item:
            # 'jsonUse': '"armorpenrtng":291'
            value = '{' + item["jsonUse"] + '}'
            print("jsonUse = %s" % value)
            item_use_json = json.loads(value)
            for key in item_use_json.keys():
                print("add key %s = %s" % (key, item_use_json[key]))
                item["use_" + key] = item_use_json[key]

    if len(item) == 0:
        return

    for spec in specs:
        item[spec] = calculate_epv(specs[spec], item)

    items[item_id] = item

    item = items[item_id]

    print(item)

def get_all_items(items, cached, update):
    item_id = first_id
    while item_id < final_id:
        #print("item id = %s" % item_id)
        get_one_item(items, item_id, cached, update)
        item_id = item_id + 1

def main():
    parser = argparse.ArgumentParser(description='Get items from wowhead website.')
    parser.add_argument("-i", "--itemid", help="item id")
    parser.add_argument("-r", "--reload", help="retrive items from wowhead directly", action="store_true")
    parser.add_argument("-a", "--all", help="get all items", action="store_true")
    parser.add_argument("-u", "--update", help="update item score(won't access wowhead website)", action="store_true")
    args = parser.parse_args()

    items = read_itemdata() or {}

    if args.itemid:
        item_id = args.itemid
        get_one_item(items, item_id, not args.reload, args.update)

    if args.all:
        get_all_items(items, not args.reload, args.update)

    write_itemdata(items)

if __name__ == "__main__":
    main()
