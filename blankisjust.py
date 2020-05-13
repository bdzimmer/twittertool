"""

Generate "blank is just blank for blank" tweets.

"""

# Copyright (c) 2020 Ben Zimmer. All rights reserved.

import random

DATA_FILENAME = "blanks.txt"
TOPIC = "music"
COUNT = 10


def main():
    """main program"""
    with open(DATA_FILENAME, "r") as data_file:
        lines = data_file.readlines()
        lines = [x.rstrip() for x in lines]

    lines = [x.split(";") for x in lines]
    items = [(x, y.split(",")) for x, y in lines]

    things = [item for item, topics in items if TOPIC in topics and "GROUP" not in topics]
    groups = [
        item for item, topics in items
        if
        # TOPIC in topics and
        "GROUP" in topics
    ]

    for _ in range(COUNT):
        thing1, thing2 = random.sample(things, 2)
        group = random.choice(groups)
        print(thing1, "is just", thing2, "for", group + ".")


if __name__ == "__main__":
    main()
