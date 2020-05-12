"""

Gather data about tweet engagement over time.

"""

# Copyright (c) 2020 Ben Zimmer. All rights reserved.

from typing import List, Tuple
from datetime import datetime
import json
import os
import pickle
import dateutil
import pytz

import pandas as pd
import tweepy

import plot


CREDS_FILENAME = "creds.json"
USER_IDS_FILENAME = "userids.txt"
DATA_DIRNAME = "data"
TWEETS_FILENAME = "tweets.pkl"

TWEET_COUNT = 100
DO_PLOT = True  # for convenience

DATETIME_FORMAT = "%Y%m%d%H%M%S"
LOCAL_TIMEZONE = pytz.timezone("America/Chicago")


def main():
    """main program"""
    # pylint: disable=invalid-name

    # load credentials and user ids
    with open(CREDS_FILENAME) as creds_file:
        creds = json.load(creds_file)

    with open(USER_IDS_FILENAME) as userids_file:
        user_ids = userids_file.readlines()
        user_ids = [x.rstrip() for x in user_ids]

    auth = tweepy.OAuthHandler(
        creds["consumer_api"], creds["consumer_api_secret"])
    auth.set_access_token(
        creds["access_token"], creds["access_token_secret"])
    api = tweepy.API(
        auth,
        wait_on_rate_limit=True,
        wait_on_rate_limit_notify=True)

    # api.verify_credentials()

    # ~~~~ download ~~~~

    for idx, user_id in enumerate(user_ids):
        print(idx + 1, "/", len(user_ids), user_id)

        # collect status objects for offline processing
        query_time = datetime.now()
        cursor = tweepy.Cursor(api.user_timeline, id=user_id)

        tweets = []
        for status in cursor.items(TWEET_COUNT):
            tweets.append(status)

        datetime_str = query_time.strftime(DATETIME_FORMAT)

        with open(
                os.path.join(DATA_DIRNAME, user_id + "." + datetime_str + ".pkl"),
                "wb") as pickle_file:
            pickle.dump(tweets, pickle_file)

    # ~~~~ analyze ~~~~

    # build dataframe of tweets by time
    pickle_filenames = [x for x in os.listdir(DATA_DIRNAME) if x.endswith(".pkl")]

    dfs = []
    for pickle_filename in pickle_filenames:
        df = load_tweets(os.path.join(DATA_DIRNAME, pickle_filename))
        # add a column for the datetime of the pull
        _, datetime_str, _ = pickle_filename.split(".")
        datetime_obj = datetime.strptime(datetime_str, DATETIME_FORMAT)
        datetime_obj = LOCAL_TIMEZONE.localize(datetime_obj)
        df.insert(0, "query_datetime", datetime_obj)
        dfs.append(df)

    tweets_df = pd.concat(dfs)

    with open(TWEETS_FILENAME, "wb") as pickle_file:
        pickle.dump(tweets_df, pickle_file)

    # ~~~~ show API usage
    print("API usage:")
    limits = usage(api.rate_limit_status())
    for name, info in limits:
        print(
            name,
            info["remaining"], "/", info["limit"],
            "\t",
            datetime.fromtimestamp(info["reset"]).strftime('%Y-%m-%d %H:%M:%S')
        )
    print()

    # ~~~~ plot
    if DO_PLOT:
        plot.main()


def load_tweets(filename: str) -> pd.DataFrame:
    """load tweets from a pickle file into a dataframe"""

    with open(filename, "rb") as pickle_file:
        tweets = pickle.load(pickle_file)

    rows = []

    for tweet in tweets:
        tweet_json = tweet._json
        # print(json.dumps(tweet_json, indent=4))

        tweet_id = tweet_json["id"]
        tweet_datetime = dateutil.parser.parse(tweet_json["created_at"])
        tweet_datetime = tweet_datetime.astimezone(LOCAL_TIMEZONE)
        user = tweet_json["user"]["screen_name"]
        text = tweet_json["text"]
        is_quote_status = tweet_json["is_quote_status"]
        retweets = tweet_json["retweet_count"]
        likes = tweet_json["favorite_count"]

        # quoted status stuff
        # the logic here is tricky, so we'll initialize these up front

        quoted_tweet = None
        quoted_user = None
        quoted_text = None
        quoted_retweets = None
        quoted_likes = None

        if (
                is_quote_status and
                ("quoted_status" in tweet_json or "retweeted_status" in tweet_json)
                ):

            quoted_tweet = tweet_json["id"]
            if tweet_json.get("quoted_status") is not None:
                quoted_status = tweet_json["quoted_status"]
                # this works sometimes
                # quoted_status = tweet_json["retweeted_status"]["quoted_status"]
                quoted_user = quoted_status["user"]["screen_name"]
                quoted_text = quoted_status["text"]
                quoted_retweets = quoted_status["retweet_count"]
                quoted_likes = quoted_status["favorite_count"]

        if "retweeted_status" in tweet_json:
            is_retweet_status = True
            retweeted_status = tweet_json["retweeted_status"]
            retweeted_tweet = retweeted_status["id"]
            retweeted_user = retweeted_status["user"]["screen_name"]
            retweeted_text = retweeted_status["text"]
            retweeted_retweets = retweeted_status["retweet_count"]
            retweeted_likes = retweeted_status["favorite_count"]
        else:
            is_retweet_status = False
            retweeted_tweet = None
            retweeted_user = None
            retweeted_text = None
            retweeted_retweets = None
            retweeted_likes = None

        if tweet_json["in_reply_to_status_id"] is not None:
            is_reply = True
            reply_tweet = tweet_json["in_reply_to_status_id"]
            reply_user = tweet_json["in_reply_to_screen_name"]
        else:
            is_reply = False
            reply_tweet = None
            reply_user = None

        row = {
            "tweet": tweet_id,
            "tweet_datetime": tweet_datetime,
            "user": user,
            "text": text,
            "retweets": retweets,
            "likes": likes,

            "is_quote_status": is_quote_status,
            "quoted_tweet": quoted_tweet,
            "quoted_user": quoted_user,
            "quoted_text": quoted_text,
            "quoted_retweets": quoted_retweets,
            "quoted_likes": quoted_likes,

            "is_retweet_status": is_retweet_status,
            "retweeted_tweet": retweeted_tweet,
            "retweeted_user": retweeted_user,
            "retweeted_text": retweeted_text,
            "retweeted_retweets": retweeted_retweets,
            "retweeted_likes": retweeted_likes,
            "is_reply": is_reply,
            "reply_tweet": reply_tweet,
            "reply_user": reply_user
        }

        rows.append(row)

    return pd.DataFrame(rows)


def disp(row: dict) -> str:
    """display a tweet record"""
    # TODO: implement correctly
    # print("\ttweet:             ", tweet_id)
    # print("\ttweet_datetime:    ", tweet_datetime)
    # print("\tuser:              ", user)
    # print("\ttext:              ", text)
    # print("\tretweets:          ", retweets)
    # print("\tlikes:             ", likes)
    #
    # print("\tis_quote_status:   ", is_quote_status)
    # print("\tquoted_tweet:      ", quoted_tweet)
    # print("\tquoted_user:       ", quoted_user)
    # print("\tquoted_text:       ", quoted_text)
    # print("\tquoted_retweets:   ", quoted_retweets)
    # print("\tquoted_likes:      ", quoted_likes)
    #
    # print("\tis_retweet_status: ", is_retweet_status)
    # print("\tretweeted_tweet:   ", retweeted_tweet)
    # print("\tretweeted_user:    ", retweeted_user)
    # print("\tretweeted_text:    ", retweeted_text)
    # print("\tretweeted_retweets:", retweeted_retweets)
    # print("\tretweeted_likes:   ", retweeted_likes)
    #
    # print("\tis_reply:          ", is_reply)
    # print("\treply_tweet:       ", reply_tweet)
    # print("\treply_user:        ", reply_user)
    # print()
    return ""


def usage(data: dict) -> List[Tuple]:
    """find all of the API actions that have been used"""

    def flatten(x_dict: dict) -> list:
        """recursively flatten the dictionaries"""
        res = []
        for key, val in x_dict.items():
            if isinstance(val, dict):
                if "limit" in val:
                    res.append((key, val))
                else:
                    res.extend(flatten(val))
        return res

    limits = flatten(data)
    limits = sorted(limits, key=lambda x: x[0])
    limits = [
        (key, val) for key, val in limits
        if val["remaining"] < val["limit"]]

    return limits


if __name__ == "__main__":
    main()
