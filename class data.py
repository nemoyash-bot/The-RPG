
ages = [9, 10, 11, 8, 12, 6, 14, 13, 11, 11, 9, 7, 7, 14, 19, 8, 9, 8, 12, 10]  
names = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't']
genders = ['F', 'F', 'F', 'F', 'F', 'F', 'F', 'M', 'M', 'M', 'M', 'M', 'M', 'M', 'M', 'M', 'M', 'M', 'M', 'M']

boys_under_10 = []
girls_under_10 = []

for age, name, gender in zip(ages, names, genders):
    if gender == "M" and age < 10:
        boys_under_10.append(name)
    elif gender == "F" and age < 10:
        girls_under_10.append(name)        

while True:
    choice = input("Would you like to see boy under 10 or girls under 10? (if boys under 10 type 1 else type 2) ")
    if choice == "1":
        print("Boys under 10 are:")
        print(boys_under_10)
        break
    elif choice == "2":
        print("Girls under 10 are:")    
        print(girls_under_10)
        break
    else:
        print("Invalid choice try again.")
