import networkx
import twitter_network


twitter_api = twitter_network.oauth_login()
print("Fetching user info...")
try:
    friends_ids, followers_ids = twitter_network.get_friends_followers_ids(twitter_api, screen_name="everyapplepro", friends_limit=5000, followers_limit=5000)
    reciprocal_friends_ids = twitter_network.get_reciprocal_friends(twitter_api, screen_name="everyapplepro", friends_limit=5000, followers_limit=5000)
    print("Information has been fetched.")

except:
    print("Failed to retrive user information.")


def pickFiveMostPopular(x):
    for user in x:
        print(user)
        print(1)


pickFiveMostPopular(reciprocal_friends_ids)




