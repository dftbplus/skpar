def func(a, b, *args, **kwargs):
    print(a,b)
    print(*args)
    print(**wargs)

print('call 1')
func(1,1)

print('call 2')
func(1,1, [2, 3])

print('call 3')
func(1,1, [2, 'a'], {'b':6})

print('call 4')
func(1,1, {'c':6})

print('call 5')
func(1,1, **{'c':6})
