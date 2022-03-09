import requests
import os 

if __name__ == '__main__':

    user = os.environ['username'] 
    password = os.environ['password']

    job_name='my_custom_metrics'
    instance_name='10.20.0.1:9000'
    provider='DataBricks'
    payload_key='cpu_utilization'
    payload_value='22.90'
    
    team_name = "Data_team"
    
    response = requests.post('https://pushgateway.example.com/metrics/job/{j}/instance/{i}/team/{t}'.format(j=job_name, i=instance_name, t=team_name), data='{k} {v}\n'.format(k=payload_key, v=payload_value),auth=(user,password))
    print(response.status_code)
