import csv
import googlemaps
import datetime
import math
import time

mode="transit"

#opening the key from the file, so i don't need to store it in github
key_file=open("key.txt")
key=key_file.read()
key_file.close()

#sign into gmaps
gmaps=googlemaps.Client(key)

#open and parse the csv file
file_data=csv.reader(open('data.csv'))

#location class, for a site
class Location():
    def __init__(self, number, name, address):
        self.name=name
        self.address=address
        
        #we need an ID to refer to it by internally
        self.number=number

#global dicts for locations and addresses
locations=[]
addresses=[]

#for each location
for n,location in enumerate(file_data):

    #initialise its object, giving it a number, name and address
    l=Location(n, location[0],location[0]+", "+location[1])
    
    #add the address to the addresses array
    addresses.append(l.address)

    #add the location to the locations array
    locations.append(l)

#inputting the home address
homeAddress = input("please input your home postcode :)\n")
print("\n")

#initialising the home object
home=Location(-1, "home", homeAddress)

#adding home to addresses array. It's added as we need it to be in the API request
addresses.append(homeAddress)

#assume all journeys take place at midday tomorrow, to simplify things. This is a way the app could be improved.
MIDDAY_TOMORROW=datetime.datetime(datetime.datetime.now().year, datetime.datetime.now().month, datetime.datetime.now().day+1, 12)

locations.append(home)

#make the distance matrix requests
#TODO: make less larger requests
travelTimes={}
for origin in locations:
    fromTimes=gmaps.distance_matrix(origins=[origin.address], destinations=addresses, mode=mode, departure_time=MIDDAY_TOMORROW)
    for destination in locations:
        travelTimes[(origin, destination)]=fromTimes["rows"][0]["elements"][destination.number]["duration"]["value"]/60

locations.remove(home)

#function for finding the travel time between 2 places
routeTime=lambda from_, to: travelTimes[(from_, to)]

#initialising the result variables
shortestTime=math.inf
shortestRoute=None

#main recursive depth first search route finder
def tryRoutes(currentTime, currentRoute, currentRemaining):

    #globalising result variables
    global shortestTime, shortestRoute

    #if we've finished a route
    if currentRemaining==():
        
        #go home at the end and update the total time
        totalTime=currentTime+routeTime(currentRoute[-1], home)

        #if it's the new fastest route then record it
        if totalTime<shortestTime:
            shortestTime=totalTime
            shortestRoute=currentRoute+(home,)
            print("new shortest route found! Travel time: "+str(shortestTime))
    
    #if this route (unfinished!) is already slower than the fastest route then don't pursue it any further
    #this is the best line in the code, without it the code would take so much longer, by pursuing all ridiculous routes
    elif currentTime>shortestTime:
        pass
    
    #otherwise, pursue all the remaining neighbours
    else:

        #for each possible next node
        for n,nextNode in enumerate(currentRemaining):

            #calculate the new trip time
            newCurrentTime=currentTime+routeTime(currentRoute[-1], nextNode)

            #add it to the new route
            newCurrentRoute=currentRoute+(nextNode,)

            #remove it from the new remaining tuple
            newRemaining=currentRemaining[:n]+currentRemaining[n+1:]

            #recurse
            tryRoutes(newCurrentTime, newCurrentRoute, newRemaining)

#the routes all start at home, with all the locations remaining
start=time.clock()
tryRoutes(0, (home,), tuple(locations))
finish=time.clock()

print("\nThe final route is:\n")

#print the final route
for loc in shortestRoute: print(loc.name)

#print the final trip time
print("\nThe travelling will take "+str(shortestTime)+" mins")

print("Execution took {0} seconds".format(finish-start))

input("press enter to exit")
