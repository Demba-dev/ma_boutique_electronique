# 🛡️ Guide de Protection Django avec PyArmor

Ce guide explique comment verrouiller le projet **diaby_electronic** avec une date d'expiration pour sécuriser vos paiements et protéger votre code source contre le vol.

---

## 1. Installation (Sur votre machine de développement)
Activez votre environnement virtuel et installez PyArmor :
```bash
source venv/bin/activate
pip install pyarmor
```

---

## 2. Génération de la Version Client (Première Installation)
Pour créer une version qui expire à une date précise (ex: le **05 Juin 2026**) :

1. Ouvrez un terminal à la racine du projet.
2. Lancez la commande suivante :
```bash
pyarmor gen -O diaby_electronic_CLIENT -r -e 2026-06-05 manage.py apps/ config/
```
3. Copiez les ressources non-Python dans le dossier généré :
```bash
cp -r templates/ diaby_electronic_CLIENT/
cp -r static/ diaby_electronic_CLIENT/
cp -r media/ diaby_electronic_CLIENT/
cp db.sqlite3 diaby_electronic_CLIENT/
```

---

## 3. Installation chez le Client (Windows)
1. Copiez le dossier complet `diaby_electronic_CLIENT` sur l'ordinateur Windows.
2. Installez Python sur son Windows.
3. Installez les dépendances nécessaires (Django, etc.).
4. Lancez le serveur normalement :
   ```cmd
   python manage.py runserver
   ```
*Le projet fonctionnera normalement jusqu'au 05 Juin 2026. Après cette date, il affichera une erreur de licence.*

---

## 4. Mise à jour ou Déverrouillage Final
**Ne faites jamais cette étape sur l'ordinateur du client !** Faites-la toujours chez vous.

### Option A : Prolonger la date (Nouvelle date)
```bash
pyarmor gen -O NEW_DIST -r -e 2026-12-31 manage.py apps/ config/
```

### Option B : Supprimer l'expiration (Version Finale payée)
```bash
pyarmor gen -O FINAL_DIST -r manage.py apps/ config/
```

---

## 5. Procédure de Remplacement chez le Client
Pour mettre à jour la licence sans faire perdre de données au client (ventes, clients, etc.) :

1. **Remplacer UNIQUEMENT ces éléments** sur l'ordi du client :
   - Le dossier `apps/`
   - Le dossier `config/`
   - Le fichier `manage.py`
   - Le dossier `pyarmor_runtime_000000/` (très important !)

2. **⚠️ NE JAMAIS TOUCHER** aux éléments suivants sur l'ordi du client :
   - **`db.sqlite3`** : Contient toutes ses ventes et ses clients.
   - **`media/`** : Contient toutes ses photos de produits.

---

## 6. Création d'un raccourci Bureau (Windows)
Pour que le client lance le projet comme une application classique :

1. Dans le dossier du projet, créez un fichier `lancer_diaby.bat` :
```batch
@echo off
cd /d "%~dp0"
call venv\Scripts\activate
start "" "http://127.0.0.1:8000"
python manage.py runserver
```
2. Faites un **Clic-droit** sur ce fichier > **Envoyer vers** > **Bureau (créer un raccourci)**.
3. Changez l'icône du raccourci dans **Propriétés** > **Changer d'icône**.

---

## 7. Commande d'automatisation (Templates & Ressources)
Pour éviter l'erreur `TemplateDoesNotExist`, lancez cette commande après `pyarmor gen` pour tout copier au bon endroit dans le dossier client :

```bash
# Copier les templates racines
cp -r templates/ diaby_electronic_CLIENT/
# Copier les templates internes aux apps
mkdir -p diaby_electronic_CLIENT/apps/accounts/templates/
cp -r apps/accounts/templates/accounts diaby_electronic_CLIENT/apps/accounts/templates/
# Copier les autres ressources
cp -r static/ diaby_electronic_CLIENT/
cp -r media/ diaby_electronic_CLIENT/
cp db.sqlite3 diaby_electronic_CLIENT/
```

---

## 💡 Résumé des Commandes Clés
| Action | Commande PyArmor |
| :--- | :--- |
| **Vérifier l'installation** | `pyarmor --version` |
| **Protéger avec expiration** | `pyarmor gen -O dist -r -e AAAA-MM-JJ manage.py apps/ config/` |
| **Protéger sans expiration** | `pyarmor gen -O dist -r manage.py apps/ config/` |

---
**Note :** *Gardez toujours votre code source original (les fichiers .py lisibles) en lieu sûr. Les fichiers générés par PyArmor sont impossibles à relire pour vous aussi !*
