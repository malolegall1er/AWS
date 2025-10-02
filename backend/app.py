import os
import io
import shutil
import subprocess
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
import boto3
import botocore
from werkzeug.utils import secure_filename

REGION = os.getenv("AWS_REGION", "us-east-1")  # ajuste ta région

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "B3KaZg+GPBRThYQ2o1hegRYr1EoL0PFNhAEhNKMY")

session = boto3.Session(region_name=REGION)
s3 = session.client("s3")
ec2 = session.client("ec2")

# ---------- Helpers S3 ----------
def bucket_exists(name: str) -> bool:
    try:
        s3.head_bucket(Bucket=name)
        return True
    except botocore.exceptions.ClientError:
        return False

def empty_bucket(name: str):
    # supprime objets & versions si versionning actif
    s3r = session.resource("s3")
    b = s3r.Bucket(name)
    b.objects.all().delete()
    try:
        b.object_versions.all().delete()
    except Exception:
        pass

# ---------- Routes ----------
@app.route("/")
def index():
    # liste buckets
    buckets = []
    try:
        resp = s3.list_buckets()
        buckets = [b["Name"] for b in resp.get("Buckets", [])]
    except Exception as e:
        flash(f"Erreur S3: {e}")
    return render_template("index.html", buckets=buckets, region=REGION)

@app.route("/bucket/create", methods=["POST"])
def create_bucket():
    name = request.form.get("bucket_name", "").strip()
    if not name:
        flash("Nom de bucket requis.")
        return redirect(url_for("index"))
    try:
        config = {"LocationConstraint": REGION}
        s3.create_bucket(Bucket=name,
                         CreateBucketConfiguration=config if REGION != "us-east-1" else {})
        flash(f"Bucket créé: {name}")
    except botocore.exceptions.ClientError as e:
        flash(f"Création échouée: {e}")
    return redirect(url_for("index"))

@app.route("/bucket/<bucket>/upload", methods=["POST"])
def upload_object(bucket):
    if "file" not in request.files:
        flash("Aucun fichier.")
        return redirect(url_for("index"))
    f = request.files["file"]
    key = secure_filename(f.filename)
    if key == "":
        flash("Nom de fichier invalide.")
        return redirect(url_for("index"))
    try:
        s3.upload_fileobj(f, bucket, key)
        flash(f"Upload OK: s3://{bucket}/{key}")
    except Exception as e:
        flash(f"Upload échoué: {e}")
    return redirect(url_for("index"))

@app.route("/bucket/<bucket>/delete", methods=["POST"])
def delete_bucket(bucket):
    try:
        empty_bucket(bucket)
        s3.delete_bucket(Bucket=bucket)
        flash(f"Bucket supprimé: {bucket}")
    except Exception as e:
        flash(f"Suppression échouée: {e}")
    return redirect(url_for("index"))

@app.route("/instances")
def instances():
    data = []
    try:
        resp = ec2.describe_instances()
        for r in resp.get("Reservations", []):
            for i in r.get("Instances", []):
                data.append({
                    "id": i["InstanceId"],
                    "type": i.get("InstanceType"),
                    "state": i.get("State", {}).get("Name"),
                    "public_ip": i.get("PublicIpAddress"),
                    "name": next((t["Value"] for t in i.get("Tags", []) if t["Key"]=="Name"), "")
                })
    except Exception as e:
        flash(f"Erreur EC2: {e}")
    return render_template("instances.html", instances=data)

# -------- Bonus 1: lancer une EC2 publique --------
@app.route("/ec2/run", methods=["POST"])
def run_instance():
    ami = request.form.get("ami", "").strip()  # ex: Amazon Linux 2023 pour ta région
    itype = request.form.get("itype", "t3.micro").strip()
    key_name = request.form.get("key_name", "").strip()
    sg_name = "aws-mini-admin-sg"

    if not ami:
        flash("AMI obligatoire")
        return redirect(url_for("index"))

    try:
        # security group (ouvre le port 80)
        vpcs = ec2.describe_vpcs()["Vpcs"]
        vpc_id = vpcs[0]["VpcId"]
        sgs = ec2.describe_security_groups(
            Filters=[{"Name":"group-name","Values":[sg_name]}])["SecurityGroups"]
        if not sgs:
            sg = ec2.create_security_group(
                GroupName=sg_name, Description="Web access", VpcId=vpc_id)
            ec2.authorize_security_group_ingress(
                GroupId=sg["GroupId"],
                IpPermissions=[{
                    "IpProtocol": "tcp", "FromPort": 80, "ToPort": 80,
                    "IpRanges": [{"CidrIp": "0.0.0.0/0"}]
                }]
            )
            sg_id = sg["GroupId"]
        else:
            sg_id = sgs[0]["GroupId"]

        # user-data: installe nginx et page test
        user_data = """#!/bin/bash
dnf -y update
dnf -y install nginx
echo '<h1>Hello from EC2</h1>' > /usr/share/nginx/html/index.html
systemctl enable nginx
systemctl start nginx
"""
        run = ec2.run_instances(
            ImageId=ami, InstanceType=itype, MinCount=1, MaxCount=1,
            KeyName=key_name if key_name else None,
            SecurityGroupIds=[sg_id],
            UserData=user_data,
            TagSpecifications=[{
                "ResourceType":"instance",
                "Tags":[{"Key":"Name","Value":"aws-mini-admin"}]
            }]
        )
        iid = run["Instances"][0]["InstanceId"]
        flash(f"Instance lancée: {iid} (attends l’IP publique)")
    except botocore.exceptions.ClientError as e:
        flash(f"Lancement EC2 échoué: {e}")
    return redirect(url_for("instances"))

# -------- Bonus 2: cloner un repo et le servir --------
@app.route("/repo/clone", methods=["POST"])
def clone_repo():
    url = request.form.get("repo_url", "").strip()
    if not url:
        flash("URL de repo obligatoire")
        return redirect(url_for("index"))
    target = os.path.join(os.getcwd(), "cloned_site")
    if os.path.exists(target):
        shutil.rmtree(target)
    try:
        subprocess.check_call(["git", "clone", "--depth", "1", url, target])
        flash("Repo cloné. S’il contient un index.html, il sera servi sur /site")
    except subprocess.CalledProcessError as e:
        flash(f"Clone échoué: {e}")
    return redirect(url_for("index"))

@app.route("/site/<path:path>")
def serve_cloned(path):
    root = os.path.join(os.getcwd(), "cloned_site")
    return send_from_directory(root, path)

@app.route("/site")
def serve_index():
    root = os.path.join(os.getcwd(), "cloned_site")
    index = os.path.join(root, "index.html")
    if os.path.exists(index):
        return send_from_directory(root, "index.html")
    return "Pas d'index.html détecté."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
