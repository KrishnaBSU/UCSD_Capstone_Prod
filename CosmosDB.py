import pandas as pd
import azure.cosmos.cosmos_client as cosmos_client
import constants
# import json
import uuid
# import azure.cosmos.errors as errors
# import azure.cosmos.documents as documents
# import azure.cosmos.http_constants as http_constants

# Initialize the Cosmos client
config = constants.cosmos_config
# Create the cosmos client
client = cosmos_client.CosmosClient(url=config["endpoint"], credential={"masterKey": config["primarykey"]})
print("Cosmos DB Client successfully instantiated.")
# Database initialization
database = client.get_database_client('commentsdb')


def db_connect(container_id):
    container = None
    # if find_container(database, 'comments_tab'):
    if find_container(database, container_id):
        container = database.get_container_client(container_id)
    else:
        print("Need to create a container now")
    return container


def find_container(db, id):
    containers = list(db.query_containers(
        {
            "query": "SELECT * FROM r WHERE r.id=@id",
            "parameters": [
                {"name": "@id", "value": id}
            ]
        }
    ))

    if len(containers) > 0:
        print('Container with id \'{0}\' was found'.format(id))
        return 1
    else:
        print('No container with id \'{0}\' was found'.format(id))
        return 0


def insert_items(container_id, df, topic):
    container = db_connect(container_id)
    df['topic'] = topic
    if container_id == "comments_tab":
        # Reset index - creates a column called 'index'
        df = df.reset_index()
        df.columns = ['date', 'Pos', 'Neg', 'topic']
        # Converting datetime time object to int.
        df['date'] = pd.to_numeric(df['date'])
        df = df.applymap(str)
        # df = pd.DataFrame({'date':['1','2','3'],'Pos':['1','2','3'], 'Neg':['1','2','3'], 'topic':['1','1','1']})
        id_list = ['item' + str(uuid.uuid4()) for i in range(0, len(df))]
        df['id'] = id_list
        df = df[['id', 'topic', 'date', 'Pos', 'Neg']]
        # Write rows of a pandas DataFrame as items to the Database Container
        for i in range(0, df.shape[0]):
            # create a dictionary for the selected row
            data_dict = dict(df.iloc[i, :])
            #print(data_dict)
            container.upsert_item(data_dict)
        print('Records inserted successfully.')
    elif container_id == "comments_details_tab":
        df = df.reset_index()
        df.columns = ['date', 'comments', 'sentiment', 'topic']
        # Converting datetime time object to int.
        df['date'] = pd.to_numeric(df['date'])
        df = df.applymap(str)
        # df = pd.DataFrame({'date':['1','2','3'],'Pos':['1','2','3'], 'Neg':['1','2','3'], 'topic':['1','1','1']})
        id_list = ['item' + str(uuid.uuid4()) for i in range(0, len(df))]
        df['id'] = id_list
        df = df[['id', 'topic', 'date', 'comments', 'sentiment']]
        # Write rows of a pandas DataFrame as items to the Database Container
        for i in range(0, df.shape[0]):
            # create a dictionary for the selected row
            data_dict = dict(df.iloc[i, :])
            #print(data_dict)
            container.upsert_item(data_dict)
        print('Records inserted successfully.')
    else:
        print("unknown container_id: {} . Can't insert items.".format(container_id))



def read_items(container_l, topic):
    # QUERY = 'SELECT * FROM mycontainer c WHERE c.topic = "bitcoin"'
    QUERY = 'SELECT c.date,c.Pos,c.Neg FROM mycontainer c WHERE c.topic = "' + topic + '"'
    print(QUERY)

    # Retrieving the items
    results = container_l.query_items(
        query=QUERY, enable_cross_partition_query=True
    )
    items = [item for item in results]
    #print(items)
    return pd.DataFrame(items)


def get_db_items(container_id, topic):
    container = db_connect(container_id)
    if container:
        df_db = read_items(container, topic)
        if len(df_db) > 0:
            # Cleaning up the data frame to be used for prediction purpose
            # Reducing the Time stamp sensitivity to 10 digits.
            df_db['date'] = df_db['date'].apply(lambda x: x[:10])
            # Converting date to datetime object and set it as the index
            df_db['date'] = pd.to_datetime(df_db['date'], unit='s')
            df_db = df_db.set_index('date')
            df_db['Pos'] = df_db['Pos'].astype(int)
            df_db['Neg'] = df_db['Neg'].astype(int)
            # print("After db : {}".format(df_db))
            return df_db
        else:
            print("No data for topic: {} present in db".format(topic))
            return pd.DataFrame()
    else:
        return pd.DataFrame()


if __name__ == '__main__':
    df_p = pd.read_pickle('bitcoin.pkl')
    df_db = get_db_items("comments_tab", "bitcoin")
    if len(df_db) == 0:
        print("Empty DataFrame")
    else:
        print("Initial Data: {}".format(df_db))
    insert_items("comments_tab", df_p, "bitcoin")

    df_db = get_db_items("comments_tab", "bitcoin")
    if len(df_db) == 0:
        print("Empty DataFrame")
    else:
        print("Final Data: {}".format(df_db))
