
class Mymath:
    def round(num):
        print("The number you round up is ",round(num))
    def abs(num):
        print("The number postove number is ",abs(num))
        
while True :
    print("                                                                                        ")
    print("×"*4,"    Welcome to my math    ","×"*4)
    print("Enter the number to want :")
    print("1.    round our number")
    print("2.    change your number to postion sign")
    print("3.    Exit")
    choose = input("Enter choose :")

    if choose == "1":
        num= float(input("Enter number :"))    
        Mymath.round(num)    
    elif choose == "2":
        num= int(input("Enter number :"))     
        Mymath.abs(num)   
    elif choose == "3":
        break
    else:
        print("You enter wrong detail","\n>>>>>",choose ,"<<<<<")