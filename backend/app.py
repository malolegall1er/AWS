import os
import boto3
from flask import Flask, render_template
from dotenv import load_dotenv

# Charger les variables depuis le fichier .env
load_dotenv()

# récupérer la région (avec fallback si absent)
REGION = os.getenv("AWS_DEFAULT_REGION", "eu-west-3")

app = Flask(__name__)

@app.route("/")
def index():
    s3 = boto3.client("s3", region_name=REGION)
    resp = s3.list_buckets()
    buckets = [b["Name"] for b in resp.get("Buckets", [])]
    return render_template("index.html", buckets=buckets)

@app.route("/instances")
def instances():
    ec2 = boto3.client("ec2", region_name=REGION)
    resp = ec2.describe_instances()
    data = []
    for r in resp.get("Reservations", []):
        for i in r.get("Instances", []):
            data.append({
                "id": i["InstanceId"],
                "state": i["State"]["Name"],
                "type": i["InstanceType"],
                "public_ip": i.get("PublicIpAddress")
            })
    return render_template("instances.html", instances=data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
