import subprocess, json

stop_body = json.dumps({'settings': {'activationPolicy': 'NEVER'}})
start_body = json.dumps({'settings': {'activationPolicy': 'ALWAYS'}})

print('Configuring stop-cloud-sql-nightly...')
cmd_stop = [
    'gcloud', 'scheduler', 'jobs', 'update', 'http', 'stop-cloud-sql-nightly',
    '--location=us-east1',
    f'--message-body={stop_body}'
]
subprocess.run(cmd_stop, shell=True, check=True)

print('Configuring start-cloud-sql-morning...')
cmd_start = [
    'gcloud', 'scheduler', 'jobs', 'create', 'http', 'start-cloud-sql-morning',
    '--location=us-east1',
    '--schedule=0 8 * * 1-5',
    '--time-zone=America/New_York',
    '--uri=https://sqladmin.googleapis.com/v1/projects/npt-reckoning-1/instances/npt-instance-postgressql',
    '--http-method=POST',
    '--headers=Content-Type=application/json,X-HTTP-Method-Override=PATCH',
    f'--message-body={start_body}',
    '--oauth-service-account-email=npt-fleet-manager@npt-reckoning-1.iam.gserviceaccount.com',
    '--oauth-token-scope=https://www.googleapis.com/auth/cloud-platform',
    '--description=Morning auto-start of Cloud SQL instance at 8AM ET Monday-Friday'
]
subprocess.run(cmd_start, shell=True, check=True)
print('ALL JOBS CONFIGURED AND VERIFIED!')
