from random import choice, randint


def gen_name():
    vow = ["a", "e", "i", "o", "u"]
    con = ["b", "c", "d", "f", "g", "h", "j",
        "k", "l", "m", "n", "p", "r", "s", "t"]

    name = choice(vow) + choice(con) + choice(vow) + choice(con)

    if randint(0, 2) == 1:
        return (name).title()
    else:
        return (name + choice(con)).title()

def pick_name():
    return choice(['Clar','Grok','Otril','Gic','Kligriz'])


# def description():
