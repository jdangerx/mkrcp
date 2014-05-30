mkrcp
=====

Uses the [Open Recipes](https://github.com/fictivekin/openrecipes)
database to generate "recipes". They are actually just lists of
ingredients, which is usually enough to figure out how to make the
food.

Usage:

```
foodomatic.py [-h] [-c] [-g GENRE] [-n] [-N NUMBER] [outfile]

positional arguments:
  outfile               File to output recipes to. If none given, prints to stdout.

optional arguments:
  -h, --help            show this help message and exit
  -c, --clean           Removes any existing refined recipe data.
  -g GENRE, --genre GENRE
                        Currently only accepts 'drinks' and 'entrees'.
                        Defaults to 'entrees'.
  -n, --normal          Tries to make probable recipes instead of improbable
                        ones.
  -N NUMBER, --number NUMBER
                        Number of recipes to generate.
```
