# Photo Compressor (VM Proxmox + Docker)

Service web minimal avec drag & drop:
- upload d'images
- compression automatique juste sous 2 Mo
- envoi par e-mail des images compressées
- archivage optionnel sur disque externe
- interface mobile iPhone + Android (galerie + camera)

## 1) Pré-requis
- VM Linux sur Proxmox
- Docker + Docker Compose plugin dans la VM
- Disque externe visible dans Proxmox, puis monté dans la VM

## 2) Configuration

```bash
cp .env.example .env
```

Puis édite `.env` avec tes infos SMTP.

### Gmail
- active la validation 2FA
- crée un mot de passe d'application
- utilise ce mot de passe dans `SMTP_PASSWORD`

Variables utiles:
- `ARCHIVE_DIR=/data/archive` pour sauvegarder originaux + compressés sur le disque externe
- `MAX_UPLOAD_MB=100` pour limiter la taille max d'upload HTTP

## 3) Monter le disque externe dans la VM

Exemple (adapte `/dev/sdb1`):

```bash
sudo mkdir -p /mnt/photo-disk
sudo mount /dev/sdb1 /mnt/photo-disk
sudo mkdir -p /mnt/photo-disk/compression-data/archive
```

Pour montage auto, ajoute une entrée dans `/etc/fstab`.

## 4) Lancer

```bash
docker compose up -d --build
```

L'interface est disponible sur:
- `http://<IP_DE_LA_VM>:8080`

## 5) Utilisation
- glisse/dépose une ou plusieurs photos
- sur mobile: utilise `Choisir des photos` ou `Prendre une photo`
- clique `Compresser et envoyer`
- les fichiers compressés sont envoyés à `MAIL_TO`
- si `ARCHIVE_DIR` est défini, originaux + compressés sont stockés sur le disque externe

## Notes
- Les images sont converties en JPEG pour mieux contrôler la taille.
- iPhone HEIC/HEIF supporté via `pillow-heif`.
- Seuil cible: inférieur à ~2 Mo (avec une petite marge de sécurité).
- Si une image est impossible à réduire sous 2 Mo sans trop dégrader, l'API renvoie une erreur.
- Mapping disque externe par défaut dans `docker-compose.yml`:
  - hôte VM: `/mnt/photo-disk/compression-data`
  - conteneur: `/data`
