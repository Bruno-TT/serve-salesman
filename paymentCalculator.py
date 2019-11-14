def zeroFloat(n):
    try:return float(n)
    except:return.0

#read the data
f=open("input.tsv","r")
data=f.read()
f.close()


total=0

#for each line
for line in data.split("\n"):

    #split the data into columns
    line=line.split("\t")

    #if the paid date column is empty (ie it hasn't been paid)
    if not line[7]:

        #for each of the 4 payment columns
        for i in (3,4,5,6):

            #add to the total if so
            total+=zeroFloat(line[i])

#output the total
print(total)
