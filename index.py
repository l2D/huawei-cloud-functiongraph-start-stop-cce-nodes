from typing import Dict, Any, List

from huaweicloudsdkcore.auth.credentials import BasicCredentials
from huaweicloudsdkcore.exceptions import exceptions
from huaweicloudsdkcce.v3.region.cce_region import CceRegion
from huaweicloudsdkcce.v3 import (
    CceClient,
    ListClustersRequest,
    HibernateClusterRequest,
    AwakeClusterRequest,
    ListNodesRequest,
)
from huaweicloudsdkecs.v2.region.ecs_region import EcsRegion

from huaweicloudsdkecs.v2 import (
    EcsClient,
    BatchStopServersRequest,
    BatchStartServersRequest,
    BatchStopServersRequestBody,
    BatchStopServersOption,
    BatchStartServersRequestBody,
    BatchStartServersOption,
    ServerId,
)


def get_cce_client(credentials: BasicCredentials, endpoint: str, region: str) -> CceClient:
    if endpoint:
        return CceClient.new_builder().with_credentials(credentials).with_endpoint(endpoint).build()
    return CceClient.new_builder().with_credentials(credentials).with_region(CceRegion.value_of(region)).build()

def get_ecs_client(credentials: BasicCredentials, endpoint: str, region: str) -> EcsClient:
    if endpoint:
        return EcsClient.new_builder().with_credentials(credentials).with_endpoint(endpoint).build()
    return EcsClient.new_builder().with_credentials(credentials).with_region(EcsRegion.value_of(region)).build()

def list_clusters(client: CceClient, logger: Any) -> List[Dict[str, str]]:
    logger.info("Starting to list clusters")
    list_clusters_req = ListClustersRequest()
    resp_list_clusters = client.list_clusters(list_clusters_req)
    
    cluster_list = []
    for cluster in resp_list_clusters.items:
        cluster_list.append({"cluster_id": cluster.metadata.uid, "cluster_name": cluster.metadata.name})

    logger.info("Cluster listing successful")
    logger.info(f"Cluster list: {cluster_list}")
    return cluster_list
    
def list_nodes(client: CceClient, logger: Any, cluster_id: str) -> List[Dict[str, str]]:
    logger.info(f"Starting to list nodes for cluster {cluster_id}")
    list_nodes_req = ListNodesRequest()
    list_nodes_req.cluster_id = cluster_id
    resp_list_nodes = client.list_nodes(list_nodes_req)

    node_list = []
    for node in resp_list_nodes.items:
                
        node_info = {
            "node_id": node.metadata.uid,
            "node_name": node.metadata.name,
            "server_id": node.status.server_id,
        }
        node_list.append(node_info)
        logger.info(f"Added node: {node_info}")
    
    logger.info(f"Node listing successful for cluster {cluster_id}")
    logger.info(f"Node list: {node_list}")
    return node_list

def stop_servers(cce_client: CceClient, ecs_client: EcsClient, instruct_type: str, logger: Any, cluster_id: str) -> Dict[str, Any]:

    server_list = list_nodes(cce_client, logger, cluster_id)
    
    logger.info("Starting to stop servers")
    stop_ecs_request = BatchStopServersRequest()
    servers_to_stop = [ServerId(id=server["server_id"]) for server in server_list]
    
    os_stop_body = BatchStopServersOption(servers=servers_to_stop, type=instruct_type)
    stop_ecs_request.body = BatchStopServersRequestBody(os_stop=os_stop_body)
    
    ecs_client.batch_stop_servers(stop_ecs_request)   
    
    logger.info("Server stop operation successful")
        
    return {
        "status": "success",
        "message": "Servers stopped successfully",
        "action": "stop",
        "data": {"server_list": server_list}
    }

def start_servers(cce_client: CceClient, ecs_client: EcsClient, logger: Any, cluster_id: str) -> Dict[str, Any]:
    server_list = list_nodes(cce_client, logger, cluster_id)

    logger.info("Starting to start servers")
    start_ecs_request = BatchStartServersRequest()
    servers_to_start = [ServerId(id=server["server_id"]) for server in server_list]
    
    os_start_body = BatchStartServersOption(servers=servers_to_start)
    start_ecs_request.body = BatchStartServersRequestBody(os_start=os_start_body)
    
    ecs_client.batch_start_servers(start_ecs_request)

    logger.info("Server start operation successful")
    
    return {
        "status": "success",
        "message": "Servers started successfully",
        "action": "start",
        "data": {"server_list": server_list}
    }

def hibernate_cluster(cce_client: CceClient, ecs_client: EcsClient, logger: Any, cluster_ids: str) -> Dict[str, Any]:
    logger.info("Starting to list clusters")
    cluster_list = list_clusters(cce_client, logger)
    
    logger.info(f"Cluster IDs to hibernate: {cluster_ids}")

    cluster_to_hibernate = []
    for cluster in cluster_list:
        if cluster["cluster_id"] in cluster_ids.split(","):
            cluster_to_hibernate.append({
                "cluster_id": cluster["cluster_id"],
                "cluster_name": cluster["cluster_name"],
            })
    
    logger.info("Starting to hibernate cluster")
    for cluster in cluster_to_hibernate:
        # Stop ECS nodes
        stop_servers(cce_client, ecs_client, instruct_type="SOFT", logger=logger, cluster_id=cluster["cluster_id"])
        
        hibernate_req = HibernateClusterRequest()
        hibernate_req.cluster_id = cluster["cluster_id"]
        cce_client.hibernate_cluster(hibernate_req)
        logger.info(f"Cluster ID: {cluster['cluster_id']}, Name: {cluster['cluster_name']} started hibernation process")
    logger.info("Cluster hibernation successful")
    
    return {
        "status": "success",
        "message": "Cluster hibernated successfully",
        "action": "hibernate",
        "data": {"cluster_list": cluster_to_hibernate}
    }
    
def awake_cluster(cce_client: CceClient, ecs_client: EcsClient, logger: Any, cluster_ids: str) -> Dict[str, Any]:
    logger.info("Starting to list clusters")
    cluster_list = list_clusters(cce_client, logger)
    
    logger.info(f"Cluster IDs to awake: {cluster_ids}")
    
    cluster_to_awake = []
    for cluster in cluster_list:
        if cluster["cluster_id"] in cluster_ids.split(","):
            cluster_to_awake.append({
                "cluster_id": cluster["cluster_id"],
                "cluster_name": cluster["cluster_name"],
            })
    
    logger.info("Starting to awake clusters")
    for cluster in cluster_to_awake:       
        # Start ECS nodes
        start_servers(cce_client, ecs_client, logger, cluster_id=cluster["cluster_id"])

        # Awake CCE cluster
        awake_req = AwakeClusterRequest()
        awake_req.cluster_id = cluster["cluster_id"]
        cce_client.awake_cluster(awake_req)
        logger.info(f"Cluster ID: {cluster['cluster_id']}, Name: {cluster['cluster_name']} started awakening process")
        
    logger.info("Cluster awakening process initiated")
    
    return {
        "status": "success",
        "message": "Cluster awakening process initiated successfully",
        "action": "awake",
        "data": {"cluster_list": cluster_to_awake}
    }

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    try:
        # Configuration
        project_id = context.getUserData("projectId", "").strip()
        endpoint = context.getUserData("endpoint", "").strip()
        region = context.getUserData("region", "").strip()
        ak = context.getAccessKey().strip() or context.getUserData("ak", "").strip()
        sk = context.getSecretKey().strip() or context.getUserData("sk", "").strip()
        action: str = context.getUserData("action", "").strip().lower()
        cluster_ids: str = context.getUserData("cluster_ids", "").strip().lower()

        # Validation
        if not project_id:
            raise ValueError("'project_id' not configured")
        if not region:
            raise ValueError("'region' not configured")
        if action not in ["start", "stop"]:
            raise ValueError("'action' must be 'start' or 'stop'")
        if not ak or not sk:
            raise ValueError("AK/SK not provided")
        if not cluster_ids:
            raise ValueError("'cluster_ids' not provided")

        logger = context.getLogger()
        credentials = BasicCredentials(ak, sk).with_project_id(project_id)
        cce_client = get_cce_client(credentials, endpoint, region)
        ecs_client = get_ecs_client(credentials, endpoint, region)

        if action == "stop":
            return hibernate_cluster(cce_client, ecs_client, logger, cluster_ids)
        elif action == "start":
            return awake_cluster(cce_client, ecs_client, logger, cluster_ids)

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
