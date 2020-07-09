
print("test@param@K1:100")

print('test@params@{"ma":20,"K2":3}')

for i in range(10):
    print(f"thread1@metric@number:{i}")

    print(f'thread1@metrics@{{"age":{i + 2},"total":{i + 3}}}')

print("test@tag@color:red")

print('test@tags@{"age":"18","sex":"male"}')
print("test@artifact@hello")
