import re
import json
import os
import sys
import urllib
import gzip
from collections import Counter

db_path = "data/recipes.json.gz"
db_source = "http://openrecipes.s3.amazonaws.com/recipeitems-latest.json.gz"
RE_INGREDIENT = re.compile("^(\d+) ([\w-]+) (.+)?")

def setup():
    try:
        f =gzip.open(db_path, "rb")

    except IOError:
        f.close()
        print("No database found at {}.".format(db_path))
        download_choice = raw_input("Download from {}? (Y/n)".format(db_source))
        if download_choice in ("Y", "y", ""):
            print("Ok, downloading...")
            urllib.urlretrieve(db_source, db_path)
            print("Done. Downloaded to {}".format(db_path))
            f =gzip.open(db_path, "rb")
        elif download_choice in ("N", "n"):
            print("Ok, exiting...")
            sys.exit()
    finally:
        lines = f.readlines()
        db = (json.loads(line) for line in lines)
        f.close()

    return db

def count_ingredients(ingredients_str, ing_ctr):
    ls = ingredients_str.split("\n")
    for ingredient in ls:
        match = re.match(RE_INGREDIENT, ingredient)
        if match:
            if match.groups()[-1] != None:
                ing = match.groups()[-1]
            elif match.groups()[-2] != None:
                ing = match.groups()[-2]
            # if ing == u"2 cloves":
                # import pdb; pdb.set_trace
            if re.search("\d", ing): # filter out measure words that slip through
                continue
            ing_ctr[ing] += 1
    return ing_ctr


def count(db):
    ingredients = Counter()
    for recipe in db:
        count_ingredients(recipe["ingredients"], ingredients)
    return ingredients

if __name__ == "__main__":
    db = setup()
    ingredients = count(db)
    from pprint import pprint
    pprint(ingredients.most_common(100))
