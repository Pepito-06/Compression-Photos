# Photo Compressor (Raspberry Pi + Docker)

Service web minimal avec drag & drop:
- upload d'images
- compression automatique juste sous 2 Mo
- envoi par e-mail des images compressées

## 1) Pré-requis
- Raspberry Pi avec Docker + Docker Compose plugin

## 2) Configuration

```bash
cp .env.example .env
```

Puis édite `.env` avec tes infos SMTP.

### Gmail
- active la validation 2FA
- crée un mot de passe d'application
- utilise ce mot de passe dans `SMTP_PASSWORD`

## 3) Lancer

```bash
docker compose up -d --build
```

L'interface est disponible sur:
- `http://<IP_DU_RASPBERRY>:8080`

## 4) Utilisation
- glisse/dépose une ou plusieurs photos
- clique `Compresser et envoyer`
- les fichiers compressés sont envoyés à `MAIL_TO`

## Notes
- Les images sont converties en JPEG pour mieux contrôler la taille.
- Seuil cible: inférieur à ~2 Mo (avec une petite marge de sécurité).
- Si une image est impossible à réduire sous 2 Mo sans trop dégrader, l'API renvoie une erreur.
