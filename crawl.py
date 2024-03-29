import networkx as nx
import twitter_network
import pymongo
import numpy as np
import matplotlib.pyplot as plt

##Jian Xin Zhou
##Social Media Data Minining
##@2019


screen_name="everythingapplepro"
twitter_api = twitter_network.oauth_login()

print("Fetching user info...")
try:
    friends_ids, followers_ids = twitter_network.get_friends_followers_ids(twitter_api, screen_name, friends_limit=5000, followers_limit=5000)
    reciprocal_friends_ids = list(set(friends_ids) & set(followers_ids))
    print("Information has been fetched.")
    print()

except:
    print("Failed to retrive user information.")
    print()


def getScreenName(users):
    output = ""
    p = twitter_network.get_user_profile(twitter_api, screen_names=None, user_ids=users)
    for user in p:
        output += (p[user]['name']) + " - " + str(int(p[user]['id'])) + " (" + str(int((p[user]['followers_count']))) + " followers), "
    output = ''.join(output)[:-2]

    return output

def save_to_mongo(data, mongo_db, mongo_db_coll, **mongo_conn_kw):
    
    client = pymongo.MongoClient(**mongo_conn_kw)
    db = client[mongo_db]
    coll = db[mongo_db_coll]
    
    try:
        return coll.insert_many(data)
    except:
        return coll.insert_one(data)

def load_from_mongo(mongo_db, mongo_db_coll, return_cursor=False,criteria=None, projection=None, **mongo_conn_kw):
    client = pymongo.MongoClient(**mongo_conn_kw)
    db = client[mongo_db]
    coll = db[mongo_db_coll]
    
    if criteria is None:
        criteria = {}
    
    if projection is None:
        cursor = coll.find(criteria)
    else:
        cursor = coll.find(criteria, projection)
    
    if return_cursor:
        return cursor
    else:
        return [ item for item in cursor ]


def pickFiveMostPopular(users):
    unsortedList_by_follower_count = []
    sortedList_by_follower_count = []

    try:
        p = twitter_network.get_user_profile(twitter_api, screen_names=None, user_ids=users)
        
        for user in users:
            unsortedList_by_follower_count.append(tuple((user, p[user]['followers_count'])))

        sortedList_by_follower_count = sorted(unsortedList_by_follower_count, key = lambda x : x[1], reverse=True)
        top5 = [x[0] for x in sortedList_by_follower_count[:5]]

    except:
        return []

    return top5


def crawl_followers(twitter_api, screen_name, limit=1000000, depth=5, **mongo_conn_kw):
   
    seed_id = str(twitter_api.users.show(screen_name=screen_name)['id'])
    next_queue = pickFiveMostPopular(twitter_network.get_reciprocal_friends(twitter_api, screen_name=screen_name, friends_limit=0, followers_limit=limit))

    G.add_node(seed_id)
    for node in next_queue:
        G.add_node(node)
        G.add_edge(seed_id, node)
    
    print("The five most popular people who also mutually follow " + screen_name + " are: " + getScreenName(next_queue))
    print()
    
    save_to_mongo({'followers' : [ _id for _id in next_queue ]}, 'followers_crawl', '{0}-follower_ids'.format(seed_id), **mongo_conn_kw)
    d = 1
    while d < depth:
        d += 1
        (queue, next_queue) = (next_queue, [])
        for fid in queue:
            _, follower_ids = twitter_network.get_friends_followers_ids(twitter_api, user_id=fid,friends_limit=0, followers_limit=5000)
            
        #    draw node here. fetch data from mongoDB and draw edges if they are a tuple.

            try:
                new_follower_ids = pickFiveMostPopular(follower_ids) #Pick 5

                for node in new_follower_ids:
                    G.add_node(node)
                    G.add_edge(fid, node)

                print("\nThe five most popular people who also mutually follow " + str(int(fid)) + " are: " + getScreenName(new_follower_ids))
                print()

                save_to_mongo({'followers' : [ _id for _id in new_follower_ids ]},'followers_crawl', '{0}-new_follower_ids'.format(fid))
            
                next_queue += new_follower_ids

            except:
                print("\nAn unexpected exception happened. Possibly no reciprocal friends!")
                print()

                    
    print("Done crawling!")
    print()

    pos = nx.spring_layout(G,scale=3)
    nx.draw(G,pos,font_size=5, node_size = 15, with_labels=True)
    plt.savefig(screen_name+"_twitter_graph.png")



def delete_from_mongo(mongo_db, mongo_db_coll, return_cursor=False, criteria=None, projection=None, **mongo_conn_kw):
    client = pymongo.MongoClient(**mongo_conn_kw)
    db = client[mongo_db]
    coll = db[mongo_db_coll]

    try:
        coll.drop()
        print("\nColumn dropping success!")
    except:
        print("\nColumn dropping failure!")


G = nx.Graph()
crawl_followers(twitter_api, screen_name, limit=100000, depth=3)
load_from_mongo('followers_crawl', 'new_follower_ids', return_cursor=False,criteria=None, projection=None)

print("\nNumber of nodes: " + str(G.number_of_nodes()))
print("\nNodes available:")
print( G.adj)
print()
print("\nNumber of edges: " + str(G.number_of_edges()))
print("\nAverage shortest path length: " + str(nx.average_shortest_path_length(G)))
print("\nAverage diameter: " + str(nx.diameter(G,e=None,usebounds=False)))
