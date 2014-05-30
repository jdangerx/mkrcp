import re
import json
import os
import sys
import urllib
import gzip
import pdb
import random
import string
from collections import Counter, deque

db_path = "data/slim_recipes.json"
recipe_path = "data/recipes.json.gz"
recipe_source = "http://openrecipes.s3.amazonaws.com/recipeitems-latest.json.gz"
ings_path = "data/ings.json"

measure_words = ["gallon", "gal", "quart", "q", "cup", "tablespoon",
                 "tbsp", "teaspoon", "tsp", "ml", "dash", "dashes",
                 "pinch", "pinches", "pound", "ounce", "ounces", "oz",
                 "fl oz", "fl. oz", "clove", "whole", "box", "boxes",
                 "package", "stick", "weight", "fluid", "\d+", "oz.",
                 "jar", "can", "slice", "slices", "tbs.", "pint"]

RE_AMOUNT = re.compile(r"\d+g|([\d\xbc-\xbe/]+ )+"+"s?|([\d\xbc-\xbe]+ )+".join(measure_words), flags=re.I|re.U)

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
            db = [{"ingredients": recipe["ingredients"].split("\n"),
                   "yield": recipe.get("recipeYield")} for recipe in recipe_list]
        with open(db_path, "wb") as db_file:
            json.dump(db, db_file)

    with open(db_path, "rb") as db_file:
        db = json.loads(db_file.read())

    return db

def main(args):
    if os.path.isfile(ings_path):
        with open(ings_path, "rb") as ings_file:
            ings = json.loads(ings_file.read())
    else:
        db = setup()
        db = [extract_ingredient(recipe["ingredients"]) for recipe in db]
        db_dict, ing_ctr = count_ingredients(db)
        most_common_ingredients = [_[0] for _ in ing_ctr.most_common(1000)]
        most_common_pairings = [dict(db_dict[ing].most_common(100)) for ing in most_common_ingredients]
        ings = dict(zip(most_common_ingredients, most_common_pairings))
        with open(ings_path, "wb") as ings_file:
            json.dump(ings, ings_file)


    entrees = ["potatoes", "chicken breasts", "chicken thighs",
               "ground beef", "pork chops", "uncooked white rice",
               "basmati rice", "quinoa"]

    drinks = ["brandy", "bourbon", "vodka", "gin", "rum"]

    food_type = {"drinks": drinks, "entrees": entrees}

    # for i in range(20):
    while True:
        ing1 = random.choice(food_type[args.genre])
        ing2 = random.choice(ings.keys())
        recipe = link_ingredients(ing1, ing2, ings, args)
        print(string.capwords(u"{} with {}\n".format(ing1, ing2)))
        if recipe:
            print(u"Commonness Index: {0:.2f}".format(recipe[0]*1000))
            try:
                print(u"Recipe:\n- "+u"\n- ".join(recipe[1]))
            except UnicodeDecodeError:
                print("Unicode is the way of the devil!")
        else:
            print("Recipe:\nNo path can guide the wicked.")
        print("\n"+"="*80+"\n")
        from time import sleep
        sleep(5)


def extract_ingredient(ing_list):
    new_ing_list = []
    for ing in ing_list:
        new_ing = re.sub(RE_AMOUNT, "", ing)
        new_ing = re.sub(r"[:%\d/,()\. -]+", lambda x: " ", new_ing)
        new_ing = new_ing.strip()
        new_ing = new_ing.lower()
        new_ing_list.append(new_ing)
    return new_ing_list

def count_ingredients(db):
    ing_ctr = Counter()
    ing_dict = {}
    for ing_list in db:
        for ing in ing_list:
            ing_ctr[ing] += 1
            if ing not in ing_dict:
                ing_dict[ing] = Counter()
            for other_ing in ing_list:
                ing_dict[ing][other_ing] += 1
    return ing_dict, ing_ctr

def make_recipes_n_prob(n, num_ingredients, num_recipes, ings):
    recipes = []
    for i in range(num_recipes):
        recipe = [random.choice(ings.keys())]
        while len(recipe) < num_ingredients:
            recipe = n_probable(n, recipe, ings)
        recipes.append(recipe)
    return recipes


def n_probable(n, recipe, ings):
    seed_dict = None
    while seed_dict == None:
        seed = random.choice(recipe)
        seed_dict = ings.get(seed)
    seed_dict.pop(seed, None)
    seed_sorted = sorted(seed_dict, key=seed_dict.get, reverse=True)
    max_size = seed_dict[seed_sorted[0]]
    possible_ings = []
    additional_ings = set()
    while len(possible_ings) < n:
        rand = random.randint(1, max_size)
        possible_ings = {_ for _ in ings[seed].keys() if rand > ings[seed][_]} - set(recipe)
    for i in range(n):
        rand_choice = random.choice(list(possible_ings))
        additional_ings.add(rand_choice)
        possible_ings.remove(rand_choice)
    return recipe+list(additional_ings)

def link_ingredients(source, end, ings, args):
    queue = deque([(source, [])])
    visited = Counter({source: len(ings[source].keys())})
    paths = []
    while len(queue) > 0:
        test_ing, test_path = queue.popleft()
        new_test_path = test_path + [test_ing]
        if test_ing == end:
            paths.append((get_average_weight(new_test_path, ings), new_test_path))
        else:
            try:
                ing_size = len(ings[test_ing].keys())
                ing_sorted = sorted(ings[test_ing].keys(), key=ings[test_ing].get, reverse=args.normal)
                possible_ings = ing_sorted[:int(ing_size/4)]
                for ing in possible_ings:
                    if ing == test_ing:
                        continue
                    if visited[ing] < 1:
                        queue.append((ing, new_test_path))
            except KeyError:
                continue
        visited[test_ing] += 1
    if paths != []:
        return sorted(paths, reverse = args.normal)[0]
    else:
        return None

def get_average_weight(ing_list, ings):
    edges = zip(ing_list[:-1], ing_list[1:])
    sum = 0
    for e in edges:
        size = float(ings[e[0]][e[0]])
        weight = float(ings[e[0]][e[1]])
        sum += weight/size
    return sum/len(edges)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--clean", action="store_true", default=False)
    parser.add_argument("-g", "--genre", default="entrees")
    parser.add_argument("-n", "--normal", action="store_true", default=False)
    args = parser.parse_args()
    if args.clean and os.path.isfile(db_path):
        os.remove(db_path)

    if args.clean and os.path.isfile(ings_path):
        os.remove(ings_path)

    main(args)
