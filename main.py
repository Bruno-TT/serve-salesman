import csv
import googlemaps
import datetime
import math
import time
from threading import Thread

mode="bicycling"
maxDepth=2 #experiment with 0, 1 and 2. 3+ may be buggy. 0 is safest but slowest.
#error messages will print for too high depth values.
DEBUG=True
ALLOW_CONSECUTIVE_IDENTICAL_AUDITS=False

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
    l=Location(n, location[0], location[1])
    
    #add the address to the addresses array
    addresses.append(l.address)

    #add the location to the locations array
    locations.append(l)

#inputting the addresses
startAddress = input("please input your starting postcode\n")
endAddress = input("please input your finishing postcode\n")
print("\n")

#initialising the start/end point location objects.
#they have negative numbers because they're at the end of the array, and thus can be accessed with a negative subscript
start=Location(-2, "starting location\n", startAddress)
end=Location(-1, "\nfinishing location", endAddress)

#adding them to addresses array. It's added as we need it to be in the API request.
addresses.append(startAddress)
addresses.append(endAddress)

#assume all journeys take place at midday tomorrow, to simplify things.
MIDDAY_TOMORROW=datetime.datetime(datetime.datetime.now().year, datetime.datetime.now().month, datetime.datetime.now().day+1, 12)

#we temporarily add start and end to the locations array, so make the following loop work nicely
locations.append(start)
locations.append(end)

#make the distance matrix requests
#TODO: make less, larger requests
travelTimes={}

#iterate through each location, taking turns to consider each one the origin of each hop
for origin in locations:

    #make the API request
    fromTimes=gmaps.distance_matrix(origins=[origin.address], destinations=addresses, mode=mode, departure_time=MIDDAY_TOMORROW)
    
    #iterating through the destinations
    for destination in locations:

        #the data is given to us in a disgusting format. This line is the one that actually unpicks the format and turns it into a time, and then
        #stores it in a dictionary with each journey combination stored with the points in a tuple as the key (see routeTime definition)
        try:
            travelTimes[(origin, destination)]=fromTimes["rows"][0]["elements"][destination.number]["duration"]["value"]/60
        except:
            print(origin.name, destination.name)
            input("")
            class InvalidData(Exception):pass
            raise InvalidData

#then we remove them again, as it's no longer beneficial to consider the start/end points as normal locations
locations.remove(start)
locations.remove(end)

#lambda wrapper for finding the travel time between 2 places (ie. accessing them from the travelTimes dictionary)
routeTime=lambda from_, to: travelTimes[(from_, to)]

#initialising the result variables

#upper bound, so it starts at infinity
shortestTime=math.inf

#gets overwritten during first pass
shortestRoute=None

#main recursive depth first search route finder
#this function calls itself multiple times
def tryRoutes(currentTime, currentRoute, currentRemaining, depth):

    #globalising result variables
    global shortestTime, shortestRoute

    #if we've finished a route
    if currentRemaining==():
        
        #go home at the end and update the total time
        totalTime=currentTime+routeTime(currentRoute[-1], end)

        #if it's the new fastest route then record it
        if totalTime<shortestTime:
            shortestTime=totalTime
            shortestRoute=currentRoute+(end,)
            if DEBUG:
                print("new shortest route found! Travel time: {0}".format(str(shortestTime)))
    
    #if this route (unfinished!) is already slower than the fastest route then don't pursue it any further.
    #the idea behind this line is that for any partial journey, a lower bound on the total time can be established by
    #adding the total time spent and the time to go straight to the end. If this is greater than the real total time
    #for another journey, then this partial route is already slower than another complete route, so we stop
    #pursuing all routes beginning with the partial route.
    elif currentTime+routeTime(currentRoute[-1], end)>shortestTime:
        pass
    
    #otherwise, pursue all the remaining neighbours
    else:

        if depth<=maxDepth:
            threads=[]
            #for each possible next node
            for n,nextNode in enumerate(currentRemaining):

                if ALLOW_CONSECUTIVE_IDENTICAL_AUDITS or nextNode.name!=currentRoute[-1].name:

                    #calculate the new trip time
                    newCurrentTime=currentTime+routeTime(currentRoute[-1], nextNode)

                    #add it to the new route
                    newCurrentRoute=currentRoute+(nextNode,)

                    #remove it from the new remaining tuple
                    newRemaining=currentRemaining[:n]+currentRemaining[n+1:]

                    newDepth=depth+1

                    #recurse
                    thread = Thread(target=tryRoutes,args=(newCurrentTime, newCurrentRoute, newRemaining, newDepth))
                    thread.start()
                    threads.append(thread)

            for thread in threads:
                thread.join()
            return
        else:
            for n,nextNode in enumerate(currentRemaining):

                if ALLOW_CONSECUTIVE_IDENTICAL_AUDITS or nextNode.name!=currentRoute[-1].name:

                    #calculate the new trip time
                    newCurrentTime=currentTime+routeTime(currentRoute[-1], nextNode)

                    #add it to the new route
                    newCurrentRoute=currentRoute+(nextNode,)

                    #remove it from the new remaining tuple
                    newRemaining=currentRemaining[:n]+currentRemaining[n+1:]

                    newDepth=depth+1

                    #recurse
                    tryRoutes(newCurrentTime, newCurrentRoute, newRemaining, newDepth)

#the routes all start at home, with all the locations remaining
print("Please wait, processing. The program will take longer with more points.")
start_time=time.perf_counter()
tryRoutes(0, (start,), tuple(locations), 1)
end_time=time.perf_counter()

print("\nThe final route is:\n")

#output file
output_file=open("recent.txt", "w")

#print the final route
for loc in shortestRoute:
    print(loc.name)
    output_file.write(loc.name+"\n")


print("\nThe travelling will take "+str(shortestTime)+" mins")
output_file.write("The travelling will take "+str(shortestTime)+" mins")

print("Execution took {0} seconds".format(end_time-start_time))

output_file.close()
input("press enter to exit")
