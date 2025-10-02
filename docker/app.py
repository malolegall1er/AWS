import os
import random
import string
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
import boto3
from botocore.exceptions import ClientError
from git import Repo

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "change-me")
REGION = os.environ.get("AWS_DEFAULT_REGION", "eu-west-3")
WORKSPACE = os.environ.get("WORKSPACE", "/workspace")
UPLOAD_DIR = os.path.join(WORKSPACE, "uploads")
REPOS_DIR = os.path.join(WORKSPACE, "repos")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(REPOS_DIR, exist_ok=True)

def s3_client():
    return boto3.client("s3", region_name=REGION)

def ec2_resource():
    return boto3.resource("ec2", region_name=REGION)

def rand_suffix(n=6):
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))

@app.route("/")
def index():
    # S3
    s3 = s3_client()
    buckets = s3.list_buckets().get("Buckets", [])
    # EC2
    ec2 = ec2_resource()
    instances = list(ec2.instances.all())
    return render_template("index.html", buckets=buckets, instances=instances, region=REGION)

# ---------- S3 ----------
@app.route("/s3/create", methods=["POST"])
def s3_create():
    base = request.form.get("bucket_name", "").strip().lower()
    if not base:
        flash("Nom de bucket requis.", "error")
        return redirect(url_for("index"))
    name = base
    s3 = s3_client()
    try:
        s3.create_bucket(
            Bucket=name,
            CreateBucketConfiguration={"LocationConstraint": REGION}
        )
        flash(f"Bucket créé: {name}", "ok")
    except ClientError as e:
        if e.response.get("Error", {}).get("Code") in ("BucketAlreadyOwnedByYou",):
            flash("Tu possèdes déjà ce bucket.", "ok")
        elif e.response.get("Error", {}).get("Code") in ("BucketAlreadyExists", "InvalidBucketName"):
            name = f"{base}-{rand_suffix()}"
            s3.create_bucket(
                Bucket=name,
                CreateBucketConfiguration={"LocationConstraint": REGION}
            )
            flash(f"Nom occupé. Bucket créé sous: {name}", "ok")
        else:
            flash(f"Erreur création bucket: {e}", "error")
    return redirect(url_for("index"))

@app.route("/s3/upload", methods=["POST"])
def s3_upload():
    bucket = request.form.get("target_bucket")
    file = request.files.get("file")
    key = request.form.get("key", "").strip() or (file.filename if file else None)
    if not bucket or not file or not key:
        flash("Bucket, fichier et clé requis.", "error")
        return redirect(url_for("index"))
    s3 = s3_client()
    data = file.read()
    s3.put_object(Bucket=bucket, Key=key, Body=data)
    flash(f"Upload ok vers s3://{bucket}/{key}", "ok")
    local = os.path.join(UPLOAD_DIR, key)
    with open(local, "wb") as f:
        f.write(data)
    return redirect(url_for("index"))

@app.route("/s3/delete", methods=["POST"])
def s3_delete():
    bucket = request.form.get("bucket_to_delete")
    if not bucket:
        flash("Nom du bucket requis.", "error")
        return redirect(url_for("index"))
    s3 = s3_client()
    try:
        # vider le bucket (objets + versions si activé)
        try:
            paginator = s3.get_paginator("list_object_versions")
            for page in paginator.paginate(Bucket=bucket):
                to_delete = []
                for v in page.get("Versions", []) + page.get("DeleteMarkers", []):
                    to_delete.append({"Key": v["Key"], "VersionId": v["VersionId"]})
                if to_delete:
                    s3.delete_objects(Bucket=bucket, Delete={"Objects": to_delete})
        except ClientError:
            # si versioning non activé, on tente delete_objects simple
            resp = s3.list_objects_v2(Bucket=bucket)
            keys = [{"Key": it["Key"]} for it in resp.get("Contents", [])]
            if keys:
                s3.delete_objects(Bucket=bucket, Delete={"Objects": keys})
        s3.delete_bucket(Bucket=bucket)
        flash(f"Bucket supprimé: {bucket}", "ok")
    except ClientError as e:
        flash(f"Erreur suppression: {e}", "error")
    return redirect(url_for("index"))

# ---------- EC2 (bonus) ----------
@app.route("/ec2/launch", methods=["POST"])
def ec2_launch():
    ami = request.form.get("ami", "").strip() or "ami-08ee015f2bb7ccb9b"  # Amazon Linux 2023 eu-west-3 (à adapter si autre région)
    instance_type = request.form.get("instance_type", "t3.micro")
    key_name = request.form.get("key_name")
    sg_id = request.form.get("security_group_id")
    user_repo = request.form.get("user_repo", "").strip()

    user_data = """#cloud-config
package_update: true
packages:
  - git
  - nginx
runcmd:
  - systemctl enable nginx
  - systemctl start nginx
"""
    if user_repo:
        user_data += f"""
  - cd /tmp && git clone {user_repo} site || true
  - if [ -d /tmp/site ]; then rm -rf /usr/share/nginx/html/* && cp -r /tmp/site/* /usr/share/nginx/html/; fi
"""

    ec2 = ec2_resource()
    params = dict(
        ImageId=ami,
        InstanceType=instance_type,
        MinCount=1, MaxCount=1,
        NetworkInterfaces=[{
            "AssociatePublicIpAddress": True,
            "DeviceIndex": 0,
        }],
        UserData=user_data
    )
    if key_name:
        params["KeyName"] = key_name
    if sg_id:
        params["NetworkInterfaces"][0]["Groups"] = [sg_id]

    try:
        inst = ec2.create_instances(**params)[0]
        inst.wait_until_running()
        inst.reload()
        flash(f"Instance lancée: {inst.id} – IP publique: {inst.public_ip_address}", "ok")
    except ClientError as e:
        flash(f"Erreur lancement EC2: {e}", "error")
    return redirect(url_for("index"))

# ---------- Git clone (bonus) ----------
@app.route("/git/clone", methods=["POST"])
def git_clone():
    repo_url = request.form.get("repo_url", "").strip()
    if not repo_url:
        flash("URL de repo requise.", "error")
        return redirect(url_for("index"))
    target = os.path.join(REPOS_DIR, f"repo-{rand_suffix()}")
    try:
        Repo.clone_from(repo_url, target)
        flash(f"Repo cloné dans {target}. Contenu statique exposé sur /repo/{os.path.basename(target)}", "ok")
    except Exception as e:
        flash(f"Echec clone: {e}", "error")
    return redirect(url_for("index"))

@app.route("/repo/<name>/<path:path>")
def serve_repo(name, path=""):
    base = os.path.join(REPOS_DIR, name)
    if not os.path.isdir(base):
        return "Not found", 404
    if path == "" or path.endswith("/"):
        path = path + "index.html"
    directory = os.path.dirname(os.path.join(base, path))
    filename = os.path.basename(path)
    return send_from_directory(directory, filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
