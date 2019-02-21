import networkx
import twitter_network

screen_name="petercougz"
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
    str = ""
    p = twitter_network.get_user_profile(twitter_api, screen_names=None, user_ids=users)
    for user in p:
        str += (p[user]['name']) + ", "
    str = ''.join(str)[:-2]

    return str


def pickFiveMostPopular(users):
    unsortedList_by_follower_count = []
    sortedList_by_follower_count = []
    p = twitter_network.get_user_profile(twitter_api, screen_names=None, user_ids=users)
    for user in users:
        unsortedList_by_follower_count.append(tuple((user, p[user]['followers_count'])))
    sortedList_by_follower_count = sorted(unsortedList_by_follower_count, key = lambda x : x[1], reverse=True)
    top5 = [x[0] for x in sortedList_by_follower_count[:5]]
    print("\nThe five most popular people who follow " + screen_name + " are: " + getScreenName(top5))

    return top5


pickFiveMostPopular(reciprocal_friends_ids)
