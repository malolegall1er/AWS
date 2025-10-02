# AWS Docker Tool (Flask)

## Démarrage
1. Copie ce dossier en local.
2. Crée un fichier `.env` à la racine avec :
```
AWS_ACCESS_KEY_ID=AKIAxxxxxxxxxxxx
AWS_SECRET_ACCESS_KEY=xxxxxxxxxxxxxxxxxxxxxx
AWS_DEFAULT_REGION=eu-west-3
```
3. Build & run :
```
docker build -t aws-tool .
docker run --rm -p 8080:8080 --env-file .env aws-tool
```
4. Ouvre http://localhost:8080

## Fonctions
- Lister les instances EC2
- Lister les buckets S3
- Créer un bucket + uploader des fichiers
- Supprimer un bucket (vide automatiquement)
- (Bonus) Lancer une instance EC2 accessible publiquement, avec Nginx et clone d’un repo
- (Bonus) Cloner un repo GitHub et servir ses fichiers statiques via l’app

> Attention: évite d'utiliser des clés root en production.
