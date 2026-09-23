# Exerçons-nous à containeriser le projet wordsmith !

Le projet wordsmith est désormais découpé en 5 parties :

- web : serveur web frontend écrit en Go
- web2 : évolution Node.js de `web`, avec le même rôle principal mais une interface plus moderne et des interactions supplémentaires pilotées par LLM
- words : API REST écrite en Java, qui interroge la base de données
- db : base PostgreSQL contenant les mots à afficher
- narrative (nouveau) : serveur REST Python qui utilise des LLM pour générer une histoire

Notre objectif est de containeriser cette application.

Il y aura 3 étapes :

1. Écrire plusieurs Dockerfiles pour construire les images des conteneurs.
   1. lancer les conteneurs indépendamment
   2. les connecter sur le même réseau
2. Écrire un fichier Compose pour automatiser certaines étapes (connexion)
   1. ajouter un volume pour relier les fichiers statiques
   2. ajouter un volume pour persister la base de données localement
   3. améliorer le Dockerfile de `words` pour éviter des reconstructions Maven inutiles
3. Faire évoluer l’application
   1. laissez libre cours à votre créativité pour améliorer l’application

## Exercice 1 : Dockerfiles

Notre objectif est d’écrire les Dockerfiles des services.

Commencez par faire un `git clone` du dépôt. Vous allez devoir
créer un Dockerfile pour chaque service. Astuce : placez chaque
Dockerfile dans le répertoire correspondant (`web`, `words`, `db`, etc.).

Les paragraphes suivants décrivent les instructions d’installation
pour chaque service.

Note : dans ce premier exercice, nous voulons seulement construire les images
et vérifier qu’elles démarrent correctement (`web`, `words` et `narrative`
doivent afficher un court message indiquant qu’ils tournent), mais nous ne
cherchons pas encore à lancer l’application complète ni à connecter les services.
Cela viendra plus tard.

### web (legacy UI)

C’est un serveur web écrit en Go. Pour compiler du Go, on peut utiliser
l’image officielle `golang`, ou bien installer les paquets Go dans
n’importe quelle image de base officielle.

Tout le code est contenu dans un unique fichier source (`dispatcher.go`)
et se compile ainsi :

```
go build dispatcher.go
```

Cela produit un exécutable nommé `dispatcher`, qui se lance comme suit :

```
./dispatcher
Listening on port 80
```

Le serveur web doit pouvoir accéder au répertoire `static`. Ce répertoire
doit être un sous-répertoire du répertoire courant au moment du lancement.

Informations supplémentaires :

- le serveur écoute sur le port 80
- le compilateur Go n’est utile que pour la construction, pas pour l’exécution

### web2

`web2` est l’évolution Node.js du service `web` d’origine.
Il conserve la même responsabilité principale que `web` : servir le frontend
et proxyfier les requêtes vers les services backend. La différence est qu’il
propose une interface plus moderne et peut appeler des API plus récentes,
comme le service `narrative`, pour afficher du contenu généré par un LLM.

Informations supplémentaires :

- le serveur écoute sur le port 8000
- il sert les fichiers statiques depuis `public`
- il proxyfie les requêtes `/words/*` vers le service Java `words`
- il peut aussi appeler le service Python `narrative` pour afficher une histoire générée

### words

Il s’agit d’un backend d’API REST écrit en Java. Il doit être construit avec Maven.

Sur une distribution Debian ou Ubuntu, on peut installer Java et Maven ainsi :

```
apt-get install maven openjdk-17-jdk
```

Comme image de conteneur, une base simple recommandée est :

```
maven:3.9.9-eclipse-temurin-17
```

Pour construire le programme, on peut invoquer Maven ainsi :

```
mvn verify
```

Le résultat est un fichier nommé `words.jar`, situé dans le répertoire `target`.

Le serveur doit être démarré avec la commande suivante,
dans le répertoire où se trouve `words.jar` :

```
java -Xmx64m -Xms64m -jar words.jar
```

Informations supplémentaires :

- le serveur écoute sur le port 8080
- la compilation nécessite les paquets `maven` et `openjdk-17-jdk`
- l’exécution nécessite `openjdk-17-jdk` (`maven` n’est pas nécessaire)

### db

Il s’agit d’une base de données PostgreSQL.

La base doit être initialisée avec le schéma (base et tables)
et les données utilisées par l’application.

Le fichier `words.sql` contient toutes les commandes SQL nécessaires
pour créer le schéma et charger les données.

```
# cat words.sql
CREATE TABLE nouns (word TEXT NOT NULL);
CREATE TABLE verbs (word TEXT NOT NULL);
CREATE TABLE adjectives (word TEXT NOT NULL);
CREATE TABLE stories (
  story TEXT NOT NULL,
  model TEXT NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO nouns(word) VALUES
  ('cloud'),
  ('elephant'),
  ('gø language'),
  ('laptøp'),
  ('cøntainer'),
  ('micrø-service'),
  ('turtle'),
  ('whale'),
  ('gøpher'),
  ('møby døck'),
  ('server'),
  ('bicycle'),
  ('viking'),
  ('mermaid'),
  ('fjørd'),
  ('legø'),
  ('flødebolle'),
  ('smørrebrød');

INSERT INTO verbs(word) VALUES
  ('will drink'),
  ('smashes'),
  ('smøkes'),
  ('eats'),
  ('walks tøwards'),
  ('løves'),
  ('helps'),
  ('pushes'),
  ('debugs'),
  ('invites'),
  ('hides'),
  ('will ship');

INSERT INTO adjectives(word) VALUES
  ('the exquisite'),
  ('a pink'),
  ('the røtten'),
  ('a red'),
  ('the serverless'),
  ('a brøken'),
  ('a shiny'),
  ('the pretty'),
  ('the impressive'),
  ('an awesøme'),
  ('the famøus'),
  ('a gigantic'),
  ('the gløriøus'),
  ('the nørdic'),
  ('the welcøming'),
  ('the deliciøus');
```

Les histoires seront ajoutées à l’exécution par le modèle.

Informations supplémentaires :

- nous recommandons fortement d’utiliser l’image officielle PostgreSQL sur Docker Hub (`postgres`)
- sur la [page de cette image officielle](https://hub.docker.com/_/postgres), la section « Initialization scripts » est particulièrement utile pour comprendre comment charger `words.sql`
- il est conseillé de protéger l’accès à la base par mot de passe ; ici, pour simplifier l’exercice, on autorise toutes les connexions avec `POSTGRES_HOST_AUTH_METHOD=trust`
- pour exposer la base en local et l’inspecter, utilisez le port 5432

### narrative

Il s’agit d’une API REST Python qui s’appuie sur les autres services.
Elle appelle l’API `words` pour récupérer un ensemble de mots générés,
puis utilise un LLM exposé via Docker Model Runner pour transformer ces mots
en une courte histoire.

Le serveur doit exposer :

- `/healthz` pour confirmer que le service fonctionne
- `/narrative` pour générer une courte histoire

Quand une histoire est générée, elle est également stockée dans PostgreSQL
avec le nom du modèle et la date de création dans la table `stories`.

Informations supplémentaires :

- le serveur écoute sur le port 8181
- il dépend de `words` pour le vocabulaire
- il dépend du serveur de modèles Docker pour la génération de texte
- il écrit les histoires générées dans le service `db`

Si vous voulez lancer et tester manuellement un modèle avant de l’intégrer
dans Compose, vous pouvez exécuter :

```bash
docker model run ai/smollm2
```

Ou le précharger en arrière-plan :

```bash
docker model run --detach ai/smollm2
```

### Connectez les conteneurs

Créer un réseau
```docker network create inclass```

Connectez les conteneurs un par un, par exemple la base de données

```docker network connect inclass db```

Les conteneurs DOIVENT avoir les noms suivants pour se connecter de manière transparente, utilisez --name <nom>
- db
- words
- narrative

## Exercice 2 : Compose

Quand les images se construisent correctement, nous pouvons passer
à l’écriture du fichier Compose. Nous suggérons de placer ce fichier
à la racine du dépôt.

À ce stade, nous voulons vérifier que les services communiquent bien
entre eux et que l’on peut se connecter à `web`.

Note : le service `web` doit être exposé.

### Comment Docker Model Runner s’intègre à Docker Compose

Docker Model Runner permet à un service de déclarer directement
le modèle dont il a besoin dans `compose.yaml`. Compose rend ensuite
ce modèle disponible au service à l’exécution, au lieu de vous obliger
à gérer manuellement un conteneur d’inférence séparé.

En pratique, le flux est le suivant :

- déclarer le modèle dans la section `models` au niveau racine
- attacher ce modèle à un service sous `services.<nom>.models`
- laisser l’application appeler le point d’accès exposé par Docker Model Runner

Exemple :

```yaml
services:
  chat-app:
    image: my-chat-app
    models:
      - llm

models:
  llm:
    model: ai/smollm2
```

Dans ce projet, le service `narrative` suit ce même principe :
il déclare un modèle LLM dans Compose, puis l’utilise à l’exécution
pour transformer les mots provenant de l’API `words` en une courte histoire.

## Exercice 3 : Jouer avec Docker Model Server

- changez le modèle pour un modèle plus puissant (attention à la mémoire)
- faites évoluer le schéma de la base et enregistrez le protagoniste
- essayez de relier plusieurs histoires entre elles
- laissez parler votre imagination !
