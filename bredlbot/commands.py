from random import randrange


def dev():
    return '7/31/17: Chat logs are live. Custom and Moderation level commands are not implemented.'


def hello(user):
    return 'Hey {}, hope you enjoy your stay!'.format(user)


def solid():
    return 'Snake? Snake? Snaaaake? BibleThump'


def roll(user):
    return '{} rolled a {}'.format(user, randrange(1, 101))


def uptime(d):
    if d:
        hours = d.seconds // 3600
        minutes = (d.seconds // 60) % 60
        if hours != 0:
            return 'Stream has been up for {} hours and {} minutes.'.format(hours, minutes)
        else:
            return 'Stream has been up for {} minutes.'.format(minutes)
    else:
        return 'Stream is not live.'
