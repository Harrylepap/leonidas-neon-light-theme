# Publier Leonidas - Neon Light sur le JetBrains Marketplace

1. [Remplir les placeholders](#1-remplir-les-placeholders)
2. [Construire le plugin](#2-construire-le-plugin)
3. [Vérifier avec le Plugin Verifier](#3-vérifier-avec-le-plugin-verifier)
4. [Signer le plugin (recommandé)](#4-signer-le-plugin-recommandé)
5. [Premier dépôt manuel sur le Marketplace](#5-premier-dépôt-manuel-sur-le-marketplace)
6. [Versions suivantes via GitHub](#6-versions-suivantes-via-github)

## 1. Remplir les placeholders

Tous les champs à compléter commencent par `TODO_`. Pour les lister :

```bash
grep -rn "TODO_" --exclude-dir=build --exclude-dir=.gradle .
```

| Fichier | Champ | Exemple |
|---|---|---|
| `gradle.properties` | `pluginId` (**définitif**, ne peut plus changer après publication) | `io.github.monpseudo.leonidas-neon-light` |
| `gradle.properties` | `pluginGroup` | `io.github.monpseudo` |
| `gradle.properties` | `vendorName` / `vendorEmail` / `vendorUrl` | nom affiché, e-mail de contact, site ou profil GitHub |
| `gradle.properties` | `pluginRepositoryUrl` | `https://github.com/monpseudo/leonidas-neon-light-theme` |
| `src/main/resources/themes/leonidas-neon-light.theme.json` | `author` | même valeur que `vendorName` |
| `LICENSE` | `TODO_VENDOR_NAME` | même valeur que `vendorName` |
| `README.md` | badges, captures d'écran | après la première publication |

La tâche `publishPlugin` refuse de partir tant qu'un champ `TODO_*` reste dans `gradle.properties`.

## 2. Construire le plugin

| Méthode | Commande | Résultat |
|---|---|---|
| Gradle (officiel, à utiliser pour le Marketplace) | `./gradlew buildPlugin` | `build/distributions/leonidas-neon-light-theme-<version>.zip` |
| Gradle avec l'IntelliJ installé (pas de téléchargement d'IDE) | `./gradlew buildPlugin -PplatformLocalPath="C:/Program Files/JetBrains/IntelliJ IDEA 2025.2.4"` | idem |
| Sans Gradle (test rapide) | `python tools/build_local_jar.py` | `build/local/leonidas-neon-light-<version>.jar` |
| Sans Gradle + installation dans IntelliJ | `python tools/build_local_jar.py --install` | copié dans `%APPDATA%/JetBrains/IntelliJIdea<dernière>/plugins`, puis redémarrer |

Tester dans un IDE isolé, sans toucher à ta config : `./gradlew runIde`.

## 3. Vérifier avec le Plugin Verifier

Le **Plugin Verifier** est l'outil de JetBrains qui charge le plugin dans plusieurs versions d'IDE
et signale les incompatibilités (API absentes, descripteur invalide, etc.). Le Marketplace le fait
aussi tourner automatiquement après chaque dépôt.

| Vérification | Commande | Durée |
|---|---|---|
| Structure du plugin et de `plugin.xml` | `./gradlew verifyPluginStructure verifyPluginProjectConfiguration` | quelques secondes |
| Plugin Verifier complet sur les IDE recommandés | `./gradlew verifyPlugin` | long : télécharge plusieurs IDE (plusieurs Go) |
| En CI | automatique dans `.github/workflows/build.yml` à chaque push | rapport en artefact `plugin-verifier-reports` |

Rapport local : `build/reports/pluginVerifier/`. Un thème pur n'ayant pas de code, le verdict attendu est *Compatible*.

## 4. Signer le plugin (recommandé)

La signature garantit que le plugin n'a pas été modifié. Elle n'est pas obligatoire pour un premier dépôt.

```bash
openssl genpkey -aes-256-cbc -algorithm RSA -out private.pem -pkeyopt rsa_keygen_bits:4096
openssl req -key private.pem -new -x509 -days 3650 -out chain.crt
```

Puis définir `CERTIFICATE_CHAIN` (contenu de `chain.crt`), `PRIVATE_KEY` (contenu de `private.pem`) et
`PRIVATE_KEY_PASSWORD`, en local ou en secrets GitHub, et lancer `./gradlew signPlugin`.
Ces fichiers ne doivent **jamais** être commités (exclus par `.gitignore`).

## 5. Premier dépôt manuel sur le Marketplace

La toute première version ne peut pas être publiée par Gradle : elle se dépose à la main.

1. Se connecter sur https://plugins.jetbrains.com avec un compte JetBrains.
2. Accepter le *JetBrains Marketplace Developer Agreement*.
3. Avatar > **Upload plugin**.
4. Déposer `build/distributions/leonidas-neon-light-theme-1.0.0.zip`.
5. Licence : **MIT** (lien vers `LICENSE` du dépôt). Catégorie : **Theme**. Tags : `theme`, `dark`, `neon`.
6. Ajouter les captures d'écran (`docs/screenshots/`).
7. Envoyer. JetBrains valide manuellement, en général sous 2 jours ouvrés. Un e-mail confirme la publication.

## 6. Versions suivantes via GitHub

1. Créer le dépôt GitHub et pousser `main`.
2. Sur plugins.jetbrains.com : avatar > **My Tokens** > *Generate Token*.
3. Dans GitHub : *Settings* > *Secrets and variables* > *Actions* : ajouter `PUBLISH_TOKEN`
   (et les 3 secrets de signature si utilisés).
4. Pour chaque nouvelle version :
   - monter `pluginVersion` dans `gradle.properties` ;
   - ajouter l'entrée correspondante dans `CHANGELOG.md` ;
   - créer une *Release* GitHub avec le tag `v<version>`.
5. Le workflow `.github/workflows/release.yml` lance `./gradlew publishPlugin` et joint le zip à la release.
