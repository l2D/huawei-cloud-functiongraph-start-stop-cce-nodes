from typing import Dict, Any, List

from huaweicloudsdkcore.auth.credentials import BasicCredentials
from huaweicloudsdkecs.v2.region.ecs_region import EcsRegion
from huaweicloudsdkcore.exceptions import exceptions
from huaweicloudsdkecs.v2 import (
    EcsClient,
    ListServersDetailsRequest,
    BatchStopServersRequest,
    BatchStartServersRequest,
    BatchStopServersRequestBody,
    BatchStopServersOption,
    BatchStartServersRequestBody,
    BatchStartServersOption,
    ServerId,
)

def get_ecs_client(credentials: BasicCredentials, endpoint: str, region: str) -> EcsClient:
    if endpoint:
        return EcsClient.new_builder().with_credentials(credentials).with_endpoint(endpoint).build()
    return EcsClient.new_builder().with_credentials(credentials).with_region(EcsRegion.value_of(region)).build()

def list_servers(client: EcsClient, logger: Any, cluster_id: str) -> List[Dict[str, str]]:
    logger.info("Starting to list servers")
    list_server_req = ListServersDetailsRequest()
    list_server_req.tags = f"CCE-Cluster-ID={cluster_id}" if cluster_id else "CCE-Cluster-ID"
    resp_list_server = client.list_servers_details(list_server_req)
    
    server_list = []
    for server in resp_list_server.servers:
        logger.info(f"Server ID: {server.id}, Name: {server.name}")
        server_list.append({"server_id": server.id, "server_name": server.name})
    
    logger.info("Server listing successful")
    return server_list

def stop_servers(client: EcsClient, instruct_type: str, logger: Any, cluster_id: str) -> Dict[str, Any]:
    server_list = list_servers(client, logger, cluster_id)
    
    logger.info("Starting to stop servers")
    stop_ecs_request = BatchStopServersRequest()
    servers_to_stop = [ServerId(id=server["server_id"]) for server in server_list]
    
    os_stop_body = BatchStopServersOption(servers=servers_to_stop, type=instruct_type)
    stop_ecs_request.body = BatchStopServersRequestBody(os_stop=os_stop_body)
    
    client.batch_stop_servers(stop_ecs_request)
    logger.info("Server stop operation successful")
    
    return {
        "status": "success",
        "message": "Servers stopped successfully",
        "action": "stop",
        "data": {"server_list": server_list}
    }

def start_servers(client: EcsClient, logger: Any, cluster_id: str) -> Dict[str, Any]:
    server_list = list_servers(client, logger, cluster_id)
    
    logger.info("Starting to start servers")
    start_ecs_request = BatchStartServersRequest()
    servers_to_start = [ServerId(id=server["server_id"]) for server in server_list]
    
    os_start_body = BatchStartServersOption(servers=servers_to_start)
    start_ecs_request.body = BatchStartServersRequestBody(os_start=os_start_body)
    
    client.batch_start_servers(start_ecs_request)
    logger.info("Server start operation successful")
    
    return {
        "status": "success",
        "message": "Servers started successfully",
        "action": "start",
        "data": {"server_list": server_list}
    }

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    try:
        # Configuration
        project_id = context.getUserData("projectId", "").strip()
        endpoint = context.getUserData("endpoint", "").strip()
        region = context.getUserData("region", "").strip()
        ak = context.getAccessKey().strip() or context.getUserData("ak", "").strip()
        sk = context.getSecretKey().strip() or context.getUserData("sk", "").strip()
        instruct_type: str = context.getUserData("type", "SOFT").strip().upper()
        action: str = context.getUserData("action", "").strip().lower()
        cluster_id: str = context.getUserData("clusterId", "").strip().lower()

        # Validation
        if not project_id:
            raise ValueError("'project_id' not configured")
        if not region:
            raise ValueError("'region' not configured")
        if action not in ["start", "stop"]:
            raise ValueError("'action' must be 'start' or 'stop'")
        if not ak or not sk:
            raise ValueError("AK/SK not provided")
        if instruct_type not in ["SOFT", "HARD"]:
            raise ValueError("'type' must be 'SOFT' or 'HARD'")
        if not cluster_id:
            cluster_id = ""

        logger = context.getLogger()
        credentials = BasicCredentials(ak, sk).with_project_id(project_id)
        client = get_ecs_client(credentials, endpoint, region)

        if action == "stop":
            return stop_servers(client, instruct_type, logger, cluster_id)
        elif action == "start":
            return start_servers(client, logger, cluster_id)

    except exceptions.ClientRequestException as e:
        logger.error(f"ClientRequestException: {e}")
        return {
            "status": "error",
            "message": f"Error: {e.error_msg}",
            "action": action,
            "data": {
                "error_code": e.error_code,
                "status_code": e.status_code,
                "request_id": e.request_id
            }
        }
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}",
            "action": action,
            "data": {}
        }
