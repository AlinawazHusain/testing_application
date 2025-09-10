import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError , ClientError
import json
from os import getenv
from dotenv import load_dotenv
from os import getenv
from config.exceptions import InternalServerError

load_dotenv()


def get_parameters(names, decrypt=False):
    """
    Retrieve parameters from AWS Systems Manager (SSM) Parameter Store.

    This function connects to AWS SSM and retrieves the specified parameter names. 
    It supports optional decryption for secure string parameters.

    Args:
        names (list): A list of parameter names to retrieve.
        decrypt (bool): Whether to decrypt SecureString values. Defaults to False.

    Returns:
        dict: A dictionary of parameter names and their corresponding values.

    Raises:
        InternalServerError: If the SSM client fails to fetch the parameters.
    """
    
    try:
        ssm_client = boto3.client(
            'ssm',
            region_name = getenv("AWS_REGION"),
            aws_access_key_id = getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key = getenv("AWS_SECRET_ACCESS_KEY")
        )
        response = ssm_client.get_parameters(
            Names=names,
            WithDecryption=decrypt
        )
        parameters = {param['Name']: param['Value'] for param in response['Parameters']}

        return parameters
    
    except ClientError as e:
        raise InternalServerError(message = f"Error in getting parameters from parameter store : {str(e)}")






async def upload_file_to_s3(file, s3_key):
    """
    Upload a file object to an AWS S3 bucket and return the file URL.

    This function uses boto3 to upload a file-like object to a specified S3 key
    and constructs the public URL for the uploaded file.

    Args:
        file (UploadFile): The file object (typically from FastAPI's UploadFile).
        s3_key (str): The destination key (path) within the S3 bucket.

    Returns:
        str: The public S3 URL of the uploaded file.

    Raises:
        InternalServerError: If AWS credentials are missing or the upload fails.
    """
    
    try:
        file_upload_bucket = getenv('FILE_UPLOAD_BUCKET')
        region = getenv('AWS_REGION')
        s3_client = boto3.client('s3', aws_access_key_id=getenv('AWS_ACCESS_KEY_ID'),
                         aws_secret_access_key=getenv('AWS_SECRET_ACCESS_KEY'),
                         region_name=region)
        
        s3_client.upload_fileobj(file.file, file_upload_bucket, s3_key)
        file_url = f"https://{file_upload_bucket}.s3.{region}.amazonaws.com/{s3_key}"
        return file_url

    except NoCredentialsError as e:
        raise InternalServerError(message = f"No Credentials : {str(e)}")
    except PartialCredentialsError as e:
        raise InternalServerError(message = f"Partial Credentials : {str(e)}")
    except Exception as e:
        raise InternalServerError(message = f"Error in getting parameters from parameter store : {str(e)}")


 
 
 

async def write_json_to_s3(details, s3_key):
    """
    Serialize and upload a Python dictionary as a JSON file to AWS S3.

    This function serializes the given dictionary to JSON format and uploads it 
    to the specified key in the configured S3 bucket.

    Args:
        details (dict): The dictionary to serialize and upload.
        s3_key (str): The S3 key (path/filename) for the uploaded JSON file.

    Returns:
        str: The public S3 URL of the uploaded JSON file.

    Raises:
        InternalServerError: If AWS credentials are missing or the upload fails.
    """
    
    try:
        s3_client = boto3.client('s3', aws_access_key_id=getenv('AWS_ACCESS_KEY_ID'),
                         aws_secret_access_key=getenv('AWS_SECRET_ACCESS_KEY'),
                         region_name=getenv('AWS_REGION'))
        json_data = json.dumps(details)
        s3_client.put_object(
        Bucket=getenv('FILE_UPLOAD_BUCKET'),
        Key=s3_key,
        Body=json_data,
        ContentType='application/json'
        )
    
        file_url = f"https://{getenv('FILE_UPLOAD_BUCKET')}.s3.{getenv('AWS_REGION')}.amazonaws.com/{s3_key}"
        return file_url

    except NoCredentialsError as e:
        raise InternalServerError(message = f"No Credentials : {str(e)}")
    except PartialCredentialsError as e:
        raise InternalServerError(message = f"Partial Credentials : {str(e)}")
    except Exception as e:
        raise InternalServerError(message = f"Error in getting parameters from parameter store : {str(e)}")


