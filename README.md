# This is an example of basic video calling app like google meet using Python, Flask, Socket IO and HTML (jinja2).

## There is 2 project
1. Peer-2-Peer / One-2-One person meeting.
=> run code using python3 p2p.py 
The code releted files are in p2p.py backend and p2p.html frontend in template directory

2. Normal multiple people meeting video call
=> run code using python3 m2m.py 
The code releted files are in m2m.py backend and m2m.html frontend in template directory


## How to setup
step 1.  create python virtual environment
=> python3 -m virtualenv env (need to install virtualenv using "pip install virtualenv")
step 2. activate python virtual environment
=> source env/bin/activate in linux or mac and source env/Script/activate in windows
step 3. install required python libraries from requirements.txt
=> python3 -m pip install -r requirements.txt
step 4. run your code using python3
=> python3 m2m.py 

It will run in 5000 port as my code. better run in ngrok (https://ngrok.com/). It will work better on https.

## How to call or execute your code
1. for p2p.py - In browser directly call IP or domain for first person
example - https://ngrok-based-generated-domain.com
and for second person call #init page
example - https://ngrok-based-generated-domain.com/#init


2. for m2m.py - In browser directly call IP or domain for all users
In main page first create a meeeting link and you can click and open meeeting link in another tab from "Create a New Meeting" option. Either you can enter last meeting ID in "Join a Meeting" option.

It will open meeting in another tab , Enter your username for meeting and Join.. 
Based on each user internet speed and your system bandwidth and speed it may take some time to show videos of other users.

## Issue
Due to asynchronous code execution for other participant to in socket join. there is a loop. emit will not execute. i have added more time so it should execute well, but still if you will face issue increase time. Problem is actually i faced sometimes, If new user join meeting can see existing users but existing users cant see new added users. If you will face the issue that cant see new users. Just reconnect the meeting. This issue should not happen because i have tried to solve the issue. If you can find better solution please share me. You can write asynchronous code also for better performance. I am little bad in asynchronously code bcz of corontine error message in every small code part. 

