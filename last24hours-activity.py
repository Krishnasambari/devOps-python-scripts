import boto3
from datetime import datetime, timedelta
import pytz

# Initialize clients
ec2 = boto3.client("ec2")
rds = boto3.client("rds")
s3 = boto3.client("s3")
lam = boto3.client("lambda")
dynamo = boto3.client("dynamodb")
ce = boto3.client("ce", region_name="us-east-1")  # Cost Explorer only available in us-east-1

# -----------------------------
# 1. COST EXPLORER - Last 24h
# -----------------------------
def get_costs():
    end = datetime.utcnow().date()
    start = end - timedelta(days=1)

    response = ce.get_cost_and_usage(
        TimePeriod={
            "Start": start.strftime("%Y-%m-%d"),
            "End": end.strftime("%Y-%m-%d"),
        },
        Granularity="DAILY",
        Metrics=["UnblendedCost"],
        GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
    )

    print("\n📊 AWS COSTS in last 24h:")
    for group in response["ResultsByTime"][0]["Groups"]:
        service = group["Keys"][0]
        amount = group["Metrics"]["UnblendedCost"]["Amount"]
        if float(amount) > 0:
            print(f"  - {service}: ${float(amount):.4f}")


# -----------------------------
# 2. RESOURCES INVENTORY
# -----------------------------
def list_resources():
    print("\n🖥️ CURRENTLY RUNNING RESOURCES:")

    # EC2
    instances = ec2.describe_instances(
        Filters=[{"Name": "instance-state-name", "Values": ["running"]}]
    )
    ec2_ids = [
        i["InstanceId"]
        for r in instances["Reservations"]
        for i in r["Instances"]
    ]
    print(f"  - EC2 Running Instances: {ec2_ids if ec2_ids else 'None'}")

    # RDS Instances
    rds_instances = rds.describe_db_instances()["DBInstances"]
    rds_ids = [db["DBInstanceIdentifier"] for db in rds_instances if db["DBInstanceStatus"] == "available"]
    print(f"  - RDS Instances: {rds_ids if rds_ids else 'None'}")

    # RDS Clusters (Aurora)
    clusters = rds.describe_db_clusters()["DBClusters"]
    cluster_ids = [cl["DBClusterIdentifier"] for cl in clusters if cl["Status"] == "available"]
    print(f"  - RDS Clusters: {cluster_ids if cluster_ids else 'None'}")

    # S3
    buckets = s3.list_buckets()["Buckets"]
    bucket_names = [b["Name"] for b in buckets]
    print(f"  - S3 Buckets: {bucket_names if bucket_names else 'None'}")

    # Lambda
    funcs = lam.list_functions()["Functions"]
    func_names = [f["FunctionName"] for f in funcs]
    print(f"  - Lambda Functions: {func_names if func_names else 'None'}")

    # DynamoDB
    tables = dynamo.list_tables()["TableNames"]
    print(f"  - DynamoDB Tables: {tables if tables else 'None'}")


# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    print("🔎 AWS 24h Resource & Cost Summary\n")
    get_costs()
    list_resources()
