import json
import paramiko
import boto3
import os

def lambda_handler(event, context):
    S3Client = boto3.client('s3')
    S3Client.download_file ('test-poc12', 'key-file/poc-test.pem', '/tmp/keyname.pem')
    pem_key = paramiko.RSAKey.from_private_key_file("/tmp/keyname.pem")
    
    #Create a new client
    SSHClient = paramiko.SSHClient()
    SSHClient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    host ="65.0.170.138"
    SSHClient.connect (hostname = host, username = "ec2-user", pkey = pem_key)

    print("Connected to: " + host)
    
    s_path = '/home/ec2-user/'
    s_pattern = '"test*"'
    rawcommand = 'find {path} -name {pattern}'
    command = rawcommand.format(path = s_path, pattern = s_pattern)
    stdin, stdout, stderr = SSHClient.exec_command(command)
    FileList = stdout.read().splitlines()
    
    SFTPClient = SSHClient.open_sftp()
    FileCount = 0
    for TrigFile in FileList:
        (head, filename) = os.path.split(TrigFile)
        FileName = filename.decode('utf-8')
        print(FileName)
        TempFile = '/tmp/' + FileName
        S3File = 'sftp-files/' + FileName
        SFTPClient.get(TrigFile, TempFile)
        S3Client.upload_file(TempFile, 'test-poc12', S3File)
        SFTPClient.remove(TrigFile)
        FileCount += 1
    SFTPClient.close()
    SSHClient.close()
    
    return str(FileCount) + " file(s) have been uploaded to the S3 bucket."
