#!/usr/bin/env python3


"""
################################################################################
#                                                                              #
# runnotify.py                                                                 #
#                                                                              #
# This script is used to monitor a given script and log events such as         #
# starting and stopping of the script, and any crashes or errors that occur.   #
# The script takes one argument, which is the name of the script to be         #
# monitored                                                                    #
# (e.g. script_name.py).                                                       #
#                                                                              #
# Proper Usage:                                                                #
#     python3 runnotify.py script_name.py                                      #
#                                                                              #
# You can also check yourself manually if sript runnig via:                    #
# ps -e | grep myscriptname.py                                                 #
# Author: JackieTreehorn                                                     #
#                                                                              #
################################################################################
"""


import datetime
import os
import psutil
import subprocess
import traceback
import smtplib
import time
import argparse
#import shlex


parser = argparse.ArgumentParser(description="Monitoring script for a given python script")
parser.add_argument("script_name", help="The name of the script to be monitored")
args = parser.parse_args()


# Configuration
#script_name = shlex.quote(args.script_name)  # using shlex to parse any special characters
script_name = args.script_name 
print(f"\n* Script Name: {script_name}")

# derive the path from the script name
#script_path = shlex.quote(os.path.abspath(script_name))
script_path = os.path.abspath(script_name)
print(f"* Script Path: {script_path}")

email_user = "sender@email.com"
email_password = "asdfasdfasdf"
to_email = "receiver@mail.com"
botlog = "3cqsbot.log"


# function - Script running check
def script_running(script_name, script_path):
    try:
        # Iterate through the process list and find a match for the script_path
        for proc in psutil.process_iter():
            try:
                open_files = [f.path for f in proc.open_files()]
                if proc.name() == "Python" and script_path in open_files:
                    print("\n---> Matched paths in proc.open_files <---\n{}".format('\n'.join(open_files)))
                    print(f"\n---> The script '{script_name}' is already running with PID '{proc.pid}' <---\n* Script Path: '{script_path}'")
                    log_it(f"---> The script '{script_name}' is already running with PID '{proc.pid}' <---\n* Script Path: '{script_path}'")
                    return True
            except (psutil.AccessDenied, psutil.ZombieProcess, psutil.NoSuchProcess, psutil.Error):
                pass

        print(f"\n---> The script '{script_name}' is NOT running <---\n")
        log_it(f"---> The script '{script_name}' is NOT running <---")
        return False
    
    except Exception:
        traceback.print_exc()
        log_it(f"{traceback.print_exc()}")
        return False


# function - loggit
def log_it(entry):
    log = "runnotify.log"
    log_file = open(log, "a")
    log_file.write(f"{datetime.datetime.now()} {entry}\n")
    log_file.close()
    

# function - email
def send_email(subject, body):
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(email_user, email_password)
            msg = f"Subject: {subject}\n\n{body}"
            server.sendmail(email_user, to_email, msg)
            server.quit()
            print(f"Email sent with subject: {subject}...")
            log_it(f"Email sent with subject: {subject}")
    except smtplib.SMTPException as e:
        print(f"SMTP Error: {e}...")
        log_it(f"SMTP Error: {e}")


#######################   MAIN    ###########################

# putting loop in a 'try' block to catch this script's crashes
try:
    while True: 
        try:
            if not script_running(script_name, script_path):
                subprocess.Popen(["python3", script_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                print(f"{script_name} Started...")
                log_it(f"Success: Started Script")
                subject = f"SUCCESS:{script_name} script has started/restarted successfully"
                body = f"The {script_name} script has started/restarted successfully"
                send_email(subject, body)
            else:
                print(f"{script_name} already running, re-check in 60sec...")
        except subprocess.CalledProcessError as e:
            print(f"{script_name} Crash...")
            log_it(f"Crash - Error: {e}")
            subject = f"CRASH:{script_name} script has crashed"
            body = f"The {script_name} script has crashed.\n\nTraceback:\n{traceback.format_exc()}"
            send_email(subject, body)
        except Exception as e:
            print(f"{script_name} Exception...")
            log_it(f"Exception - Error: {e}")
            subject = f"ERROR:{script_name} script has error"
            body = f"The {script_name} script has error.\n\nTraceback:\n{traceback.format_exc()}"
            send_email(subject, body)
        finally:
            botlog_last_write = os.path.getmtime(botlog)
            time.sleep(60)
            botlog_current_write = os.path.getmtime(botlog)
            if botlog_last_write == botlog_current_write:
                print(f"Botlog:{botlog} not written to in 60sec - possible crash...")
                log_it(f"Botlog:{botlog} not written to in 60sec - possible crash")
                subject = f"CRASH:{script_name} - Botlog:{botlog} hasnt been written-to in 30sec"
                body = f"The {script_name} script has likely crashed. Botlog not written-to in 30 seconds"
                send_email(subject, body)

except KeyboardInterrupt:
    print("Monitoring script stopped by user...")
    log_it(f"---> Monitoring script stopped by user <---")
except Exception as e:
    print(f"Monitoring script crashed with error: {e}")
    log_it(f"---> Monitoring script crashed with error: {e} <---")