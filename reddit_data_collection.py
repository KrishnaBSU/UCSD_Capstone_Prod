"""
Program to get the comments about a specific subject from Reddit within a given data range and clean, process
the data and provide in a data frame.
"""

import pandas as pd
pd.options.mode.chained_assignment = None
#import numpy as np
from copy import deepcopy as deepcopy
import string
import datetime
import time
import contractions
import demoji
import nltk
from nltk.corpus import stopwords
from pmaw import PushshiftAPI
import praw
import re

# Reddit Key
import constants

reddit = praw.Reddit(
    client_id=constants.reddit_client_id,
    client_secret=constants.reddit_client_secret,
    user_agent=constants.reddit_user_agent
)

# Creating a pushshift API sub instance
api = PushshiftAPI()


# Get comments from reddit using pmaw and pushshift APIs
def get_comments(topic, start_time, end_time):
    comments_list = []
    api_praw = PushshiftAPI(praw=reddit)
    comments = api_praw.search_comments(q=topic, limit=1000, after=int(start_time), before=int(end_time))

    # Getting the Comment created time, Author and Comment body from the generator object.
    comment_list_exp = [[comment['created_utc'], comment['author'], comment['body']] for comment in comments]

    for comment in comment_list_exp:
        # Creating the data frame with comments.
        comments_list.append(comment[2])

    return pd.DataFrame(comments_list, columns=['comments'])


# Clean the data frame by removing punctuations, duplicate rows, emojis etc
def clean_df(df):
    # Removing Web links
    df['comments'] = df['comments'].apply(lambda x: re.sub(r"http\S+", "", x))

    # Fixing contractions like i'd
    df['comments'] = df['comments'].apply(lambda x: contractions.fix(x))

    # Lowercasing all the comments
    df['comments'] = df['comments'].apply(lambda x: str(x).lower())

    # Removing Punctuations
    punc_to_remove = string.punctuation + '\n'
    replace_punc = str.maketrans('', '', punc_to_remove)
    df['comments'] = df['comments'].apply(lambda x: x.translate(replace_punc))

    def replace_digits(x):
        y = ''
        for i in x:
            if i.isdigit():
                continue
            else:
                y = y + i
        return y

    # Removing Numbers
    df['comments'] = df.comments.apply(replace_digits)

    # Removing Extra Spaces
    df['comments'] = df['comments'].apply(lambda x: " ".join(x.split()))

    # Dropping any duplicate comments
    df = df.drop_duplicates()

    # Remove stop words
    nltk.download('stopwords')
    stop = stopwords.words('english')
    # Common comment seen when a particular comment is deleted. It doesnt add much value to the analysis.
    stop.append('deleted')
    df['comments'] = df['comments'].apply(lambda x: " ".join(x for x in x.split() if x not in stop))

    # Removing Emoticons
    EMOTICONS = {
        u":‑)": "Happy face or smiley",
        u":)": "Happy face or smiley",
        u":-]": "Happy face or smiey",
        u":]": "Happy face or smiley",
        u":-3": "Happy face smiley",
        u":3": "Happy face smiley",
        u":->": "Happy face smiley",
        u":>": "Happy face smiley",
        u"8-)": "Happy face smiley",
        u":o)": "Happy face smiley",
        u":-}": "Happy face smiley",
        u":}": "Happy face smiley",
        u":-)": "Happy face smiley",
        u":c)": "Happy face smiley",
        u":^)": "Happy face smiley",
        u"=]": "Happy face smiley",
        u":(": "Sad face smiley"
    }

    # Replacing Emoticons with respective text
    def convert_emoticons(text):
        for emot in EMOTICONS:
            #text = re.sub(u'(' + emot + ')', "_".join(EMOTICONS[emot].replace(",", "").split()), text)
            text = text.replace(emot, EMOTICONS[emot])
        return text
    df['comments'] = df['comments'].apply(convert_emoticons)

    # Replace Emojis with text
    def replace_emoji(str1):
        return demoji.replace_with_desc(str1, " ")

    df['comments'] = df['comments'].apply(replace_emoji)

    # Remove non ASCII Letters
    df['comments'] = df['comments'].apply(lambda x: x.encode("ascii", errors="ignore").decode())

    # Return the cleaned Data Frame
    return df


# Main method to get the topic details, date range and provide the cleaned data frame.
def get_clean_data(topic=None, from_date=None, to_date=None):
    #print("In Data Collection mode. Topic: {} , from_data: {}, to_date: {}".format(topic,from_date,to_date))
    if from_date is None or to_date is None:
        # Setting the time for the past day
        to_date = datetime.date.today()
        to_date = int(time.mktime(to_date.timetuple()))
        from_date = to_date - 86400
    else:
        # Converting string of YYYY-Month-Date format to Datetime Object
        to_date = datetime.date.fromisoformat(to_date)
        to_date = int(time.mktime(to_date.timetuple()))
        from_date = datetime.date.fromisoformat(from_date)
        from_date = int(time.mktime(from_date.timetuple()))

    # Setting the default topic as bitcoin
    if topic is None:
        topic = 'bitcoin'

    df_to_clean = get_comments(topic, from_date, to_date)
    df = deepcopy(df_to_clean)
    df = clean_df(df)
    return df
    #print(df_to_clean.head())
    #df_to_clean.to_csv('uncleaned.csv')
    #df.to_csv('cleaned.csv')


if __name__ == '__main__':
    df = get_clean_data('bitcoin', '2021-01-01', '2022-01-01')
    df.to_csv('2021_reddit_bitcoin.csv')