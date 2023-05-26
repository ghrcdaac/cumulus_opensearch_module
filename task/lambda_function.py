import json
import os
import sys
import time

import boto3

from task.logger import ops_logger
from task.open_search import CumulusOpenSearch

logging = ops_logger

if os.environ.get('CUMULUS_MESSAGE_ADAPTER_DIR'):
    sys.path.insert(0, os.environ.get('CUMULUS_MESSAGE_ADAPTER_DIR'))
    from run_cumulus_task import run_cumulus_task


def cumulus_handler(event, context):
    logging.info(f'Full Event: {event}')
    if run_cumulus_task and 'cma' in event:
        result = run_cumulus_task(lambda_handler, event, context)
    else:
        result = lambda_handler(event, context)
    return result


def lambda_handler(event, context):
    logging.info('start')
    logging.info(f'event: {event}')

    # Config should be the wrapper from either workflow execution or direct lambda invocation
    config = event.get('config')
    config = config.get('opensearch_config', config)
    terminate_after = config.get('terminate_after', 0)
    query = config.get('query')
    if not query:
        query_terms = config.get('query_terms')
        query = construct_query(query_terms)

    logging.info('querying open search...')
    cos = CumulusOpenSearch(record_type=config.get('record_type', 'granule'))
    response = cos.query_opensearch(query=query, terminate_after=terminate_after)

    opensearch_res = []
    for record in response:
        opensearch_res = opensearch_res + list(record)
    record_count = len(opensearch_res)
    logging.info(f'record_count: {len(opensearch_res)}')
    if event.get('config').get('workflow_name') == 'ReingestGranules':
        ret = generate_granule_output(opensearch_res)
    else:
        ret = upload_results_s3(opensearch_res, record_count)

    logging.info('end')
    return ret

def construct_query(fields):
    must = []
    for keyword, value in fields.items():
        temp = {f'{keyword}.keyword': value}
        if isinstance(value, list):
            must.append({'terms': temp})
        elif '*' in value:
            must.append({'wildcard': temp})
        else:
            must.append({'term': temp})

    query = {
        'query': {'bool': {"must": must}}
    }
    return query


def upload_results_s3(ret, record_count):
    bucket = os.getenv('private_bucket')
    key = 'opensearch_results.json'
    logging.info(f'Writing results to {bucket}/{key}')
    s3_client = boto3.client('s3')
    s3_client.put_object(
        Body=json.dumps(ret).encode('utf-8'),
        Bucket=bucket,
        Key=key
    )

    return {
        'bucket': bucket,
        'key': key,
        'record_count': record_count
    }


def generate_granule_output(response):
    ret = []
    for record in response:
        source = record.get('_source')
        file_list = []
        for file in source.get('files'):
            bucket = file.get('bucket')
            if 'private' in bucket:
                name = file.get('fileName')
                file_list.append(
                    {
                        'name': name,
                        'path': file.get('source', '').replace(f'/{name}', ''),
                        'size': file.get('size', 0),
                        'time': round(time.time() * 1000),
                        'bucket': file.get('bucket', ''),
                        'url_path': file.get('key', '').replace(f'/{name}', ''),
                        'type': file.get('type', '')

                    }
                )

        collection, version = str(source.get('collectionId')).rsplit('___', maxsplit=1)
        ret.append(
            {
                'granuleId': source.get('granuleId'),
                'dataType': collection,
                'version': version,
                'files': file_list
            }
        )

    return {'granules': ret}


if __name__ == '__main__':
    pass
