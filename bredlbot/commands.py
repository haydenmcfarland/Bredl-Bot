from random import randrange


def dev():
    return '7/23/17: Chat logs are live. Custom and Moderation level commands are not implemented.'


def hello(user):
    return 'Hey {}, hope you enjoy your stay!'.format(user)


def solid():
    return 'Snake? Snake? Snaaaake? BibleThump'


def banned(user):
    return 'Ssssssayanara {}!'.format(user)


def roll(user):
    return '{} rolled a {}'.format(user, randrange(1,101))


