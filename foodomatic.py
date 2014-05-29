import re
import json
import os
import sys
import urllib
import gzip
from collections import Counter

db_path = "data/slim_recipes.json"
recipe_path = "data/recipes.json.gz"
recipe_source = "http://openrecipes.s3.amazonaws.com/recipeitems-latest.json.gz"
ings_path = "data/ings.json"

measure_words = ["gallon", "gal", "quart", "q", "cup", "tablespoon",
                 "tbsp", "teaspoon", "tsp", "ml", "dash", "dashes",
                 "pinch", "pinches", "pound", "ounce", "ounces", "oz",
                 "fl oz", "fl. oz", "clove", "whole", "box", "boxes",
                 "package", "stick", "weight", "fluid", "\d+", ""]

RE_AMOUNT = re.compile(r"[\d\xbc-\xbe]+ "+"s?|[\d\xbc-\xbe]+ ".join(measure_words), flags=re.I|re.U)
# RE_INVALID_ING = re.compile("|".join(measure_words), flags=re.I|re.U)

def setup():
    if not os.path.isfile(db_path):
        print("No database found at {}. Building...".format(db_path))

        try:
            recipes = gzip.open(recipe_path, "rb")
        except IOError:
            download_choice = raw_input("No recipe data. Download from {}? (Y/n)".format(recipe_source))
            if download_choice in ("Y", "y", ""):
                print("Ok, downloading...")
                urllib.urlretrieve(recipe_source, db_path)
                print("Done. Downloaded to {}".format(recipe_path))
                recipes =gzip.open(recipe_path, "rb")
            elif download_choice in ("N", "n"):
                print("Ok, exiting...")
                sys.exit()

        finally:
            lines = recipes.readlines()
            recipe_list = (json.loads(line) for line in lines)
            # import pdb; pdb.set_trace()
            db = [{"ingredients": recipe["ingredients"].split("\n"),
                   "yield": recipe.get("recipeYield")} for recipe in recipe_list]
        with open(db_path, "wb") as db_file:
            json.dump(db, db_file)

    with open(db_path, "rb") as db_file:
        db = json.loads(db_file.read())

    return db

def extract_ingredient(ing_list):
    # ings = []
    # for ing_str in ing_list:
        # ing = re.sub(RE_AMOUNT, "", ing_str).strip("1/, ")
        # if re.search(RE_INVALID_ING, ing):
            # continue
        # ings.append(ing)
    return [re.sub(RE_AMOUNT, "", ing_str).strip("1/, ") for ing_str in ing_list]
    # return ings

def count_ingredients(db):
    ing_ctr = Counter()
    ing_dict = {}
    for ing_list in db:
        for ing in ing_list:
            ing_ctr[ing] += 1
            if ing not in ing_dict:
                ing_dict[ing] = Counter()
            for other_ing in ing_list:
                if other_ing == ing:
                    continue
                ing_dict[ing][other_ing] += 1
    return ing_dict, ing_ctr


# def extract_ingredient_amount(ing_list):
#     ingredients = {}
#     for ing_str in ing_list:
#         ing = re.sub(RE_AMOUNT, "", ing_str)
#         amt = re.search(RE_AMOUNT, ing_str).group(0)
#         ingredients[ing]=amt
#     return ingredients

def main():
    if os.path.isfile(ings_path):
        with open(ings_path, "rb") as ings_file:
            ings = json.loads(ings_file.read())
    else:
        db = setup()
        db = [extract_ingredient(recipe["ingredients"]) for recipe in db]
        db_dict, ing_ctr = count_ingredients(db)
        most_common_ingredients = [_[0] for _ in ing_ctr.most_common(200)]
        most_common_pairings = [dict(db_dict[ing].most_common(50)) for ing in most_common_ingredients]
        ings = dict(zip(most_common_ingredients, most_common_pairings))
        with open(ings_path, "wb") as ings_file:
            json.dump(ings, ings_file)

    import pdb; pdb.set_trace()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--clean", action="store_true", default=False)
    args = parser.parse_args()
    if args.clean and os.path.isfile(db_path):
        os.remove(db_path)

    if args.clean and os.path.isfile(ings_path):
        os.remove(ings_path)

    main()
