# UCSD_Capstone_Prod

**Production Repo for Capstone**

1. Goal of the current capstone project is to predict the sentiment(Positive or Negative) of 'bitcoin' from the comments on Reddit. Project is broadly divided into 3 main components:

2. **Comments collection from Reddit** - This is done through _reddit_data_collection.py_, where we use Pushift API through PMAW mode to collect the comments and then perform data cleaning on the data to be able to use with the Bert Model from HuggingFace.

3. **Sentiment Prediction** - This is accomplished through the _CosmosDB_Senti_Update.py_, where the data from the reddit is consumed and produces a list with negative or positive sentiment for each comment. The comments along with the predictions and the number of possitive/negative comments for each day are saved to CosmosDB through the use of _CosmosDB.py_ file. HuggingFace BERT Model was pre-trained with the data from IMDB data base and then saved. We will continue to use this pre-trained and saved model as training it for data everyday is very resource intensive. Example data downloaded from cosmosdb are 'bitcoin_pred_cosmosdb.csv' with the total predictions for each day(columns namely date, positive count, negative count) and 'bitcoin_comments_cosmosdb.csv' with individual comments(columns namely date, id(cosmosdb id), topic,  comments, sentiment) and what the prediction for that comment was(0->negative, 1->positive).

4. **Web Interface to Plot the data and take the input** - This is accomplished through the _app.py_ file, which will provide a web interface for the user to the provide the dates between which the user is looking for the sentiment analysis dashboard. Using these dates, we will fetch the data from Azure CosmosDB data base through _CosmosDB.py_ and then plot the data trend on the web interface. 

5. Above components are dockerized into two different docker modules: one for data collection, sentiment prediction and update the data base with those predictions. Other to provide the web interface to the user and access the data from the CosmosDB data base and plot the sentiment trend for 'bitcoin'.

6. Both the dockers are hosted on Azure Cloud and the user web interface can be accessed through: _sentipred1.a0gvdsgaezadgfdx.eastus2.azurecontainer.io:5000_ . Please note the FQDN change everytime the container is started for security reasons(eg: to avoid web spoofing).
