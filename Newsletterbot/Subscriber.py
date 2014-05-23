class Subscriber(object):
    name = ''
    sub = []

def newsub(name):
    subscriber = Subscriber()
    subscriber.name = name
    subscriber.sub = []
    return subscriber