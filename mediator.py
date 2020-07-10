import pika
import json
import os
import collections
import ast
import requests
from datetime import datetime,timedelta
from dotenv import load_dotenv

load_dotenv()
HOSTURL = os.getenv("HOST_URL")
RABBITMQ_USERNAME = os.getenv("RABBITMQ_USERNAME")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD")
MAIN_SERVER = os.getenv("MAIN_SERVER")

features_pack = {}
frame_rate = 0.5

'''------------------------------------------------
        Finding unique persons from the video
--------------------------------------------------'''
#todo
#find the unique person in video (traverse sequentially)
##find the similarity between 2 frames based on labels
##check the similarity betwen them using box sizes
#Save into db twice at 2 different locations (Whole video_output and unique_person)
def UniquePersonSearch(video_id, object_data,timestamp):
    
    #Saving all the frames into the db
    # db.features.insert_many(video_output)

    #converting to 3d-Array
    array3d=[]
    array3d = [collections.Counter([ str(feature['labels']+feature['colors'])  for feature in data['persons'] if feature is not []]) for data in object_data]
    # print(array3d)
    unique_person = []

    #Finding the Unique ones
    for i in range(len(array3d)-1):
        person = array3d[i]-array3d[i+1]
        # print(person)
        if person:
            for k in person.keys() :
                unpack = ast.literal_eval(k)
                for _ in range(person[k]):
                    new_timestamp = timestamp + timedelta(seconds=i*frame_rate)
                    unique_person.append({'video_id': video_id, 'last_seen': { "date": str(new_timestamp.date()), "time": new_timestamp.strftime("%X") }, 'labels': unpack[:(len(unpack)//2)], 'colors': unpack[(len(unpack)//2):]})
    new_timestamp = timestamp + timedelta(seconds=(i+1)*frame_rate)
    for k in array3d[len(array3d)-1].keys():
        unpack = ast.literal_eval(k)
        for _ in range(array3d[len(array3d)-1][k]):
            unique_person.append({'video_id': video_id, "date": str(new_timestamp.date()), "time": new_timestamp.strftime("%X") , 'labels': unpack[:(len(unpack)//2)], 'colors': unpack[(len(unpack)//2):]})
    
    #Send to the main Server(gearstalk_baxkend1)
    print(unique_person)
    r = requests.post("https://33a7c36c8710.ngrok.io/process/FindUnique", data=json.dumps({"video_id": video_id, "unique_person":unique_person}) )

    return "Your video is processed"



#supporting functions
def FindUnique(data):
    data = json.loads(data)
    video_id = data['video_id']
    frame_sec = data['frame_sec']
    timestamp = json.loads(data['timestamp'])
    total_frames = int(data['total_frames'])
    frame_details = json.loads(data['frame_details'])
    message = "Video Processing not over!!"
    new_timestamp = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f")
    
    if video_id in features_pack.keys():
        features_pack[video_id][int(frame_sec//frame_rate)] =  {"frame_sec":frame_sec,"persons":frame_details}
    else:
        arr = [None]*total_frames
        features_pack[video_id] =  arr
        features_pack[video_id][int(frame_sec//frame_rate)] =  {"frame_sec":frame_sec,"persons":frame_details}
    
    if None not in features_pack[video_id]:
        video_output = features_pack.pop(video_id)
        # print(video_output)
        message = UniquePersonSearch(video_id,video_output,new_timestamp)



'''-----------------------------------------
        Consuming packets from rabbitmq
        and adding it into a subprocess
------------------------------------------'''

def rabbitmq_consumer():
    credentials = pika.PlainCredentials('test', 'test')

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost', credentials=credentials))                       #load_balancer url/ip in (host)
    channel = connection.channel()

    channel.queue_declare(queue='frame_output')

    def callback(ch, method, properties, body):
            print(" [x] Received ")
            FindUnique(body)


    channel.basic_consume(
        queue='frame_output', on_message_callback=callback, auto_ack=True)

    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()



if __name__ == '__main__':
    # app.run(host="0.0.0.0", debug=True, use_reloader=True, threaded=True)
    try:
        rabbitmq_consumer()
    except KeyboardInterrupt:
        quit = True