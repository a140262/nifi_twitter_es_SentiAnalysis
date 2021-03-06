'''
Created on Oct 8, 2015

@author: mentzera
'''

import json
import boto3
import twitter_to_es

s3 = boto3.client('s3')

def lambda_handler(event, context):
    print("Received event: " + json.dumps(event, indent=2))

    # Get the object from the event and show its content type
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    twitter_user_key = "client/twitter-ids.json"

    # Getting twitter s3 object
    try:
        response = s3.get_object(Bucket=bucket, Key=key)

    except Exception as e:
        print(e)
        print('Error getting object {} from bucket {}. Make sure they exist and your bucket is in the same region as this function.'.format(key, bucket))
        raise e

    # Getting customer twitter handle object
    try:
        handlelist = s3.get_object(Bucket=bucket, Key=twitter_user_key)

    except Exception as e:
        print(e)
        print(
        'Error getting object {} from bucket {}. Make sure they exist and your bucket is in the same region as this function.'.format(
            twitter_user_key, bucket))
        raise e

    # Parse s3 object content (JSON)
    try:
        s3_file_content = response['Body'].read()
        s3_twitter_user_content = handlelist['Body'].read()

        #clean trailing comma
        if s3_file_content.endswith('\n,'):
            s3_file_content = s3_file_content[:-2]
        tweets_str = '['+s3_file_content+']'
        tweets = json.loads(tweets_str)

        handlelist = json.loads(s3_twitter_user_content)

    except Exception as e:
        print(e)
        print('Error loading json from object {} in bucket {}'.format(key, bucket))
        raise e
    
    # Load data into ES
    try:
        twitter_to_es.load(tweets,handlelist)

    except Exception as e:
        print(e)
        print('Error loading data into ElasticSearch')
        raise e

