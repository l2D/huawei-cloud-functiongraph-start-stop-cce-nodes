from typing import Dict, Any, List

from huaweicloudsdkcore.auth.credentials import BasicCredentials
from huaweicloudsdkcore.exceptions import exceptions
from huaweicloudsdkcce.v3.region.cce_region import CceRegion
from huaweicloudsdkcce.v3 import (
    CceClient,
    ListClustersRequest,
    HibernateClusterRequest,
    AwakeClusterRequest,
)

def get_cce_client(credentials: BasicCredentials, endpoint: str, region: str) -> CceClient:
    if endpoint:
        return CceClient.new_builder().with_credentials(credentials).with_endpoint(endpoint).build()
    return CceClient.new_builder().with_credentials(credentials).with_region(CceRegion.value_of(region)).build()

def list_clusters(client: CceClient, logger: Any) -> List[Dict[str, str]]:
    logger.info("Starting to list clusters")
    list_clusters_req = ListClustersRequest()
    resp_list_clusters = client.list_clusters(list_clusters_req)
    
    cluster_list = []
    for cluster in resp_list_clusters.clusters:
        logger.info(f"Cluster ID: {cluster.id}, Name: {cluster.name}")
        cluster_list.append({"cluster_id": cluster.id, "cluster_name": cluster.name})
    
    logger.info("Cluster listing successful")
    return cluster_list

def hibernate_cluster(client: CceClient, logger: Any, cluster_ids: str) -> Dict[str, Any]:
    cluster_list = list_clusters(client, logger)

    cluster_to_hibernate = []
    for cluster in cluster_list:
        if cluster["cluster_id"] in cluster_ids.split(","):
            cluster_to_hibernate.append({
                "cluster_id": cluster["cluster_id"],
                "cluster_name": cluster["cluster_name"],
            })
    
    logger.info("Starting to hibernate cluster")
    for cluster_id in cluster_to_hibernate:
        hibernate_req = HibernateClusterRequest()
        hibernate_req.body = {"cluster_id": cluster_id}
        client.hibernate_cluster(hibernate_req)
        logger.info(f"Cluster ID: {cluster_id['cluster_id']}, Name: {cluster_id['cluster_name']} started hibernation process")
    logger.info("Cluster hibernation successful")
    
    return {
        "status": "success",
        "message": "Cluster hibernated successfully",
        "action": "hibernate",
        "data": {"cluster_list": cluster_to_hibernate}
    }
    
def awake_cluster(client: CceClient, logger: Any, cluster_ids: str) -> Dict[str, Any]:
    cluster_list = list_clusters(client, logger)
    
    cluster_to_awake = []
    for cluster in cluster_list:
        if cluster["cluster_id"] in cluster_ids.split(","):
            cluster_to_awake.append({
                "cluster_id": cluster["cluster_id"],
                "cluster_name": cluster["cluster_name"],
            })
    
    logger.info("Starting to awake cluster")
    for cluster_id in cluster_to_awake:
        awake_req = AwakeClusterRequest()
        awake_req.body = {"cluster_id": cluster_id}
        client.awake_cluster(awake_req)
        logger.info(f"Cluster ID: {cluster_id['cluster_id']}, Name: {cluster_id['cluster_name']} started awakening process")
    
    logger.info("Cluster awakening successful")
    
    return {
        "status": "success",
        "message": "Cluster awakened successfully",
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
        client = get_cce_client(credentials, endpoint, region)

        if action == "stop":
            return hibernate_cluster(client, logger, cluster_ids)
        elif action == "start":
            return awake_cluster(client, logger, cluster_ids)

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
