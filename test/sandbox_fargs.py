def func(a, b, *args, **kwargs):
    print(a, b)
    for arg in args:
        print(arg)
    for key, val in kwargs.items():
        print (key, val)

def func2(a, b, c=30, d=40, **kwargs):
    print(a, b)
    print(c, d)
    for key, val in kwargs.items():
        print (key, val)

def func3(a, b, c=100, d=200):
    print(a, b)
    print(c, d)



a = 1
b = 2
c = 3
d = 4
e = {'k1': 10, 'k2':20}
print ('w/o args/kwargs')
func(a, b)
print ('w/ args')
func(a, b, (c, d))
print ('w/ *args and kwargs')
func(a, b, *(c, d), e)
print ('w/ *args and **kwargs')
func(a, b, *(c, d), **e)

print ('w/ **kwargs')
f = {'d': d, 'c': c}
f.update(e)
func(a, b, **f)

print ('func2 w/ **kwargs')
f = {'d': d, 'c': c}
f.update(e)
func2(a, b, **f)

print ('func2 w/ **kwargs')
#f = {'d': d, 'c': c}
f = {}
f.update(e)
func2(a, b, **f)

print ('func3 w/ ')
func3(a, b, c, d, **{})

