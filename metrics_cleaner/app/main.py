from prometheus_client import CollectorRegistry, Gauge, delete_from_gateway
import requests, logging, time, argparse, multiprocessing, socket
import logging as logger
import http.server
import socketserver

#logger = basicConfig(level="INFO")

def clean_job(url, retention_time):
    counter = 0 
    global jobs

    base_url =  "http://"+url+":9091"
    pushgateway_url =  base_url+"/api/v1/metrics" 

    try: 
        response = requests.get(pushgateway_url, verify=False,timeout=10)
        jobs = response.json()['data']
        #response.raise_for_status()
        
    except requests.exceptions.RequestException as e:
        logger.error(e.response.text)
        #logger.error("Can't receive pushgateway jobs & metrics from url")
        return "Error: " + str(e)

    for job in jobs:
        job_name =  job['labels']['job']
        grouping_key_labels = job['labels']

        if len(grouping_key_labels) > 1:  #if more than job (default) label
            grouping_key_labels.pop("job")

        print (grouping_key_labels)
        last_timestamp = float(job['push_time_seconds']['metrics'][0]['value'][:-4]) #.split('.')[-1]
        current_time = float(time.time() / 10**9)
        time_difference =  (current_time - float(last_timestamp)) * 10**9
        print (time_difference)
        # Use seconds in retention time. 
        # Eg. 86400 seconds in 24 hrs, 3600 sec in 1 hour, 900 sec in 15 mins
        logger.debug("time_difference %s" %(time_difference))

        if time_difference > retention_time:
            try: 
                delete_from_gateway(base_url, job=job_name, grouping_key=grouping_key_labels)
                logger.info("Metrics deleted for job %s successfully" % (job_name))
                counter += 1

            except requests.exceptions.RequestException as e:
                logger.error("Exception caught: %s" %(e))

    logger.info("Deleted "+ str(counter) +" jobs")
    
    return ' '

def web_server(port_num):
    """
    web server to keep the container running
    """
    Handler = http.server.SimpleHTTPRequestHandler
    httpd = socketserver.TCPServer(('127.0.0.1', port_num), Handler)

    return ' '


if __name__ == '__main__':

    my_parser = argparse.ArgumentParser(description='Mention metric cleaner args')

    # retention_time, default to 15 mins (in seconds) 
    my_parser.add_argument('--retention_time', action='store', type=int, help='retention_time', default=900)

    # job frequency to 1 hour (in seconds) 
    my_parser.add_argument('--job_frequency', action='store', type=int, help='job_frequency', default=3600)

    # log level: info, debug, error 
    my_parser.add_argument('--log_level', action='store', type=str, help='logging level', default='error', choices=['info','error','warning','debug'])

    # url of pushgateway. 
    my_parser.add_argument('--url', action='store', type=str, help='url', default='localhost')
    
    # port on which server is running not pushgateway. Pushgateway runs on port 9091
    my_parser.add_argument('--port', action='store', type=int,help='port', default=8000)
    
    # Execute the parse_args() method
    args = my_parser.parse_args()

    if args.log_level: 
        logs_level = (args.log_level).upper()

    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logs_level,
        datefmt='%Y-%m-%d %H:%M:%S')

    retention_time = int(args.retention_time)
    job_frequency = int(args.job_frequency)
    url = args.url
    port_num = int(args.port)

    # http socket to keep sidecar running
    p = multiprocessing.Process(target=web_server, args = [port_num])
    p.start()

    logger.info("#### Starting Pushgateway Cleaner ####")
    logger.debug("Retention: %s and Frequency: %s (in seconds) running on port: %s" %(retention_time, job_frequency, port_num))

    s = socket.socket()
    s.settimeout(5)   # 5 seconds

    while True:

        try:
            clean_job(url,retention_time)
            time.sleep(job_frequency)

        except ConnectionRefusedError:
            print("Pushgateway not reachable")
            time.sleep(10)

        #except OSError:
        #    print("Pushgateway not reachable")
        #    time.sleep(10)

        except Exception as e:
            print(e)
            time.sleep(10)