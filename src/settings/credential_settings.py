import boto3
from os import getenv
from dotenv import load_dotenv
load_dotenv()

def chunk_list(lst, size=10):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]



class AwsParameterStoreSettings:
    def __init__(self):
        self.region_name = getenv("AWS_REGION")
        self.aws_access_key = getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = getenv("AWS_SECRET_ACCESS_KEY")
        self.parameters = self._fetch_parameters()

    def _fetch_parameters(self):
        ssm_client = boto3.client(
            'ssm',
            region_name=self.region_name,
            aws_access_key_id=self.aws_access_key,
            aws_secret_access_key=self.aws_secret_access_key
        )

        server_env = getenv("SERVER", "DEVELOPMENT")
        is_production = server_env == "PRODUCTION"


        parameter_names = [
            'JWT-secret-key',
            'JWT-hashing-algorithm',
            'Avronn-backend-development-db' if not is_production else 'avaronn-backend-production-db',
            'avaronn-backend-development-db-endpoint' if not is_production else 'avaronn-production-db-hostedenpoint',
            '2factor-avaronn-api-key',
            'appyflow-gst-api-key',
            'Attrstr-RC-key',
            'hash_key_otp',
            'google_map_api_key',
            'firebase-development',
            'Google_fastapi_authentication_client_id',
            'Google_fastapi_authentication_client_secrets'
        ]

        aws_to_class_attrs = {
            'JWT-secret-key': 'jwt_secret_key',
            'JWT-hashing-algorithm': 'jwt_hashing_algorithm',
            'Avronn-backend-development-db': 'avronn_backend_db',
            'avaronn-backend-development-db-endpoint': 'avaronn_backend_db_endpoint',
            'avaronn-backend-production-db': 'avronn_backend_db',
            'avaronn-production-db-hostedenpoint': 'avaronn_backend_db_endpoint',
            '2factor-avaronn-api-key': 'twofactor_avaronn_api_key',
            'appyflow-gst-api-key': 'appyflow_gst_api_key',
            'Attrstr-RC-key': 'attrstr_rc_key',
            'hash_key_otp': 'hash_key_otp',
            'google_map_api_key': 'google_map_api_key',
            'firebase-development': 'firebase_development',
            'Google_fastapi_authentication_client_id': 'Google_fastapi_authentication_client_id',
            'Google_fastapi_authentication_client_secrets': 'Google_fastapi_authentication_client_secrets'
        }

        parameters = {}

        for chunk in chunk_list(parameter_names, 10):
            response = ssm_client.get_parameters(Names=chunk, WithDecryption=True)
            for param in response["Parameters"]:
                key = aws_to_class_attrs.get(param["Name"])
                if key:
                    parameters[key] = param["Value"]

        missing_params = {aws_to_class_attrs[name] for name in parameter_names if aws_to_class_attrs.get(name)} - set(parameters.keys())
        if missing_params:
            raise ValueError(f"Missing parameters from AWS Parameter Store: {missing_params}")

        parameters['database_name'] = f"Avaronn_{server_env}"
        return parameters

    def __getattr__(self, item):
        try:
            return self.parameters[item]
        except KeyError:
            raise AttributeError(f"Parameter '{item}' not found in AWS Parameter Store.")

# Usage
credential_setting = AwsParameterStoreSettings()
