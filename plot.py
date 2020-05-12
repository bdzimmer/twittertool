"""

Plot tweet engagement over time.

"""

# Copyright (c) 2020 Ben Zimmer. All rights reserved.

from datetime import datetime
from datetime import date
import pickle
import pytz

import pandas as pd
import plotly.express as px


TWEETS_FILENAME = "tweets.pkl"
LOCAL_TIMEZONE = pytz.timezone("America/Chicago")


def main():
    """main program"""
    # pylint: disable=invalid-name

    with open(TWEETS_FILENAME, "rb") as pickle_file:
        df = pickle.load(pickle_file)

    df = df.sort_values("query_datetime")

    # ~~~~ create and concat "initial" tweet rows
    initial_tweets = df.groupby("tweet").first().reset_index()

    print("unique tweets:", len(initial_tweets))

    # set query_datetime to tweet_datetime to mark the origin of the tweet
    initial_tweets["query_datetime"] = initial_tweets["tweet_datetime"]

    # set retweet and like counts to zero
    # TODO: reset other counts if not none
    initial_tweets["retweets"] = 0
    initial_tweets["likes"] = 0

    df = pd.concat([initial_tweets, df])

    df = df.sort_values("query_datetime")
    df["summary"] = df["user"] + "<br />" + df["text"] + "<br />" + df["tweet_datetime"].astype(str)
    df["engagements"] = df["likes"] + df["retweets"]

    # filter
    print("rows before filter:", len(df))
    today_midnight = datetime.combine(
        date.today(), datetime.min.time())
    today_midnight = LOCAL_TIMEZONE.localize(today_midnight)

    print("filtering tweets and queries after:", today_midnight)

    df = df.loc[df["query_datetime"] > today_midnight]
    df = df.loc[df["tweet_datetime"] > today_midnight]

    print("removing replies")
    df = df.loc[~df["is_reply"]]

    print("rows after filter:", len(df))

    # get rid of timezone information because plotly always plots UTC
    df["query_datetime"] = df["query_datetime"].map(lambda x: x.replace(tzinfo=None))
    df["tweet_datetime"] = df["tweet_datetime"].map(lambda x: x.replace(tzinfo=None))

    # fig = go.Figure(
    #     data=[
    #         go.Scatter(
    #             x=df["query_datetime"],
    #             y=df["likes"],
    #             mode="markers",
    #             text=df["user"] + " " + df["text"]
    #         )
    #     ],
    #     layout=go.Layout(title="TWITTERTOOL")
    # )

    fig = px.line(
        df,
        x="query_datetime",
        y="likes",
        color="user",
        line_group="tweet",
        hover_name="summary").update_traces(
            mode="lines+markers")

    fig.show()


if __name__ == "__main__":
    main()
