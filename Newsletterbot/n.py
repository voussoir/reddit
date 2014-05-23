import Subscriber

n = Subscriber.newsub('o')
m = Subscriber.newsub('p')
n.sub.append('hallo')
print(n.name, n.sub)
print(m.name, m.sub)