#test lúc coi video hướng dẫn của python


a= "+49 (176) 123-4567"

print (a)
print (a.replace("+","00").replace(" (","").replace(") ","").replace("-",""))

stamp = "1000-22-33-4-2-222-33-2423-23413 14:30"

print(stamp.replace(" ","-").split("-"))
 
text = "2026/20/04 . Today I study python and it looks easy, oke, dont worry, it will be okey"

#2
print(text[0])

#y
print(text[-1])

#22/00  oa  td yhnadi ok ay k,dn or,i ilb k
print(text[0:-1:2])

#extract day
print(text[5:7])

#extract month
print(text[8:10])

#extract year
print(text[:4])

#clean space
text = "  outer space # @ "

print(text.lstrip())
print(text.rstrip())
print(text.strip())
print(text.strip(' # @'))

date = "2026/20/04"

print(date.startswith("2026")) #true
print(date.endswith("14")) #false
print(date.find("/")) #4


#data type
a = 9
b=10
print (float(a))
print (str(a))
print (complex(a,b))


ids = [201, 302, 10.03]
names = ["a","b","c"]
print(list(zip(ids,names)))

print (list(filter(lambda x: type(x) is int,list(ids))))


user = {
    "id":1,
    "name":"John",
    "age": 30,
    "city":"berlin"
}
cleaned_user = {
    k: v.upper()
    for k,v in user.items()
    if (type(v) is str)
}
# for k,v in user.items():
#     if (type(v) is str):
#         cleaned_user[k]=v.upper()
print (cleaned_user)