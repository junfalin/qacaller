print("test@artifact@hello")
print("test@param@K1:100")
print("test@param@K1:200")
print('test@params@{"ma":20,"K2":3}')
for i in range(10):
    print(f"thread1@metric@number:{i}")
    print(f'thread1@metrics@{{"age":{i + 2},"total":{i + 3}}}')
print("test@tag@color:red")
print("test@tag@color:Green")
print('test@tags@{"age":"18","性别":"male"}')
print("thread1@artifact@helloworld！")

1 / 0

r"""
python qacaller\listener.py --run test --cmd "python D:\\qacaller\\qacaller\\Test.py"
"""
